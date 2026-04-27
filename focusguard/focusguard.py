"""
FocusGuard CLI entry point.

Usage:
    python focusguard.py             # Default: webcam 0, with overlay
    python focusguard.py --camera 1  # Use second webcam
    python focusguard.py --no-landmarks  # Hide landmark dots
"""
import argparse
import sys

from focusguard import FocusGuard


def main():
    parser = argparse.ArgumentParser(
        description="FocusGuard — AI focus coach (privacy-first, runs offline)",
    )
    parser.add_argument(
        "--camera", type=int, default=0,
        help="Camera index (default: 0)",
    )
    parser.add_argument(
        "--no-window", action="store_true",
        help="Run headless (no preview window)",
    )
    parser.add_argument(
        "--no-landmarks", action="store_true",
        help="Hide eye landmark dots in overlay",
    )
    args = parser.parse_args()

    print("=" * 50)
    print("  FocusGuard v0.1 — Privacy-first AI focus coach")
    print("  100% offline. No data leaves your machine.")
    print("=" * 50)

    try:
        app = FocusGuard(
            camera_index=args.camera,
            show_window=not args.no_window,
            show_landmarks=not args.no_landmarks,
        )
        app.run()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)
    except RuntimeError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
