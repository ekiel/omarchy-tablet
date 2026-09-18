#!/usr/bin/env python3
"""Select a Squeekboard language independently of the English interface."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("layout", nargs="?", default="ca")
parser.add_argument("--restore", action="store_true")
args = parser.parse_args()
backup = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "omarchy-tablet/keyboard-language-backup.json"
base = ["gsettings", "org.gnome.desktop.input-sources", "sources"]
if args.restore:
    if backup.exists():
        value = json.loads(backup.read_text())["sources"]
        subprocess.run([base[0], "set", *base[1:], value], check=True)
        backup.unlink()
else:
    if not re.fullmatch(r"[a-zA-Z0-9_+:-]+", args.layout):
        parser.error("Use an XKB layout ID, for example ca")
    if not backup.exists():
        value = subprocess.check_output([base[0], "get", *base[1:]], text=True).strip()
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_text(json.dumps({"sources": value}) + "\n")
    subprocess.run([base[0], "set", *base[1:], f"[('xkb', '{args.layout}') ]"], check=True)
