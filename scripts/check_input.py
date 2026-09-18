#!/usr/bin/env python3
"""Opt-in disposable-field input test. Does not record audio or start dictation."""
import json
import os
from pathlib import Path
import subprocess
import time
from live_smoke import ipc, run, state, wait_for

previous = state()
probe = None
try:
    ipc("tablet", "mode", "tablet")
    ipc("tablet", "close")
    wait_for(lambda: state()["keyboardRunning"], "OSK running")
    probe = subprocess.Popen(["python3", str(Path(__file__).with_name("input_probe.py"))],
                             env=dict(os.environ, GTK_IM_MODULE="wayland"))
    wait_for(lambda: json.loads(run("hyprctl", "-j", "activewindow")).get("class") == "io.github.omarchy_tablet.InputProbe", "disposable field focused")
    wait_for(lambda: 'true' in run("busctl", "--user", "get-property", "sm.puri.OSK0", "/sm/puri/OSK0", "sm.puri.OSK0", "Visible"), "OSK opens automatically for GTK field")
    run("wtype", "Keyboard check")
    time.sleep(.5)
    report = json.loads(Path("/tmp/omarchy-tablet-input-probe.json").read_text())
    assert report["characters"] == len("Keyboard check"), report
    assert report["fieldFocused"], report
    print("PASS Wayland field accepts input; physical speech transcription remains a manual check")
finally:
    if probe:
        probe.terminate()
        probe.wait(timeout=5)
    ipc("tablet", "layout", previous["layout"])
    ipc("tablet", "mode", previous["mode"])
