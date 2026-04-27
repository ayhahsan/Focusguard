"""
Eye Aspect Ratio (EAR) — drowsiness detection.

Algorithm: Soukupová & Čech 2016
"Real-Time Eye Blink Detection using Facial Landmarks"

Idea:
  EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)

  p1, p4 = horizontal eye corners
  p2, p3 = upper eyelid points
  p5, p6 = lower eyelid points

When eye is open, vertical distances are large → high EAR (~0.30)
When eye closes, vertical distances shrink → low EAR (~0.10)

A blink is brief (1-2 frames). Drowsiness = sustained low EAR.
"""
from typing import Tuple
import numpy as np

from ..config import (
    LEFT_EYE_EAR,
    RIGHT_EYE_EAR,
    EAR_DROWSY_THRESHOLD,
    DROWSY_FRAME_COUNT,
)


def _euclidean(p1: np.ndarray, p2: np.ndarray) -> float:
    """Euclidean distance between two 2D/3D points."""
    return float(np.linalg.norm(p1 - p2))


def compute_ear(landmarks: np.ndarray, eye_indices: list) -> float:
    """
    Compute Eye Aspect Ratio for one eye.

    Args:
        landmarks: (478, 3) array of normalized face landmarks
        eye_indices: 6 landmark indices [p1, p2, p3, p4, p5, p6]
                     ordered: outer corner, top-left, top-right,
                              inner corner, bottom-right, bottom-left

    Returns:
        EAR value (typically 0.0 to 0.4)
    """
    if len(eye_indices) != 6:
        raise ValueError(f"Need 6 eye landmarks, got {len(eye_indices)}")

    pts = landmarks[eye_indices][:, :2]  # 2D coords only
    p1, p2, p3, p4, p5, p6 = pts

    # Vertical distances
    v1 = _euclidean(p2, p6)
    v2 = _euclidean(p3, p5)

    # Horizontal distance
    h = _euclidean(p1, p4)

    if h < 1e-6:  # Avoid divide-by-zero on edge cases
        return 0.0

    return (v1 + v2) / (2.0 * h)


class DrowsinessDetector:
    """
    Stateful drowsiness detector.

    Tracks consecutive frames of low EAR. A normal blink (a few frames)
    won't trigger; only sustained eye closure will.
    """

    def __init__(
        self,
        threshold: float = EAR_DROWSY_THRESHOLD,
        frame_count: int = DROWSY_FRAME_COUNT,
    ):
        self.threshold = threshold
        self.frame_count = frame_count
        self._closed_frames = 0

    def update(self, landmarks: np.ndarray) -> Tuple[float, bool, bool]:
        """
        Process new frame.

        Args:
            landmarks: face mesh landmarks

        Returns:
            (avg_ear, eyes_closed_this_frame, is_drowsy)
            - avg_ear: average EAR across both eyes (0-0.4 typical)
            - eyes_closed_this_frame: instant state
            - is_drowsy: sustained closure detected
        """
        left_ear = compute_ear(landmarks, LEFT_EYE_EAR)
        right_ear = compute_ear(landmarks, RIGHT_EYE_EAR)
        avg_ear = (left_ear + right_ear) / 2.0

        eyes_closed = avg_ear < self.threshold

        if eyes_closed:
            self._closed_frames += 1
        else:
            self._closed_frames = 0

        is_drowsy = self._closed_frames >= self.frame_count

        return avg_ear, eyes_closed, is_drowsy

    def reset(self):
        """Reset counter — call after user becomes alert again."""
        self._closed_frames = 0

    @property
    def closed_frame_count(self) -> int:
        return self._closed_frames
