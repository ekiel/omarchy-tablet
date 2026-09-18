#!/usr/bin/env python3
"""Opt-in live checks. Temporarily changes shell palette/font and display rotation.

Restores original settings in finally. Run from an unlocked Omarchy session.
Captures only the tablet Home, never application windows or user text.
"""
import base64
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/screenshots"


def run(*args):
    p = subprocess.run(args, capture_output=True, text=True, timeout=20)
    if p.returncode:
        raise RuntimeError(f"{args[0]}: {p.stderr.strip() or p.stdout.strip()}")
    return p.stdout.strip()


def ipc(*args):
    return run("omarchy-shell", *args)


def state():
    return json.loads(ipc("tablet", "status"))


def wait_for(test, label):
    for _ in range(30):
        if test():
            print(f"PASS {label}", flush=True)
            return
        time.sleep(.3)
    raise AssertionError(label)


def theme(path):
    def b64(file):
        return base64.b64encode(file.read_bytes() if file.exists() else b"").decode()
    ipc("shell", "applyTheme", b64(path / "colors.toml"), b64(path / "shell.toml"))


def rotate(monitor, transform):
    # Names are compositor-provided; json quoting is also valid for this Lua string.
    run("hyprctl", "eval", 'hl.monitor({output=' + json.dumps(monitor["name"]) + ', transform=' + str(transform) + '})')
    time.sleep(1.2)
    actual = next(m for m in json.loads(run("hyprctl", "-j", "monitors")) if m["name"] == monitor["name"])
    assert actual["transform"] == transform, actual


def capture(name):
    ipc("tablet", "home")
    time.sleep(.7)
    run("grim", str(OUT / f"{name}.png"))
    print(f"CAPTURE {name}", flush=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    original = state()
    font_path = Path.home() / ".config/omarchy/shell.toml"
    original_font = font_path.read_bytes() if font_path.exists() else None
    theme_path = Path.home() / ".local/state/omarchy/current/theme"
    monitors = json.loads(run("hyprctl", "-j", "monitors"))
    monitor = next(m for m in monitors if m["name"].startswith(("eDP", "DSI", "LVDS")))
    initial_clients = json.loads(run("hyprctl", "-j", "clients"))
    report = []
    autorotate = subprocess.run(["systemctl", "--user", "is-active", "--quiet", "surface-autorotate.service"]).returncode == 0
    try:
        if autorotate:
            run("systemctl", "--user", "stop", "surface-autorotate.service")
        ipc("shell", "hide", "omarchy.audio")
        ipc("tablet", "close")
        ipc("tablet", "mode", "tablet")
        ipc("tablet", "layout", "single")
        wait_for(lambda: state()["tablet"] and state()["keyboardRunning"], "tablet + keyboard service")
        time.sleep(1)
        assert not state()["error"], state()["error"]
        for c in json.loads(run("hyprctl", "-j", "clients")):
            if c["address"] == initial_clients[0]["address"] and not c["floating"]:
                assert c["fullscreen"] == 1, c
        report.append("Single app maximizes active internal window")
        ipc("tablet", "layout", "tiling")
        time.sleep(1)
        # Single was already active at the beginning; normal restoration is 0.
        current = json.loads(run("hyprctl", "-j", "clients"))
        assert all(c["fullscreen"] == 0 for c in current if c["address"] == initial_clients[0]["address"])
        report.append("Omarchy tiling restores window state")
        ipc("tablet", "keyboard")
        wait_for(lambda: 'true' in run("busctl", "--user", "get-property", "sm.puri.OSK0", "/sm/puri/OSK0", "sm.puri.OSK0", "Visible"), "manual OSK visible")
        ipc("tablet", "keyboard")
        wait_for(lambda: 'false' in run("busctl", "--user", "get-property", "sm.puri.OSK0", "/sm/puri/OSK0", "sm.puri.OSK0", "Visible"), "manual OSK hidden")
        report.append("Manual on-screen keyboard show/hide")
        for plugin in ("audio", "bluetooth", "network", "power", "clock", "monitor", "agents"):
            assert ipc("shell", "summon", "omarchy." + plugin, "{}") == "ok"
            time.sleep(.3)
            ipc("shell", "hide", "omarchy." + plugin)
            report.append(f"Native {plugin} popup lifecycle")
        font_path.write_text("[font]\nbase-size = 12\n")
        time.sleep(1)
        theme(Path("/usr/share/omarchy/themes/tokyo-night"))
        rotate(monitor, 0)
        capture("landscape-tokyo-night")
        geometry = json.loads(ipc("tablet-bar", "geometry"))
        assert all(s["loaded"] for h in geometry for s in h["slots"]), geometry
        assert len(geometry[0]["slots"]) >= 14
        report.append("Configured native widgets loaded")
        rotate(monitor, 1)
        capture("portrait-tokyo-night")
        ipc("tablet-bar", "more")
        time.sleep(.7)
        run("grim", str(OUT / "portrait-more.png"))
        ipc("tablet-bar", "more")
        theme(Path("/usr/share/omarchy/themes/catppuccin-latte"))
        capture("portrait-latte")
        font_path.write_text("[font]\nbase-size = 20\n")
        time.sleep(1)
        capture("portrait-large-text")
        report.append("Portrait/landscape, dark/light palette and 12/20px font captures")
        ipc("shell", "rescanPlugins")
        time.sleep(2)
        assert not state()["error"], state()["error"]
        assert len(json.loads(ipc("tablet-bar", "geometry"))[0]["slots"]) >= 14
        report.append("Plugin rescan preserves widgets and backend")
        ipc("tablet", "mode", "desktop")
        wait_for(lambda: not state()["keyboardRunning"], "desktop releases OSK")
        report.append("Desktop mode releases keyboard service")
    finally:
        rotate(monitor, monitor["transform"])
        if autorotate:
            run("systemctl", "--user", "start", "surface-autorotate.service")
        if original_font is None:
            font_path.unlink(missing_ok=True)
        else:
            font_path.write_bytes(original_font)
        theme(theme_path)
        ipc("tablet", "close")
        ipc("tablet", "layout", original["layout"])
        ipc("tablet", "mode", original["mode"])
        (ROOT / "docs/live-results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
