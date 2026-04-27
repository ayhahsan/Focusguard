"""
FocusGuard configuration constants.

Sab tunable parameters yahan rakhe hain. Ek jagah change karo,
poora system update ho jaye.
"""

# ─── Camera Settings ─────────────────────────────────────────
CAMERA_INDEX = 0          # Default webcam (0 = built-in usually)
TARGET_FPS = 15           # Process at 15 FPS — saves CPU, plenty for focus tracking
FRAME_WIDTH = 640         # Lower res = faster; quality enough for focus detection
FRAME_HEIGHT = 480

# ─── MediaPipe Face Mesh Landmark Indices ────────────────────
# Reference: https://github.com/google/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png

# Right eye (from CAMERA's view = user's left eye, since webcam mirrors)
# 6 landmarks for Eye Aspect Ratio (EAR) — Soukupová & Čech 2016
RIGHT_EYE_EAR = [33, 160, 158, 133, 153, 144]

# Left eye (camera view = user's right)
LEFT_EYE_EAR = [362, 385, 387, 263, 373, 380]

# Iris landmarks (require refine_landmarks=True in MediaPipe)
# Each iris has 5 points: center + 4 cardinal directions
RIGHT_IRIS = [468, 469, 470, 471, 472]
LEFT_IRIS = [473, 474, 475, 476, 477]

# Key facial landmarks for head pose estimation (solvePnP)
# These map to 3D model points of an average face
HEAD_POSE_LANDMARKS = {
    "nose_tip": 1,
    "chin": 152,
    "left_eye_corner": 33,
    "right_eye_corner": 263,
    "left_mouth_corner": 61,
    "right_mouth_corner": 291,
}

# ─── Detection Thresholds ────────────────────────────────────
# EAR below this = eyes mostly closed (drowsy or blinking)
EAR_DROWSY_THRESHOLD = 0.20

# How many consecutive frames of low EAR before flagging drowsy
# At 15 FPS, 30 frames = ~2 seconds (longer than a normal blink)
DROWSY_FRAME_COUNT = 30

# Head pose angles (degrees) beyond which user is "looking away"
# Pitch = up/down, Yaw = left/right
HEAD_PITCH_THRESHOLD = 20.0   # Looking down (toward phone or desk)
HEAD_YAW_THRESHOLD = 25.0     # Looking sideways

# Gaze: iris center distance from eye center as fraction of eye width
GAZE_DRIFT_THRESHOLD = 0.25

# ─── Focus Score Aggregation ─────────────────────────────────
# Weights for each signal — must sum to 1.0
FOCUS_WEIGHTS = {
    "presence": 0.30,    # Most important — if absent, nothing else matters
    "eyes_open": 0.25,   # Drowsiness check
    "head_pose": 0.25,   # Looking at screen check
    "gaze": 0.20,        # Eye-level gaze direction
}

# Smoothing window for focus score (in frames) — prevents jitter
SCORE_SMOOTHING_WINDOW = 15  # ~1 second at 15 FPS

# ─── Distraction State Thresholds ────────────────────────────
# Score zones for state classification
SCORE_FOCUSED = 70       # Above this = FOCUSED
SCORE_DRIFTING = 50      # 50-70 = DRIFTING
# Below 50 = DISTRACTED
# Below 20 = ABSENT (handled separately)

# ─── Display / Overlay ───────────────────────────────────────
# Colors in BGR format (OpenCV convention)
COLOR_FOCUSED = (0, 200, 0)       # Green
COLOR_DRIFTING = (0, 165, 255)    # Orange
COLOR_DISTRACTED = (0, 0, 255)    # Red
COLOR_ABSENT = (128, 128, 128)    # Gray
COLOR_TEXT = (255, 255, 255)      # White

# Window title
WINDOW_NAME = "FocusGuard — Press Q to quit"
