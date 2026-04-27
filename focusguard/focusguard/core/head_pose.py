"""
Head Pose Estimation — pitch, yaw, roll.

Uses cv2.solvePnP to solve the Perspective-n-Point problem:
given 2D facial landmarks and a known 3D face model,
compute the 3D rotation of the head.

Pitch = up/down nodding (looking at phone = pitch down)
Yaw   = left/right turning
Roll  = head tilt (less useful for focus tracking)
"""
from typing import Tuple, Optional
import math
import numpy as np

from ..config import HEAD_POSE_LANDMARKS


# 3D model points for a generic face (in millimeters, approximate)
# These are rough averages — perfect for relative pose, not absolute position.
# Reference: standard PnP-based head pose papers.
FACE_3D_MODEL = np.array([
    [0.0,    0.0,    0.0],     # nose_tip
    [0.0,   -63.6,  -12.5],    # chin
    [-43.3,  32.7,  -26.0],    # left_eye_corner (user's left)
    [43.3,   32.7,  -26.0],    # right_eye_corner
    [-28.9, -28.9,  -24.1],    # left_mouth_corner
    [28.9,  -28.9,  -24.1],    # right_mouth_corner
], dtype=np.float64)

# Order matches FACE_3D_MODEL above
LANDMARK_ORDER = [
    "nose_tip",
    "chin",
    "left_eye_corner",
    "right_eye_corner",
    "left_mouth_corner",
    "right_mouth_corner",
]


def _rotation_matrix_to_euler(R: np.ndarray) -> Tuple[float, float, float]:
    """
    Convert 3x3 rotation matrix to Euler angles (pitch, yaw, roll) in degrees.
    Uses ZYX convention (common for face/camera).
    """
    sy = math.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)
    singular = sy < 1e-6

    if not singular:
        pitch = math.atan2(-R[2, 0], sy)
        yaw = math.atan2(R[1, 0], R[0, 0])
        roll = math.atan2(R[2, 1], R[2, 2])
    else:
        pitch = math.atan2(-R[2, 0], sy)
        yaw = 0
        roll = math.atan2(-R[1, 2], R[1, 1])

    return (
        math.degrees(pitch),
        math.degrees(yaw),
        math.degrees(roll),
    )


def estimate_head_pose(
    landmarks_pixels: np.ndarray,
    frame_shape: Tuple[int, int, int],
) -> Optional[Tuple[float, float, float]]:
    """
    Estimate head pose from face landmarks.

    Args:
        landmarks_pixels: (478, 2) array of pixel coordinates
        frame_shape: (height, width, channels) from cv2 frame

    Returns:
        (pitch_deg, yaw_deg, roll_deg) or None if estimation fails

        pitch > 0  → looking up
        pitch < 0  → looking down (toward phone/desk)
        yaw   > 0  → looking right (from camera view)
        yaw   < 0  → looking left
    """
    import cv2

    h, w = frame_shape[:2]

    # Camera matrix — approximate using image dimensions
    # focal_length ≈ image_width is a reasonable starting point
    focal_length = w
    center = (w / 2, h / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1],
    ], dtype=np.float64)

    # Assume no lens distortion (good enough for webcams)
    dist_coeffs = np.zeros((4, 1), dtype=np.float64)

    # Extract the 6 landmarks we need, in correct order
    image_points = np.array([
        landmarks_pixels[HEAD_POSE_LANDMARKS[name]]
        for name in LANDMARK_ORDER
    ], dtype=np.float64)

    success, rvec, tvec = cv2.solvePnP(
        FACE_3D_MODEL,
        image_points,
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )

    if not success:
        return None

    # Convert rotation vector to matrix, then to Euler angles
    R, _ = cv2.Rodrigues(rvec)
    pitch, yaw, roll = _rotation_matrix_to_euler(R)

    return pitch, yaw, roll
