"""
MediaPipe Face Mesh wrapper.

Webcam frame in karo → 478 facial landmarks out (or None if no face).
Lazy-loads MediaPipe to keep import fast.
"""
from typing import Optional, List, Tuple
import numpy as np


class FaceDetector:
    """
    Wraps MediaPipe Face Mesh for landmark detection.

    Refined landmarks include iris (478 total instead of 468).
    Iris tracking is essential for gaze estimation.
    """

    def __init__(self, max_faces: int = 1, min_detection_confidence: float = 0.5):
        self.max_faces = max_faces
        self.min_detection_confidence = min_detection_confidence
        self._mesh = None  # Lazy load

    def _load_model(self):
        if self._mesh is None:
            try:
                import mediapipe as mp
            except ImportError:
                raise ImportError(
                    "mediapipe required. Install: pip install mediapipe"
                )
            self._mp_face_mesh = mp.solutions.face_mesh
            self._mesh = self._mp_face_mesh.FaceMesh(
                max_num_faces=self.max_faces,
                refine_landmarks=True,           # Required for iris landmarks
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=0.5,
            )
        return self._mesh

    def detect(self, frame_bgr: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect face landmarks in a BGR frame (OpenCV format).

        Args:
            frame_bgr: Frame from cv2.VideoCapture (height, width, 3) BGR

        Returns:
            np.ndarray of shape (478, 3) with normalized [x, y, z] coords,
            or None if no face detected.
        """
        import cv2
        mesh = self._load_model()

        # MediaPipe expects RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # Disable write flag — small perf optimization
        frame_rgb.flags.writeable = False
        results = mesh.process(frame_rgb)

        if not results.multi_face_landmarks:
            return None

        # Take first face (we only track one)
        face = results.multi_face_landmarks[0]
        landmarks = np.array(
            [[lm.x, lm.y, lm.z] for lm in face.landmark],
            dtype=np.float32,
        )
        return landmarks

    @staticmethod
    def landmarks_to_pixels(
        landmarks: np.ndarray,
        frame_shape: Tuple[int, int, int],
    ) -> np.ndarray:
        """
        Convert normalized landmarks [0,1] to pixel coordinates.

        Args:
            landmarks: (N, 3) array of normalized coords
            frame_shape: (height, width, channels) from frame.shape

        Returns:
            (N, 2) array of [x_pixel, y_pixel]
        """
        h, w = frame_shape[:2]
        pixels = landmarks[:, :2].copy()
        pixels[:, 0] *= w
        pixels[:, 1] *= h
        return pixels.astype(np.int32)

    def close(self):
        """Release MediaPipe resources."""
        if self._mesh is not None:
            self._mesh.close()
            self._mesh = None
