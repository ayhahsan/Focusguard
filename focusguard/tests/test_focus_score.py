"""
Tests for FocusScoreEngine — pure logic, no camera/MediaPipe needed.

Run with:
    pytest tests/test_focus_score.py -v
"""
import pytest

from focusguard.core.focus_score import (
    FocusScoreEngine, FrameSignals, FocusState,
)


def test_absent_when_no_face():
    engine = FocusScoreEngine()
    signals = FrameSignals(face_present=False)
    reading = engine.compute(signals)
    assert reading.state == FocusState.ABSENT
    assert reading.smoothed_score < 30  # presence weight 0.30 → max 30 if absent


def test_focused_with_good_signals():
    engine = FocusScoreEngine()
    # All signals indicate good focus
    signals = FrameSignals(
        face_present=True,
        avg_ear=0.30,         # eyes wide open
        is_drowsy=False,
        pitch=0.0, yaw=0.0, roll=0.0,  # head straight
        gaze_drift=0.0,       # looking forward
    )
    # Run multiple frames so smoothing settles
    for _ in range(20):
        reading = engine.compute(signals)
    assert reading.state == FocusState.FOCUSED
    assert reading.smoothed_score >= 70


def test_drowsy_drops_score():
    engine = FocusScoreEngine()
    drowsy_signals = FrameSignals(
        face_present=True,
        avg_ear=0.10,
        is_drowsy=True,
        pitch=0.0, yaw=0.0,
        gaze_drift=0.0,
    )
    for _ in range(20):
        reading = engine.compute(drowsy_signals)
    # Drowsy should drag score below FOCUSED
    assert reading.state != FocusState.FOCUSED


def test_looking_down_drops_score():
    engine = FocusScoreEngine()
    looking_at_phone = FrameSignals(
        face_present=True,
        avg_ear=0.30,
        is_drowsy=False,
        pitch=-40.0,  # Strongly looking down
        yaw=0.0,
        gaze_drift=0.0,
    )
    for _ in range(20):
        reading = engine.compute(looking_at_phone)
    # Should not be focused if looking down
    assert reading.state != FocusState.FOCUSED


def test_smoothing_reduces_jitter():
    engine = FocusScoreEngine()
    good = FrameSignals(face_present=True, avg_ear=0.30, pitch=0, yaw=0, gaze_drift=0)
    bad = FrameSignals(face_present=False)

    # Alternate good/bad signals
    readings = []
    for i in range(30):
        signals = good if i % 2 == 0 else bad
        readings.append(engine.compute(signals))

    # Raw scores swing wildly; smoothed scores should be in middle range
    smoothed = [r.smoothed_score for r in readings[10:]]  # after warm-up
    # All smoothed values should be within a moderate band (no extreme jumps)
    assert max(smoothed) - min(smoothed) < 60


def test_sub_scores_present_when_face_detected():
    engine = FocusScoreEngine()
    signals = FrameSignals(
        face_present=True, avg_ear=0.25, pitch=5, yaw=5, gaze_drift=0.1,
    )
    reading = engine.compute(signals)
    assert "presence" in reading.sub_scores
    assert "eyes_open" in reading.sub_scores
    assert "head_pose" in reading.sub_scores
    assert "gaze" in reading.sub_scores
    for v in reading.sub_scores.values():
        assert 0.0 <= v <= 1.0


def test_score_in_zero_to_hundred():
    engine = FocusScoreEngine()
    # Try a bunch of varied signals
    for ear in [0.10, 0.20, 0.30]:
        for pitch in [-30, -10, 0, 10, 30]:
            for drift in [0, 0.3, 0.6, 1.0]:
                signals = FrameSignals(
                    face_present=True,
                    avg_ear=ear, pitch=pitch, yaw=0,
                    gaze_drift=drift,
                )
                reading = engine.compute(signals)
                assert 0.0 <= reading.smoothed_score <= 100.0


def test_reset_clears_smoothing():
    engine = FocusScoreEngine()
    good = FrameSignals(face_present=True, avg_ear=0.30, pitch=0, yaw=0, gaze_drift=0)
    for _ in range(20):
        engine.compute(good)

    engine.reset()
    bad = FrameSignals(face_present=False)
    reading = engine.compute(bad)
    # After reset, smoothed score == raw score (only one sample)
    assert abs(reading.smoothed_score - reading.raw_score) < 0.01
