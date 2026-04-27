"""
Gaze Direction Estimator.

Uses iris position relative to eye corners to estimate gaze direction.
This is a SIMPLE estimator — for a Week 1 baseline. More sophisticated
gaze estimation (using head pose + iris) can come in Week 2+.

Logic:
  - Eye width = distance between eye corners (p1, p4 of EAR landmarks)
  - Iris center = average of 4-5 iris landmarks
  - If iris is centered horizontally → looking forward
  - If iris is left/right of center → looking left/right
"""
from typing import Tuple, Optional
import numpy as np

from ..config import (
    LEFT_EYE_EAR,
    RIGHT_EYE_EAR,
    LEFT_IRIS,
    RIGHT_IRIS,
    GAZE_DRIFT_THRESHOLD,
)


def _iris_center_offset(
    landmarks: np.ndarray,
    eye_indices: list,
    iris_indices: list,
) -> Optional[float]:
    """
    Compute horizontal offset of iris from eye center,
    normalized by eye width.

    Returns:
        Float in roughly [-1, 1]:
            0  = iris centered (looking forward)
            -1 = iris fully left (looking left)
            +1 = iris fully right (looking right)
        None if computation fails.
    """
    if len(iris_indices) < 4:
        return None

    eye_pts = landmarks[eye_indices][:, :2]
    iris_pts = landmarks[iris_indices][:, :2]

    # Eye corners: index 0 = outer corner, index 3 = inner corner
    outer_corner = eye_pts[0]
    inner_corner = eye_pts[3]

    eye_center_x = (outer_corner[0] + inner_corner[0]) / 2.0
    eye_width = abs(inner_corner[0] - outer_corner[0])

    if eye_width < 1e-6:
        return None

    iris_center_x = float(np.mean(iris_pts[:, 0]))

    offset = (iris_center_x - eye_center_x) / (eye_width / 2.0)
    return offset


def estimate_gaze(landmarks: np.ndarray) -> Tuple[float, bool]:
    """
    Estimate gaze drift from face landmarks.

    Args:
        landmarks: (478, 3) face mesh landmarks

    Returns:
        (drift_score, is_drifted)
            drift_score: 0.0 to 1.0, higher = more off-screen
            is_drifted:  bool, True if drift exceeds threshold
    """
    left = _iris_center_offset(landmarks, LEFT_EYE_EAR, LEFT_IRIS)
    right = _iris_center_offset(landmarks, RIGHT_EYE_EAR, RIGHT_IRIS)

    offsets = [o for o in (left, right) if o is not None]
    if not offsets:
        return 0.0, False

    # Average absolute offset across both eyes
    avg_offset = float(np.mean([abs(o) for o in offsets]))

    # Clamp to [0, 1] for score interpretation
    drift_score = min(avg_offset, 1.0)
    is_drifted = drift_score > GAZE_DRIFT_THRESHOLD

    return drift_score, is_drifted
