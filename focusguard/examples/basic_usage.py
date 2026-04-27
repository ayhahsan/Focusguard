"""
Basic FocusGuard usage example.

Run from the project root:
    python examples/basic_usage.py
"""
from focusguard import FocusGuard


def main():
    print("Starting FocusGuard...")
    print("Tip: try picking up your phone, looking down, or closing eyes")
    print("     to see the focus score react. Press Q to quit.\n")

    app = FocusGuard(
        camera_index=0,
        show_window=True,
        show_landmarks=True,
    )
    app.run()


if __name__ == "__main__":
    main()
