"""
Main FocusGuard application.

Camera loop:
  1. Capture frame from webcam
  2. Run face detection (MediaPipe)
  3. Compute eye/head/gaze signals
  4. Aggregate into focus score
  5. Draw overlay
  6. Display + log
"""
from collections import Counter
from typing import Optional
import time
from .session_logger import SessionLogger
import os

from .config import (
    CAMERA_INDEX,
    TARGET_FPS,
    FRAME_WIDTH,
    FRAME_HEIGHT,
    WINDOW_NAME,
)
from .core.face_detector import FaceDetector
from .core.eye_tracker import DrowsinessDetector
from .core.head_pose import estimate_head_pose
from .core.gaze_estimator import estimate_gaze
from .core.focus_score import (
    FocusScoreEngine, FrameSignals, FocusState, FocusReading,
)
from .utils.overlay import draw_focus_overlay


class FocusGuard:
    """
    Main application orchestrator.

    Usage:
        app = FocusGuard()
        app.run()        # blocks until user presses Q
    """

    def __init__(
        self,
        camera_index: int = CAMERA_INDEX,
        show_window: bool = True,
        show_landmarks: bool = True,
    ):
        self.camera_index = camera_index
        self.show_window = show_window
        self.show_landmarks = show_landmarks
        self.logger = SessionLogger()

        # Initialize components (lazy-load heavy dependencies)
        self.face_detector = FaceDetector()
        self.drowsiness = DrowsinessDetector()
        self.score_engine = FocusScoreEngine()

        # Session stats
        self._session_start: Optional[float] = None
        self._state_counter: Counter = Counter()
        self._readings_count = 0
        self._sum_scores = 0.0

    def _process_frame(self, frame) -> tuple:
        """
        Run all detectors on one frame.

        Returns:
            (reading, landmarks_pixels) — landmarks_pixels for overlay.
        """
        landmarks = self.face_detector.detect(frame)

        if landmarks is None:
            # No face — build absent signal
            signals = FrameSignals(face_present=False)
            return self.score_engine.compute(signals), None

        # Convert to pixel coords (needed for head pose)
        landmarks_pixels = FaceDetector.landmarks_to_pixels(
            landmarks, frame.shape,
        )

        # Drowsiness check
        avg_ear, _, is_drowsy = self.drowsiness.update(landmarks)

        # Head pose
        head = estimate_head_pose(landmarks_pixels, frame.shape)
        if head is not None:
            pitch, yaw, roll = head
        else:
            pitch = yaw = roll = None

        # Gaze
        gaze_drift, is_gaze_off = estimate_gaze(landmarks)

        signals = FrameSignals(
            face_present=True,
            avg_ear=avg_ear,
            is_drowsy=is_drowsy,
            pitch=pitch,
            yaw=yaw,
            roll=roll,
            gaze_drift=gaze_drift,
            is_gaze_off=is_gaze_off,
        )

        return self.score_engine.compute(signals), landmarks_pixels

    def _update_session_stats(self, reading: FocusReading):
        self._state_counter[reading.state] += 1
        self._readings_count += 1
        self._sum_scores += reading.smoothed_score

    def _print_session_summary(self):
        if self._session_start is None or self._readings_count == 0:
            print("\nNo data captured.")
            return

        duration = time.time() - self._session_start
        avg_score = self._sum_scores / self._readings_count

        print("\n" + "=" * 50)
        print("FocusGuard — Session Summary")
        print("=" * 50)
        print(f"Duration:         {duration / 60:.1f} min")
        print(f"Average score:    {avg_score:.1f} / 100")
        print()
        print("Time breakdown:")
        total = sum(self._state_counter.values())
        for state in (
            FocusState.FOCUSED,
            FocusState.DRIFTING,
            FocusState.DISTRACTED,
            FocusState.ABSENT,
        ):
            count = self._state_counter.get(state, 0)
            pct = (count / total * 100.0) if total else 0.0
            bar = "█" * int(pct / 2)
            print(f"  {state.value:11s} {pct:5.1f}%  {bar}")
        print("=" * 50)

    def run(self):
        """
        Main loop. Blocks until user presses Q or closes window.
        """
        import cv2

        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError(
                f"Cannot open camera index {self.camera_index}. "
                "Check webcam permissions."
            )

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)

        frame_interval = 1.0 / TARGET_FPS
        self._session_start = time.time()

        print("FocusGuard running. Press Q to quit.")
        print("(First few seconds: models loading, then real-time tracking begins.)")

        try:
            while True:
                loop_start = time.time()

                ok, frame = cap.read()
                if not ok:
                    print("Frame grab failed — exiting.")
                    break

                # Mirror frame for natural user-facing view
                frame = cv2.flip(frame, 1)

                reading, landmarks_pixels = self._process_frame(frame)
                self.logger.add_reading(reading)
                self._update_session_stats(reading)

                if self.show_window:
                    draw_focus_overlay(
                        frame,
                        reading,
                        landmarks_pixels,
                        self.show_landmarks,
                    )
                    cv2.imshow(WINDOW_NAME, frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key in (ord("q"), ord("Q"), 27):  # Q or ESC
                        break

                # Throttle to target FPS
                elapsed = time.time() - loop_start
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)

        finally:
            self.logger.save_session(companion=os.environ.get('FG_COMPANION', 'batman'))
            cap.release()
            if self.show_window:
                cv2.destroyAllWindows()
            self.face_detector.close()
            self._print_session_summary()
