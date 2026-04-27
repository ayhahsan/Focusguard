"""
Focus Score Engine.

Combines all detection signals into a single 0-100 focus score.

Strategy:
  1. Get sub-scores for each signal (presence, eyes, head, gaze)
  2. Weighted aggregate per FOCUS_WEIGHTS in config
  3. Smooth over a sliding window to prevent jitter
  4. Classify into states: FOCUSED / DRIFTING / DISTRACTED / ABSENT
"""
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict
import time

from ..config import (
    FOCUS_WEIGHTS,
    SCORE_SMOOTHING_WINDOW,
    SCORE_FOCUSED,
    SCORE_DRIFTING,
    HEAD_PITCH_THRESHOLD,
    HEAD_YAW_THRESHOLD,
)


class FocusState(str, Enum):
    FOCUSED = "FOCUSED"
    DRIFTING = "DRIFTING"
    DISTRACTED = "DISTRACTED"
    ABSENT = "ABSENT"


@dataclass
class FrameSignals:
    """Per-frame raw signals from detectors."""
    face_present: bool
    avg_ear: float = 0.0
    is_drowsy: bool = False
    pitch: Optional[float] = None
    yaw: Optional[float] = None
    roll: Optional[float] = None
    gaze_drift: float = 0.0
    is_gaze_off: bool = False


@dataclass
class FocusReading:
    """A single moment's focus reading."""
    timestamp: float
    raw_score: float          # Instantaneous score (jittery)
    smoothed_score: float     # Smoothed score (display this)
    state: FocusState
    signals: FrameSignals
    sub_scores: Dict[str, float] = field(default_factory=dict)


class FocusScoreEngine:
    """Computes focus score from detector signals."""

    def __init__(self, smoothing_window: int = SCORE_SMOOTHING_WINDOW):
        self._score_history = deque(maxlen=smoothing_window)

    @staticmethod
    def _presence_score(face_present: bool) -> float:
        """1.0 if face detected, 0.0 if absent."""
        return 1.0 if face_present else 0.0

    @staticmethod
    def _eyes_score(is_drowsy: bool, avg_ear: float) -> float:
        """
        Drowsiness penalty.

        - Drowsy: score crashes to 0.1
        - Closing (low EAR): partial penalty
        - Wide open (high EAR): full score
        """
        if is_drowsy:
            return 0.1
        # Map EAR range [0.15, 0.30] linearly to [0, 1]
        normalized = (avg_ear - 0.15) / (0.30 - 0.15)
        return max(0.0, min(1.0, normalized))

    @staticmethod
    def _head_pose_score(pitch: Optional[float], yaw: Optional[float]) -> float:
        """
        Score based on how much head is angled away from screen.

        Looking down (pitch < -threshold) = looking at phone/desk → low score
        Looking sideways (|yaw| > threshold) → low score
        """
        if pitch is None or yaw is None:
            return 0.5  # No data — neutral

        # Pitch: negative is looking down, positive is looking up
        # Looking slightly down at screen is normal — only penalize sustained downward
        pitch_penalty = max(0.0, (-pitch - HEAD_PITCH_THRESHOLD) / 30.0)
        yaw_penalty = max(0.0, (abs(yaw) - HEAD_YAW_THRESHOLD) / 30.0)

        total_penalty = min(1.0, pitch_penalty + yaw_penalty)
        return max(0.0, 1.0 - total_penalty)

    @staticmethod
    def _gaze_score(gaze_drift: float) -> float:
        """Lower drift = higher score."""
        return max(0.0, 1.0 - gaze_drift)

    def compute(self, signals: FrameSignals) -> FocusReading:
        """
        Compute focus reading from a single frame's signals.

        Returns FocusReading with raw + smoothed score and state.
        """
        # Compute per-signal sub-scores [0, 1]
        sub_scores = {
            "presence": self._presence_score(signals.face_present),
            "eyes_open": self._eyes_score(signals.is_drowsy, signals.avg_ear),
            "head_pose": self._head_pose_score(signals.pitch, signals.yaw),
            "gaze": self._gaze_score(signals.gaze_drift),
        }

        # If face absent, the whole score drops sharply (presence weight dominates)
        # Other sub-scores stay at 0.5 as neutral fallback
        if not signals.face_present:
            for key in ("eyes_open", "head_pose", "gaze"):
                sub_scores[key] = 0.0

        # Weighted aggregate
        raw_score = sum(
            sub_scores[name] * FOCUS_WEIGHTS[name]
            for name in FOCUS_WEIGHTS
        ) * 100.0  # Scale to 0-100

        # ─── Hard caps for decisive distraction signals ───
        # Some signals are categorical, not gradual: if you're drowsy or
        # staring down at your phone, the aggregate shouldn't average it
        # away with "well, the rest looks fine."
        if signals.face_present:
            # Drowsy = sustained eye closure → not focused, period
            if signals.is_drowsy:
                raw_score = min(raw_score, 30.0)

            # Strong head-down (well past threshold) = phone-checking signature
            if signals.pitch is not None and -signals.pitch > HEAD_PITCH_THRESHOLD + 10:
                raw_score = min(raw_score, 49.0)

            # Strong head-side (talking to someone, looking at second monitor)
            if signals.yaw is not None and abs(signals.yaw) > HEAD_YAW_THRESHOLD + 15:
                raw_score = min(raw_score, 55.0)

        # Update smoothing buffer
        self._score_history.append(raw_score)
        smoothed_score = sum(self._score_history) / len(self._score_history)

        # Classify state
        if not signals.face_present:
            state = FocusState.ABSENT
        elif smoothed_score >= SCORE_FOCUSED:
            state = FocusState.FOCUSED
        elif smoothed_score >= SCORE_DRIFTING:
            state = FocusState.DRIFTING
        else:
            state = FocusState.DISTRACTED

        return FocusReading(
            timestamp=time.time(),
            raw_score=raw_score,
            smoothed_score=smoothed_score,
            state=state,
            signals=signals,
            sub_scores=sub_scores,
        )

    def reset(self):
        """Clear smoothing history."""
        self._score_history.clear()
