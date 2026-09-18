#!/usr/bin/env python3
"""Install/update the local plugin, or restore the previous bar without resetting Omarchy."""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import hashlib
import subprocess
import time
from tablet import atomic_json

PLUGIN_ID = "surface.tablet"


def install(config_dir, state_dir, source, activate=True):
    config_file = config_dir / "omarchy/shell.json"
    config = json.loads(config_file.read_text())
    if config.get("version") != 1:
        raise RuntimeError("Unsupported Omarchy shell.json version")
    backup = state_dir / "omarchy-tablet/install-backup.json"
    if not backup.exists():
        atomic_json(backup, {"bar": copy.deepcopy(config.get("bar", {}))})
    destination = config_dir / "omarchy/plugins" / PLUGIN_ID
    destination.mkdir(parents=True, exist_ok=True)
    files = [*source.glob("*.qml"), source / "tablet.py", source / "layout.py", source / "manifest.json", source / "install.py"]
    # New URLs avoid stale QML components retained by the host during a rescan.
    revision = hashlib.sha256(b"".join(f.read_bytes() for f in sorted(files))).hexdigest()[:16]
    release = destination / "releases" / revision
    release.mkdir(parents=True, exist_ok=True)
    for file in files:
        shutil.copy2(file, release / file.name)
        if file.name != "manifest.json" and file.resolve() != (destination / file.name).resolve():
            shutil.copy2(file, destination / file.name)
    manifest = json.loads((source / "manifest.json").read_text())
    # Accept installation from a previously installed directory as well.
    manifest["entryPoints"] = {kind: f"releases/{revision}/{Path(name).name}"
                               for kind, name in manifest["entryPoints"].items()}
    atomic_json(destination / "manifest.json", manifest)
    config.setdefault("bar", {})["id"] = PLUGIN_ID
    config["bar"]["position"] = "top"
    atomic_json(config_file, config)
    if activate:
        # File watchers may already be rebuilding plugins. An IPC reply can
        # time out even though the request was delivered, so verify the new
        # service URL instead of treating that transient timeout as failure.
        subprocess.run(["omarchy-shell", "shell", "rescanPlugins"], capture_output=True, timeout=20)
        subprocess.run(["omarchy-shell", "shell", "reloadConfig"], capture_output=True, timeout=20)
        ready = 0
        for attempt in range(60):
            time.sleep(.5)
            result = subprocess.run(["omarchy-shell", "tablet", "build"], capture_output=True, text=True, timeout=10)
            ready = ready + 1 if result.returncode == 0 and f"/releases/{revision}/" in result.stdout else 0
            if ready >= 3:
                break
        else:
            raise RuntimeError("Plugin installed but service is not ready. Run omarchy restart shell or restore.")
    print(f"Installed {PLUGIN_ID}. Previous bar saved in {backup}")


def restore(config_dir, state_dir, activate=True):
    config_file = config_dir / "omarchy/shell.json"
    backup = state_dir / "omarchy-tablet/install-backup.json"
    config = json.loads(config_file.read_text())
    if config.get("bar", {}).get("id") == PLUGIN_ID:
        original = json.loads(backup.read_text())["bar"] if backup.exists() else {"id": "omarchy.bar", "position": "top"}
        for key in ("id", "position"):
            if key in original:
                config["bar"][key] = original[key]
            else:
                config["bar"].pop(key, None)
    # Preserve unrelated changes made after installation.
    atomic_json(config_file, config)
    if activate:
        subprocess.run(["omarchy-shell", "shell", "reloadConfig"], check=True)
    backup.unlink(missing_ok=True)
    print("Previous bar restored. Plugin files and tablet preferences kept for reuse.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()
    config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    state_dir = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    if args.restore:
        restore(config_dir, state_dir)
    else:
        install(config_dir, state_dir, Path(__file__).resolve().parent)
