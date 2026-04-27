"""
FocusGuard web server.

Place this file at:  focusguard_starter/server.py
Run with:           python server.py
Then open:          http://localhost:5000

What it does:
  - Serves the FocusGuard web UI (index.html)
  - When you click "Start Session", launches focusguard/focusguard.py in a subprocess
  - Reads live state + session history from JSON files written by session_logger.py
"""
from flask import Flask, jsonify, request, send_file
from pathlib import Path
import subprocess
import sys
import json
import time

ROOT = Path(__file__).resolve().parent
FOCUSGUARD_SCRIPT = ROOT / 'focusguard' / 'focusguard.py'
STATE_FILE = ROOT / 'state.json'
SESSIONS_FILE = ROOT / 'sessions.json'
INDEX_FILE = ROOT / 'index.html'

app = Flask(__name__)

# Process state
session = {
    'process': None,
    'started_at': None,
    'companion': 'batman',
}


def read_json(path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return default


@app.route('/')
def index():
    if not INDEX_FILE.exists():
        return f'index.html not found at {INDEX_FILE}', 500
    return send_file(INDEX_FILE)


@app.route('/api/start', methods=['POST'])
def start_session():
    proc = session['process']
    if proc is not None and proc.poll() is None:
        return jsonify({'error': 'A session is already running'}), 409

    if not FOCUSGUARD_SCRIPT.exists():
        return jsonify({
            'error': f'focusguard.py not found at {FOCUSGUARD_SCRIPT}'
        }), 500

    body = request.get_json(silent=True) or {}
    companion = body.get('companion', 'batman')

    # Clean up old live state
    if STATE_FILE.exists():
        try:
            STATE_FILE.unlink()
        except OSError:
            pass

    # Pass companion to subprocess via env var (focusguard can read it if you want)
    import os
    env = os.environ.copy()
    env['FG_COMPANION'] = companion

    proc = subprocess.Popen(
        [sys.executable, str(FOCUSGUARD_SCRIPT)],
        cwd=str(FOCUSGUARD_SCRIPT.parent),
        env=env,
    )

    session['process'] = proc
    session['started_at'] = time.time()
    session['companion'] = companion

    return jsonify({'status': 'started', 'companion': companion})


@app.route('/api/status')
def status():
    proc = session['process']

    if proc is None:
        return jsonify({'active': False, 'ever_started': False})

    if proc.poll() is None:
        # Still running
        elapsed = int(time.time() - session['started_at'])
        live = read_json(STATE_FILE, default={}) or {}
        return jsonify({
            'active': True,
            'elapsed': elapsed,
            'companion': session['companion'],
            'live': live,
        })

    # Process ended — return last session if available
    return jsonify({
        'active': False,
        'ever_started': True,
        'last_companion': session['companion'],
    })


@app.route('/api/last')
def last_session():
    sessions = read_json(SESSIONS_FILE, default=[]) or []
    if not sessions:
        return jsonify(None)
    return jsonify(sessions[-1])


@app.route('/api/sessions')
def all_sessions():
    sessions = read_json(SESSIONS_FILE, default=[]) or []
    return jsonify(sessions)


if __name__ == '__main__':
    print('=' * 56)
    print('  FocusGuard Web')
    print('  Open in browser:  http://localhost:5000')
    print('  Press Ctrl+C to stop the server.')
    print('=' * 56)
    app.run(host='127.0.0.1', port=5000, debug=False)