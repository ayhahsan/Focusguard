"""
Visual overlay for webcam frame.

Draws focus score, state, eye landmarks, and other diagnostic info
onto each frame so user can see what FocusGuard is doing.
"""
from typing import Optional
import numpy as np

from ..config import (
    LEFT_EYE_EAR,
    RIGHT_EYE_EAR,
    COLOR_FOCUSED,
    COLOR_DRIFTING,
    COLOR_DISTRACTED,
    COLOR_ABSENT,
    COLOR_TEXT,
)
from ..core.focus_score import FocusReading, FocusState


def _state_color(state: FocusState) -> tuple:
    """Return BGR color for a focus state."""
    return {
        FocusState.FOCUSED: COLOR_FOCUSED,
        FocusState.DRIFTING: COLOR_DRIFTING,
        FocusState.DISTRACTED: COLOR_DISTRACTED,
        FocusState.ABSENT: COLOR_ABSENT,
    }[state]


def draw_eye_landmarks(
    frame: np.ndarray,
    landmarks_pixels: Optional[np.ndarray],
):
    """Draw small dots on eye landmark points."""
    import cv2
    if landmarks_pixels is None:
        return
    for idx in LEFT_EYE_EAR + RIGHT_EYE_EAR:
        cv2.circle(frame, tuple(landmarks_pixels[idx]), 2, (0, 255, 255), -1)


def draw_focus_overlay(
    frame: np.ndarray,
    reading: Optional[FocusReading],
    landmarks_pixels: Optional[np.ndarray] = None,
    show_landmarks: bool = True,
):
    """
    Draw focus score, state, and stats on a frame in-place.

    Args:
        frame: BGR frame to draw on (modified in-place)
        reading: latest focus reading; None means "no face / first frame"
        landmarks_pixels: optional landmark pixels to draw
        show_landmarks: whether to overlay eye landmark dots
    """
    import cv2
    h, w = frame.shape[:2]

    if reading is None:
        cv2.putText(
            frame,
            "Searching for face...",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            COLOR_TEXT,
            2,
        )
        return

    color = _state_color(reading.state)

    # Top-left score badge — large, prominent
    score_text = f"{int(reading.smoothed_score)}"
    cv2.rectangle(frame, (10, 10), (200, 100), (40, 40, 40), -1)
    cv2.rectangle(frame, (10, 10), (200, 100), color, 2)
    cv2.putText(
        frame, "FOCUS", (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_TEXT, 1,
    )
    cv2.putText(
        frame, score_text, (20, 85),
        cv2.FONT_HERSHEY_SIMPLEX, 1.8, color, 3,
    )

    # State label
    cv2.putText(
        frame, reading.state.value, (210, 45),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2,
    )

    # Sub-scores breakdown (right side)
    y = 30
    for name, val in reading.sub_scores.items():
        bar_width = int(val * 100)
        cv2.putText(
            frame, f"{name}", (w - 220, y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_TEXT, 1,
        )
        cv2.rectangle(frame, (w - 110, y - 10), (w - 10, y), (60, 60, 60), -1)
        cv2.rectangle(
            frame, (w - 110, y - 10), (w - 110 + bar_width, y),
            color, -1,
        )
        cv2.putText(
            frame, f"{int(val*100)}", (w - 35, y - 1),
            cv2.FONT_HERSHEY_SIMPLEX, 0.35, COLOR_TEXT, 1,
        )
        y += 22

    # Bottom status bar with detailed signals
    s = reading.signals
    parts = [
        f"EAR: {s.avg_ear:.2f}",
        f"Drowsy: {'Y' if s.is_drowsy else 'N'}",
    ]
    if s.pitch is not None:
        parts.append(f"Pitch: {s.pitch:+.0f}")
        parts.append(f"Yaw: {s.yaw:+.0f}")
    parts.append(f"Gaze: {s.gaze_drift:.2f}")

    status = " | ".join(parts)
    cv2.rectangle(frame, (0, h - 30), (w, h), (0, 0, 0), -1)
    cv2.putText(
        frame, status, (10, h - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLOR_TEXT, 1,
    )

    # Eye landmarks
    if show_landmarks and landmarks_pixels is not None:
        draw_eye_landmarks(frame, landmarks_pixels)
