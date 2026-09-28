#!/usr/bin/env python3
"""Lint QML using Omarchy's runtime qs imports, without modifying the shell."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shell-dir', type=Path,
                        default=Path(os.environ.get('OMARCHY_PATH', '/usr/share/omarchy')) / 'shell')
    args = parser.parse_args()
    executable = shutil.which('qmllint') or '/usr/lib/qt6/bin/qmllint'
    if not Path(executable).is_file():
        parser.error('qmllint is required (Qt declarative development tools)')
    for name in ('Commons', 'Ui'):
        if not (args.shell_dir / name / 'qmldir').is_file():
            parser.error(f'Missing Omarchy module: {args.shell_dir / name}')
    # Quickshell creates the qs namespace at runtime; qmllint needs the same
    # directory mapping. Temporary links stay outside the distributable plugin.
    with tempfile.TemporaryDirectory(prefix='omarchy-tablet-lint-') as folder:
        namespace = Path(folder) / 'qs'
        namespace.mkdir()
        for name in ('Commons', 'Ui'):
            (namespace / name).symlink_to((args.shell_dir / name).resolve(), target_is_directory=True)
        root = Path(__file__).resolve().parents[1]
        return subprocess.run([executable, '-I', folder, *map(str, sorted(root.glob('*.qml')))]).returncode


if __name__ == '__main__':
    raise SystemExit(main())
