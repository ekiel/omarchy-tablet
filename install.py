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
import tempfile
from tablet import atomic_json

PLUGIN_ID = "surface.tablet"


def install(config_dir, state_dir, source, activate=True):
    config_file = config_dir / "omarchy/shell.json"
    config = json.loads(config_file.read_text())
    if config.get("version") != 1:
        raise RuntimeError("Unsupported Omarchy shell.json version")
    destination = config_dir / "omarchy/plugins" / PLUGIN_ID
    if (destination / ".git").exists():
        raise RuntimeError("This plugin is managed by git. Use omarchy plugin update surface.tablet; "
                           "do not run the development installer over a marketplace checkout.")
    files = [*source.glob("*.qml"), source / "tablet.py", source / "layout.py", source / "keyboard_theme.py", source / "keyboard_watch.py", source / "manifest.json", source / "install.py"]
    # Validate the complete payload before changing configuration or backups.
    revision = hashlib.sha256(b"".join(f.read_bytes() for f in sorted(files))).hexdigest()[:16]
    manifest = json.loads((source / "manifest.json").read_text())
    backup = state_dir / "omarchy-tablet/install-backup.json"
    if not backup.exists():
        original = copy.deepcopy(config.get("bar", {}))
        if original.get("id") == PLUGIN_ID:
            original = {"id": "omarchy.bar", "position": "top"}
        atomic_json(backup, {"bar": original})
    destination.mkdir(parents=True, exist_ok=True)
    # New URLs avoid stale QML components retained by the host during a rescan.
    release = destination / "releases" / revision
    if not release.exists():
        # Prepare outside the watched plugin tree. Publishing a complete release
        # prevents repeated hot reloads against partially copied QML / Python.
        release.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="tablet-stage-", dir=config_dir) as stage:
            staged = Path(stage) / revision
            staged.mkdir()
            for file in files:
                shutil.copy2(file, staged / file.name)
            staged.rename(release)
    # Accept installation from a previously installed directory as well.
    manifest["entryPoints"] = {kind: f"releases/{revision}/{Path(name).name}"
                               for kind, name in manifest["entryPoints"].items()}
    # Stable entry point for restoring from the installed directory. The code
    # itself always comes from the currently published immutable release.
    wrapper = """#!/usr/bin/env python3
import json
from pathlib import Path
import runpy
base = Path(__file__).resolve().parent
manifest = json.loads((base / 'manifest.json').read_text())
script = base / Path(manifest['entryPoints']['bar']).parent / 'install.py'
import sys
sys.path.insert(0, str(script.parent))
runpy.run_path(str(script), run_name='__main__')
"""
    entry = destination / "install.py"
    if not entry.exists() or entry.read_text() != wrapper:
        entry.write_text(wrapper)
    atomic_json(destination / "manifest.json", manifest)
    config.setdefault("bar", {})["id"] = PLUGIN_ID
    config["bar"]["position"] = "top"
    if json.loads(config_file.read_text()) != config:
        atomic_json(config_file, config)
    if activate:
        # Let the file watcher finish first. Immediate rescan + config reload
        # used to rebuild every plugin several times in the same installation.
        ready = 0
        for attempt in range(60):
            time.sleep(.5)
            try:
                result = subprocess.run(["omarchy-shell", "tablet", "build"], capture_output=True, text=True, timeout=3)
                ready = ready + 1 if result.returncode == 0 and f"/releases/{revision}/" in result.stdout else 0
            except subprocess.TimeoutExpired:
                ready = 0
            if ready >= 3:
                break
            if attempt == 15:
                try:
                    subprocess.run(["omarchy-shell", "shell", "rescanPlugins"], capture_output=True, timeout=3)
                except subprocess.TimeoutExpired:
                    pass  # IPC may time out after delivering the request.
        else:
            raise RuntimeError("Plugin installed but service is not ready. Run omarchy restart shell or restore.")
    print(f"Installed {PLUGIN_ID}. Previous bar saved in {backup}")


def restore(config_dir, state_dir, activate=True):
    config_file = config_dir / "omarchy/shell.json"
    backup = state_dir / "omarchy-tablet/install-backup.json"
    config = json.loads(config_file.read_text())
    if config.get("version") != 1:
        raise RuntimeError("Unsupported Omarchy shell.json version")
    if config.get("bar", {}).get("id") == PLUGIN_ID:
        original = json.loads(backup.read_text())["bar"] if backup.exists() else {"id": "omarchy.bar", "position": "top"}
        if original.get("id") == PLUGIN_ID:
            original = {"id": "omarchy.bar", "position": "top"}
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
