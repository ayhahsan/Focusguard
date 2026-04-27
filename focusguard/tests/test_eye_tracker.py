"""
Tests for EAR (Eye Aspect Ratio) computation.

Uses synthetic landmark data — no camera needed.
"""
import numpy as np
import pytest

from focusguard.core.eye_tracker import compute_ear, DrowsinessDetector


def _make_landmarks(eye_open: bool = True, n: int = 478):
    """
    Create synthetic 478-landmark array with one eye configured.

    For LEFT_EYE_EAR indices [33, 160, 158, 133, 153, 144],
    we set them so EAR = high (open) or low (closed).
    """
    landmarks = np.zeros((n, 3), dtype=np.float32)

    # Eye open: vertical distance ~0.06, horizontal ~0.20 → EAR ≈ 0.30
    # Eye closed: vertical ~0.01, horizontal ~0.20 → EAR ≈ 0.05
    if eye_open:
        v_offset = 0.03
    else:
        v_offset = 0.005

    # LEFT_EYE_EAR indices in order
    left_idx = [33, 160, 158, 133, 153, 144]
    # p1: outer corner, p4: inner corner (horizontal endpoints)
    landmarks[left_idx[0]] = [0.10, 0.20, 0]   # p1
    landmarks[left_idx[3]] = [0.30, 0.20, 0]   # p4
    # p2, p3: top eyelid
    landmarks[left_idx[1]] = [0.15, 0.20 - v_offset, 0]
    landmarks[left_idx[2]] = [0.25, 0.20 - v_offset, 0]
    # p5, p6: bottom eyelid
    landmarks[left_idx[4]] = [0.25, 0.20 + v_offset, 0]
    landmarks[left_idx[5]] = [0.15, 0.20 + v_offset, 0]

    # Same for right eye
    right_idx = [362, 385, 387, 263, 373, 380]
    landmarks[right_idx[0]] = [0.60, 0.20, 0]
    landmarks[right_idx[3]] = [0.80, 0.20, 0]
    landmarks[right_idx[1]] = [0.65, 0.20 - v_offset, 0]
    landmarks[right_idx[2]] = [0.75, 0.20 - v_offset, 0]
    landmarks[right_idx[4]] = [0.75, 0.20 + v_offset, 0]
    landmarks[right_idx[5]] = [0.65, 0.20 + v_offset, 0]

    return landmarks


def test_ear_open_eye_high():
    """An open eye should have EAR > 0.20."""
    landmarks = _make_landmarks(eye_open=True)
    ear = compute_ear(landmarks, [33, 160, 158, 133, 153, 144])
    assert ear > 0.20, f"Expected open eye EAR > 0.20, got {ear:.3f}"


def test_ear_closed_eye_low():
    """A closed eye should have EAR < 0.10."""
    landmarks = _make_landmarks(eye_open=False)
    ear = compute_ear(landmarks, [33, 160, 158, 133, 153, 144])
    assert ear < 0.10, f"Expected closed eye EAR < 0.10, got {ear:.3f}"


def test_ear_requires_six_landmarks():
    landmarks = np.zeros((478, 3), dtype=np.float32)
    with pytest.raises(ValueError):
        compute_ear(landmarks, [33, 160, 158])  # only 3


def test_drowsiness_detector_no_false_positive_on_blink():
    """A few frames of closed eyes should NOT trigger drowsy."""
    detector = DrowsinessDetector(frame_count=30)
    closed_landmarks = _make_landmarks(eye_open=False)

    # Simulate a blink: 5 frames closed
    for _ in range(5):
        _, _, is_drowsy = detector.update(closed_landmarks)

    assert not is_drowsy, "Brief blink should not trigger drowsy"


def test_drowsiness_triggers_on_sustained_closure():
    """30+ frames of closed eyes should trigger drowsy."""
    detector = DrowsinessDetector(frame_count=30)
    closed_landmarks = _make_landmarks(eye_open=False)

    is_drowsy = False
    for _ in range(35):
        _, _, is_drowsy = detector.update(closed_landmarks)

    assert is_drowsy, "Sustained closure should trigger drowsy"


def test_drowsiness_resets_on_eye_open():
    """Counter should reset when eyes open again."""
    detector = DrowsinessDetector(frame_count=30)

    # Close 20 frames (not enough)
    closed = _make_landmarks(eye_open=False)
    for _ in range(20):
        detector.update(closed)
    assert detector.closed_frame_count == 20

    # Open eyes — counter resets
    open_lm = _make_landmarks(eye_open=True)
    detector.update(open_lm)
    assert detector.closed_frame_count == 0
