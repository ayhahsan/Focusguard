"""
FocusGuard — AI focus coach using computer vision.

Quick start:
    from focusguard import FocusGuard
    FocusGuard().run()
"""
from .app import FocusGuard
from .core.focus_score import FocusState, FocusReading, FrameSignals

__version__ = "0.1.0"
__all__ = ["FocusGuard", "FocusState", "FocusReading", "FrameSignals"]
