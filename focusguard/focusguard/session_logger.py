"""
Session logger for FocusGuard.

Place this file at:  focusguard_starter/focusguard/focusguard/session_logger.py

This writes:
  - state.json     : live stats while session runs (overwritten ~once per second)
  - sessions.json  : append-only history of completed sessions

Both files live in focusguard_starter/ (project root).
"""
import json
import os
import time
from pathlib import Path
from datetime import datetime

# focusguard_starter/focusguard/focusguard/session_logger.py
#                  └── ROOT (focusguard_starter)
ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE = ROOT / 'state.json'
SESSIONS_FILE = ROOT / 'sessions.json'


def _state_name(reading):
    """Pull a state name out of whatever reading object the engine returns."""
    state = getattr(reading, 'state', None)
    if state is None:
        return 'unknown'
    name = getattr(state, 'name', None)
    if name:
        return name.lower()
    return str(state).lower()


class SessionLogger:
    """
    Drop-in session tracker. Use it like this in your FocusGuard.run() loop:

        from .session_logger import SessionLogger

        # in __init__:
        self.logger = SessionLogger()

        # inside the frame loop, after you compute `reading`:
        self.logger.add_reading(reading)

        # right before run() returns / breaks out of the loop:
        self.logger.save_session(companion=os.environ.get('FG_COMPANION', 'batman'))
    """

    def __init__(self):
        self.start_time = time.time()
        self.readings = []   # list of (timestamp_offset, state_name)
        self._last_disk_write = 0.0

        # Wipe stale live-state from any previous run
        if STATE_FILE.exists():
            try:
                STATE_FILE.unlink()
            except OSError:
                pass

    def add_reading(self, reading):
        offset = time.time() - self.start_time
        self.readings.append((offset, _state_name(reading)))

        now = time.time()
        if now - self._last_disk_write > 1.0:
            self._write_live_state()
            self._last_disk_write = now

    def _aggregate(self):
        n = len(self.readings)
        if n == 0:
            return {
                'focused': 0, 'distracted': 0, 'absent': 0, 'unknown': 0,
                'focused_pct': 0.0, 'absent_pct': 0.0, 'distracted_pct': 0.0,
                'score': 0,
            }
        counts = {'focused': 0, 'distracted': 0, 'absent': 0, 'unknown': 0}
        for _, state in self.readings:
            counts[state] = counts.get(state, 0) + 1
        focused_pct = counts['focused'] / n * 100
        absent_pct = counts['absent'] / n * 100
        distracted_pct = counts['distracted'] / n * 100
        return {
            **counts,
            'focused_pct': round(focused_pct, 1),
            'absent_pct': round(absent_pct, 1),
            'distracted_pct': round(distracted_pct, 1),
            # Simple score: focused% minus a penalty for absences
            'score': max(0, round(focused_pct - absent_pct * 0.5)),
        }

    def _seconds_split(self):
        elapsed = time.time() - self.start_time
        n = len(self.readings)
        if n == 0 or elapsed <= 0:
            return {'focused_seconds': 0, 'absent_seconds': 0, 'distracted_seconds': 0}
        sec_per_reading = elapsed / n
        agg = self._aggregate()
        return {
            'focused_seconds': int(agg['focused'] * sec_per_reading),
            'absent_seconds': int(agg['absent'] * sec_per_reading),
            'distracted_seconds': int(agg['distracted'] * sec_per_reading),
        }

    def _write_live_state(self):
        try:
            elapsed = int(time.time() - self.start_time)
            agg = self._aggregate()
            secs = self._seconds_split()
            payload = {
                'elapsed': elapsed,
                'score': agg['score'],
                'focused_pct': agg['focused_pct'],
                'absent_pct': agg['absent_pct'],
                'distracted_pct': agg['distracted_pct'],
                **secs,
            }
            STATE_FILE.write_text(json.dumps(payload), encoding='utf-8')
        except OSError:
            pass

    def _build_timeline(self, segments=60):
        if not self.readings:
            return []
        total = self.readings[-1][0]
        if total < 1:
            return []
        seg_dur = total / segments
        timeline = []
        for i in range(segments):
            lo, hi = i * seg_dur, (i + 1) * seg_dur
            slice_states = [s for t, s in self.readings if lo <= t < hi]
            if not slice_states:
                timeline.append('absent')
                continue
            focused = slice_states.count('focused')
            absent = slice_states.count('absent')
            if focused / len(slice_states) >= 0.5:
                timeline.append('focused')
            elif absent / len(slice_states) >= 0.3:
                timeline.append('absent')
            else:
                timeline.append('distracted')
        return timeline

    def save_session(self, companion='batman'):
        elapsed = int(time.time() - self.start_time)
        agg = self._aggregate()
        secs = self._seconds_split()

        record = {
            'started_at': datetime.fromtimestamp(self.start_time).isoformat(timespec='seconds'),
            'ended_at': datetime.now().isoformat(timespec='seconds'),
            'duration_seconds': elapsed,
            'focus_score': agg['score'],
            'focused_pct': agg['focused_pct'],
            'absent_pct': agg['absent_pct'],
            'distracted_pct': agg['distracted_pct'],
            **secs,
            'companion': companion,
            'timeline': self._build_timeline(),
        }

        sessions = []
        if SESSIONS_FILE.exists():
            try:
                sessions = json.loads(SESSIONS_FILE.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, OSError):
                sessions = []
        sessions.append(record)
        SESSIONS_FILE.write_text(json.dumps(sessions, indent=2), encoding='utf-8')

        # Clean up live state file
        if STATE_FILE.exists():
            try:
                STATE_FILE.unlink()
            except OSError:
                pass

        return record