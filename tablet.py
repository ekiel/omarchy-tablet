#!/usr/bin/env python3
"""Small session backend: hardware presence, preferences and the Wayland OSK.

No text, keystrokes, window contents or credentials are read or stored.
The QML service owns this process through stdin/stdout JSON messages.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import select
import shlex
import shutil
import signal
import subprocess
import struct
import sys
import time

DEFAULT_FAVORITES = ["chromium", "org.gnome.Nautilus", "com.github.xournalpp.xournalpp",
                     "libreoffice-writer", "YouTube", "org.gnome.Calculator", "murmure", "localsend"]
MODES = {"auto", "tablet", "desktop"}


def valid_command(value):
    return (isinstance(value, list) and bool(value)
            and all(isinstance(v, str) and v and "\0" not in v for v in value))


def wallpaper():
    path = Path.home() / ".local/state/omarchy/current/background"
    return path.resolve().as_uri() if path.exists() else ""


def physical_keyboard_present(devices):
    """Use Linux input topology, not virtual-keyboard counts from Hyprland."""
    for block in devices.split("\n\n"):
        name = re.search(r'^N: Name="(.*)"$', block, re.M)
        path = re.search(r"^S: Sysfs=(.*)$", block, re.M)
        handlers = re.search(r"^H: Handlers=(.*)$", block, re.M)
        if not (name and path and handlers):
            continue
        if "kbd" not in handlers[1].split() or "/virtual/" in path[1]:
            continue
        label = name[1].lower()
        if any(word in label for word in ("virtual", "video bus", "buttons", "power button", "speaker", "consumer control", "system control")):
            continue
        keys = re.search(r"^B: KEY=(.*)$", block, re.M)
        if keys:
            bits = 0
            for word in keys[1].split():
                bits = (bits << (struct.calcsize("L") * 8)) | int(word, 16)
            if all(bits & (1 << code) for code in (28, 30, 44, 57)):
                return True
            continue
        if "keyboard" in label or "type cover" in label:
            return True
    return False


def tablet_mode(mode, attached):
    return mode == "tablet" or (mode == "auto" and not attached)


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


def run(*args, check=True):
    result = subprocess.run(args, capture_output=True, text=True, timeout=12)
    if check and result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip()[:300])
    return result


class Backend:
    def __init__(self, state_dir=None):
        self.state_dir = Path(state_dir or Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "omarchy-tablet")
        self.preferences_path = self.state_dir / "preferences.json"
        self.preferences = {"mode": "auto", "favorites": DEFAULT_FAVORITES.copy(), "layout": "single",
                            "dictationCommand": ["murmure", "--transcription"]}
        if self.preferences_path.exists():
            try:
                saved = json.loads(self.preferences_path.read_text())
            except (ValueError, OSError):
                saved = {}
            if saved.get("layout") in {"single", "tiling"}:
                self.preferences["layout"] = saved["layout"]
            if valid_command(saved.get("dictationCommand")):
                self.preferences["dictationCommand"] = saved["dictationCommand"]
            if saved.get("mode") in MODES:
                self.preferences["mode"] = saved["mode"]
            if isinstance(saved.get("favorites"), list):
                self.preferences["favorites"] = [s for s in saved["favorites"] if isinstance(s, str)]
        self.runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "omarchy-tablet"
        self.runtime.mkdir(mode=0o700, exist_ok=True)
        self.lease = self.runtime / "keyboard-lease.json"
        self.manual_keyboard = False
        self.keyboard_started = False
        self.error = ""
        self.last_mode = None
        self.retry_after = 0
        self.running = True
        from layout import SingleApp
        self.layout = SingleApp(self.runtime / "window-lease.json")
        self.dictation_process = None
        self.animations = True
        self.next_style_check = 0

    def active(self, unit):
        return run("systemctl", "--user", "is-active", "--quiet", unit, check=False).returncode == 0

    def restore_keyboard(self):
        if not self.lease.exists():
            return
        lease = json.loads(self.lease.read_text())
        run("systemctl", "--user", "stop", "omarchy-tablet-keyboard.service", check=False)
        if "oskEnabled" in lease:
            run("gsettings", "set", "org.gnome.desktop.a11y.applications", "screen-keyboard-enabled", lease["oskEnabled"])
        if lease.get("fcitx"):
            run("systemctl", "--user", "start", "omarchy-fcitx5.service")
        self.lease.unlink(missing_ok=True)
        self.keyboard_started = False

    def start_keyboard(self):
        # Only yield the known Omarchy input-method service, never kill arbitrary IMEs.
        if self.active("omarchy-tablet-keyboard.service"):
            self.keyboard_started = True
            return
        fcitx = self.active("omarchy-fcitx5.service")
        osk_enabled = run("gsettings", "get", "org.gnome.desktop.a11y.applications", "screen-keyboard-enabled").stdout.strip()
        if osk_enabled not in {"true", "false"}:
            raise RuntimeError("Cannot read the on-screen keyboard accessibility setting")
        atomic_json(self.lease, {"fcitx": fcitx, "oskEnabled": osk_enabled})
        try:
            run("gsettings", "set", "org.gnome.desktop.a11y.applications", "screen-keyboard-enabled", "true")
            if fcitx:
                run("systemctl", "--user", "stop", "omarchy-fcitx5.service")
            run("systemd-run", "--user", "--collect", "--unit=omarchy-tablet-keyboard",
                "--property=PartOf=graphical-session.target", "--", "/usr/bin/env",
                shutil.which("squeekboard"))
            self.keyboard_started = True
        except Exception:
            self.restore_keyboard()
            raise

    def visible(self):
        result = run("busctl", "--user", "get-property", "sm.puri.OSK0", "/sm/puri/OSK0",
                     "sm.puri.OSK0", "Visible", check=False)
        return result.returncode == 0 and result.stdout.strip() == "b true"

    def show_keyboard(self, visible):
        run("busctl", "--user", "call", "sm.puri.OSK0", "/sm/puri/OSK0",
            "sm.puri.OSK0", "SetVisible", "b", "true" if visible else "false")

    def state(self):
        attached = physical_keyboard_present(Path("/proc/bus/input/devices").read_text())
        return dict(self.preferences, attached=attached,
                    tablet=tablet_mode(self.preferences["mode"], attached),
                    keyboardAvailable=bool(shutil.which("squeekboard")),
                    keyboardRunning=self.keyboard_started, error=self.error,
                    dictationCommandText=shlex.join(self.preferences["dictationCommand"]),
                    dictationAvailable=bool(shutil.which(self.preferences["dictationCommand"][0])),
                    animations=self.animations,
                    wallpaper=wallpaper())

    def command(self, data):
        if not isinstance(data, dict):
            raise ValueError("Expected a command object")
        action, value = data.get("action"), data.get("value")
        if action == "mode":
            if value == "toggle":
                value = "desktop" if self.state()["tablet"] else "tablet"
            if value not in MODES:
                raise ValueError("Unknown mode")
            self.preferences["mode"] = value
            self.manual_keyboard = False
        elif action == "layout":
            if value not in {"single", "tiling"}:
                raise ValueError("Unknown layout")
            self.preferences["layout"] = value
        elif action == "dictationCommand":
            argv = shlex.split(value) if isinstance(value, str) else value
            if not valid_command(argv):
                raise ValueError("Enter a command and optional arguments")
            self.preferences["dictationCommand"] = argv
        elif action == "dictation":
            if self.dictation_process and self.dictation_process.poll() is None:
                return
            self.dictation_process = subprocess.Popen(self.preferences["dictationCommand"],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif action == "favorite":
            if not isinstance(value, str) or not value or len(value) > 256:
                raise ValueError("Invalid application ID")
            favorites = self.preferences["favorites"]
            favorites.remove(value) if value in favorites else favorites.append(value)
        elif action == "keyboard":
            if not shutil.which("squeekboard"):
                raise RuntimeError("Keyboard unavailable: install squeekboard.")
            if self.keyboard_started and self.visible():
                self.show_keyboard(False)
                if not self.state()["tablet"]:
                    self.manual_keyboard = False
                    self.restore_keyboard()
            else:
                self.manual_keyboard = True
                self.start_keyboard()
                # D-Bus registration happens just after process startup.
                for attempt in range(20):
                    try:
                        self.show_keyboard(True)
                        break
                    except RuntimeError:
                        if attempt == 19:
                            raise
                        time.sleep(0.1)
        else:
            raise ValueError("Unknown command")
        atomic_json(self.preferences_path, self.preferences)
        self.error = ""

    def reconcile(self):
        state = self.state()
        if self.last_mode is not None and state["tablet"] != self.last_mode:
            self.manual_keyboard = False
        self.last_mode = state["tablet"]
        wanted = state["keyboardAvailable"] and (state["tablet"] or self.manual_keyboard)
        if wanted and not self.keyboard_started and time.monotonic() >= self.retry_after:
            try:
                self.start_keyboard()
            except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
                self.error = str(exc)
                self.retry_after = time.monotonic() + 30
        elif not wanted and self.keyboard_started:
            self.restore_keyboard()
        if self.keyboard_started and not self.active("omarchy-tablet-keyboard.service"):
            self.restore_keyboard()
            self.error = "Keyboard stopped. Check journalctl --user -u omarchy-tablet-keyboard."
            self.retry_after = time.monotonic() + 30
        self.layout.reconcile(state["tablet"] and self.preferences["layout"] == "single")
        if time.monotonic() >= self.next_style_check:
            self.next_style_check = time.monotonic() + 5
            result = run("hyprctl", "-j", "getoption", "animations:enabled", check=False)
            if result.returncode == 0:
                self.animations = bool(json.loads(result.stdout).get("int", 1))
        if self.dictation_process and self.dictation_process.poll() is not None:
            if self.dictation_process.returncode:
                self.error = "Dictation command failed. Check your dictation application."
            self.dictation_process = None
        return self.state()

    def stop(self, *_):
        self.running = False

    def daemon(self):
        lock = (self.runtime / "backend.lock").open("w")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)
        self.layout.restore()
        self.restore_keyboard()  # recover a lease after a previous shell crash
        previous = ""
        buffer = b""
        try:
            while self.running:
                try:
                    state = json.dumps(self.reconcile(), ensure_ascii=False)
                    if state != previous:
                        print(state, flush=True)
                        previous = state
                    readable, _, _ = select.select([sys.stdin], [], [], 0.5)
                    if readable:
                        chunk = os.read(sys.stdin.fileno(), 65536)
                        if not chunk:
                            break
                        buffer += chunk
                        while b"\n" in buffer:
                            line, buffer = buffer.split(b"\n", 1)
                            try:
                                self.command(json.loads(line))
                            except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as exc:
                                self.error = str(exc)
                except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
                    self.error = str(exc)
                    print(json.dumps(self.state(), ensure_ascii=False), flush=True)
                    previous = ""
                    time.sleep(2)
        finally:
            try:
                self.layout.restore()
            finally:
                self.restore_keyboard()
                lock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["daemon", "status"])
    args = parser.parse_args()
    if args.action == "daemon":
        Backend().daemon()
    else:
        print(json.dumps(Backend().state(), ensure_ascii=False, indent=2))
