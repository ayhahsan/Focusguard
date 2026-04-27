# FocusGuard

> AI focus coach that watches you, not your apps. 100% offline.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Privacy: Offline](https://img.shields.io/badge/Privacy-100%25%20Offline-green.svg)]()

The average worker can't focus for more than 4 minutes without getting distracted. FocusGuard uses your webcam + AI to detect distraction in real-time — phone pickup, gaze drift, drowsiness, absence — and helps you stay in deep work.

**Your webcam feed never leaves your machine.**

## Why FocusGuard?

Most productivity tools track your **apps**. FocusGuard tracks **you**:

- 👁️ **Eye gaze** — are you actually looking at the screen?
- 🪶 **Head pose** — looking down at your phone?
- 😴 **Drowsiness** — eye closure rate
- 🪑 **Presence** — did you walk away from desk?
- 📱 **Phone detection** — coming in v0.2

All processed locally. No cloud. No accounts. No tracking.

## Install

```bash
git clone https://github.com/ayhahsan/Focusguard.git
cd focusguard
pip install -r requirements.txt
```

## Run

```bash
python focusguard.py
```

Window opens with your webcam feed and a live focus score. Try:
- Pick up your phone — score drops, "DISTRACTED" state
- Close your eyes for 2+ seconds — drowsy detected
- Look away — gaze drift detected
- Walk away — "ABSENT" state

Press **Q** to quit. End-of-session summary printed in terminal.

## How It Works

```
Webcam → MediaPipe Face Mesh → Signals → Focus Score Engine → Live Overlay
                                  ├─ Eye Aspect Ratio (drowsiness)
                                  ├─ Head pose (solvePnP)
                                  ├─ Iris-based gaze direction
                                  └─ Face presence
```

The focus score is a weighted aggregate of these signals, smoothed over a 1-second window to prevent jitter.

## Privacy

- Webcam frames are processed in-memory and **never written to disk**
- No internet connection used (or required) at runtime
- All ML models run locally via MediaPipe
- See `focusguard/app.py` — the entire pipeline is auditable

## Roadmap

- [x] **v0.1 Week 1** — Core eye/head tracking, focus score, live overlay
- [ ] **v0.2 Week 2** — Phone detection (YOLOv8-nano), yawn detection, smart alerts
- [ ] **v0.3 Week 3** — SQLite logger, Streamlit dashboard with daily heatmaps
- [ ] **v0.4 Week 4** — System tray app, packaged installers, launch

## Configuration

Edit `focusguard/config.py` to tune thresholds:
- `EAR_DROWSY_THRESHOLD` — when to flag eyes as closed
- `HEAD_PITCH_THRESHOLD` — how far down before "looking at phone"
- `FOCUS_WEIGHTS` — relative importance of each signal

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

Tests run without a webcam — they test the score logic directly.

## License

MIT — fork it, ship it, build on it.

## Author

Built by [Ayhahsan Ansari](https://github.com/ayhahsan), who also created [Profiled](https://github.com/ayhahsan/profiled) — an offline tool to discover what platforms know about you.

Both tools share the same belief: **AI should empower you, not surveil you.**

---

If FocusGuard helps you reclaim deep work, give it a star ⭐
