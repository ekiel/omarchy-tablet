#!/usr/bin/env python3
"""Live Surface validation; restores mode, orientation and autorotation in finally.

Uses a disposable terminal to check window management; never closes user apps.
--pointer optionally accepts a local Wayland pointer helper for real click/drag tests.
No microphone recording or text injection into user applications is performed.
"""
import argparse
import json
from pathlib import Path
import statistics
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
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            if test():
                print(f"PASS {label}", flush=True)
                return
        except RuntimeError:
            pass  # Service / D-Bus registration can lag process startup.
        time.sleep(.1)
    raise AssertionError(label)


def clients():
    return json.loads(run("hyprctl", "-j", "clients"))


def layers():
    return [layer for screen in json.loads(run("hyprctl", "-j", "layers")).values()
            for level in screen["levels"].values() for layer in level
            if layer["namespace"].startswith("omarchy-tablet-")]


def capture(name):
    time.sleep(.65)
    run("grim", str(OUT / f"{name}.png"))
    print(f"CAPTURE {name}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pointer", help="Optional Wayland pointer helper executable")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    original = state()
    monitor = next(m for m in json.loads(run("hyprctl", "-j", "monitors"))
                   if m["name"].startswith(("eDP", "DSI", "LVDS")))
    report = {"passed": [], "rotation_dispatch_ms": [], "limits": [
        "No physical accelerometer, touch/stylus accuracy or keyboard detach tested",
        "No microphone transcription tested", "Dispatch timing is not frame timing"]}
    autorotate = subprocess.run(["systemctl", "--user", "is-active", "--quiet", "surface-autorotate.service"]).returncode == 0
    terminal = None

    def passed(label):
        report["passed"].append(label)
        print("PASS " + label, flush=True)

    def rotate(transform):
        start = time.monotonic()
        run("hyprctl", "eval", 'hl.monitor({output=' + json.dumps(monitor["name"]) + ', transform=' + str(transform) + '})')
        report["rotation_dispatch_ms"].append(round((time.monotonic() - start) * 1000, 1))
        time.sleep(.5)
        current = next(m for m in json.loads(run("hyprctl", "-j", "monitors")) if m["name"] == monitor["name"])
        assert current["transform"] == transform

    def osk_visible():
        return run("busctl", "--user", "get-property", "sm.puri.OSK0", "/sm/puri/OSK0", "sm.puri.OSK0", "Visible") == "b true"

    def hide_keyboard():
        # systemd-run returns before Squeekboard registers its D-Bus name.
        for attempt in range(30):
            try:
                run("busctl", "--user", "call", "sm.puri.OSK0", "/sm/puri/OSK0", "sm.puri.OSK0", "SetVisible", "b", "false")
                return
            except RuntimeError:
                if attempt == 29:
                    raise
                time.sleep(.1)

    def view():
        return json.loads(ipc("tablet", "view"))

    def click(x, y, *extra):
        run(args.pointer, str(x), str(y), "1368", "912", *(str(v) for v in extra))
        time.sleep(.2)

    try:
        if autorotate:
            run("systemctl", "--user", "stop", "surface-autorotate.service")
        ipc("tablet", "close")
        ipc("tablet", "mode", "tablet")
        wait_for(lambda: state()["tablet"] and state()["keyboardRunning"], "tablet + keyboard service")
        assert not state()["error"], state()
        rotate(0)
        hide_keyboard()
        ipc("tablet", "close")
        assert {l["namespace"] for l in layers()} == {"omarchy-tablet-bar", "omarchy-tablet-gesture"}
        passed("Only two tablet layers while apps are in use")
        terminal = subprocess.Popen(["foot", "--app-id=tablet-validation", "--title=Tablet validation", "sleep", "180"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_for(lambda: any(c["class"] == "tablet-validation" and c["fullscreen"] == 1 for c in clients()), "new test window maximized")
        ipc("tablet", "mode", "desktop")
        wait_for(lambda: not state()["tablet"] and not state()["keyboardRunning"], "desktop releases keyboard")
        wait_for(lambda: any(c["class"] == "tablet-validation" and c["fullscreen"] == 0 for c in clients()), "desktop restores test window")
        passed("Single-app maximize and desktop restoration")
        assert len(layers()) == 1
        ipc("tablet", "mode", "tablet")
        wait_for(lambda: state()["keyboardRunning"], "tablet keyboard restarted")
        hide_keyboard()
        ipc("tablet", "keyboard")
        wait_for(osk_visible, "manual keyboard visible")
        ipc("tablet", "keyboard")
        wait_for(lambda: not osk_visible(), "manual keyboard hidden")
        passed("Keyboard show/hide via backend and D-Bus")
        for mode in ("desktop", "tablet", "desktop", "tablet"):
            ipc("tablet", "mode", mode)
            wait_for(lambda: state()["tablet"] == (mode == "tablet"), "mode " + mode)
            geometry = json.loads(ipc("tablet-bar", "geometry"))
            for host in geometry:
                ids = [s["id"] for s in host["slots"]]
                assert len(ids) == len(set(ids)) == 14, ids
                assert all(s["loaded"] for s in host["slots"])
        passed("Repeated mode changes retain 14 unique loaded widgets")
        for plugin in ("audio", "bluetooth", "network", "power", "clock", "monitor", "agents"):
            assert ipc("shell", "summon", "omarchy." + plugin, "{}") == "ok", plugin
            time.sleep(.2)
            ipc("shell", "hide", "omarchy." + plugin)
        passed("Seven native popups open/close")
        if args.pointer:
            assert monitor["width"] / monitor["scale"] == 1368, "Pointer coordinates require this Surface at scale 2"
            ipc("tablet", "close")
            hide_keyboard()
            click(40, 38)
            wait_for(lambda: not state()["tablet"], "real desktop toggle click")
            click(20, 23)
            wait_for(lambda: state()["tablet"], "real tablet toggle click")
            click(111, 38)
            assert view()["home"]
            click(183, 38)
            assert view()["switcher"] and not view()["home"]
            click(1255, 38)
            assert view()["home"] and view()["page"] == "settings" and not view()["switcher"]
            passed("Real Wayland clicks: mode, apps, windows, settings")
            ipc("tablet", "close")
            hide_keyboard()
            time.sleep(.5)
            grip = next(l for l in layers() if l["namespace"] == "omarchy-tablet-gesture")
            click(grip["x"] + grip["w"] // 2, grip["y"] + grip["h"] // 2)
            assert view()["home"]
            ipc("tablet", "close")
            time.sleep(.6)
            # The grip follows the OSK's exclusive zone. Measure its real
            # position instead of clicking an obsolete screen coordinate.
            grip = next(l for l in layers() if l["namespace"] == "omarchy-tablet-gesture")
            gx, gy = grip["x"] + grip["w"] // 2, grip["y"] + grip["h"] // 2
            click(gx, gy, gx, gy - 110)
            assert view()["switcher"]
            passed("Real pointer gesture: bottom tap and upward drag")
            # The disposable terminal is still active. Closing via nav is safe
            # only after confirming its actual focus.
            ipc("tablet", "close")
            active = json.loads(run("hyprctl", "-j", "activewindow"))
            if active.get("class") == "tablet-validation":
                click(1325, 38)
                wait_for(lambda: not any(c["class"] == "tablet-validation" for c in clients()), "close button closes test window")
                passed("Close button on disposable application")
        for transform, name in ((0, "06-landscape-home"), (1, "07-portrait-home"), (3, "08-portrait-inverted"), (0, "09-landscape-final")):
            rotate(transform)
            ipc("tablet", "home")
            hide_keyboard()
            capture(name)
            assert len(layers()) == 3
            assert not state()["error"], state()
        passed("Landscape and both portrait orientations; three layers with Home open")
        ipc("tablet", "switcher")
        hide_keyboard()
        capture("10-windows-final")
        assert view()["switcher"]
        ipc("tablet", "settings")
        hide_keyboard()
        capture("11-settings-final")
        assert view()["page"] == "settings" and not view()["switcher"]
        passed("Switcher and settings share one exclusive overlay")
        ipc("tablet", "mode", "auto")
        wait_for(lambda: state()["tablet"] == (not state()["attached"]), "automatic mode follows keyboard topology")
        passed("Auto mode follows detected physical keyboard")
    finally:
        if terminal and terminal.poll() is None:
            terminal.terminate()
            terminal.wait(timeout=5)
        try:
            rotate(monitor["transform"])
        finally:
            if autorotate:
                run("systemctl", "--user", "start", "surface-autorotate.service")
            ipc("tablet", "close")
            ipc("tablet", "mode", original["mode"])
            if report["rotation_dispatch_ms"]:
                report["median_rotation_dispatch_ms"] = statistics.median(report["rotation_dispatch_ms"])
            (ROOT / "docs/live-results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
