"""Release regressions: exercise installation in isolated XDG directories."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from install import install, restore


class InstallReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / "config"
        self.state = self.root / "state"
        self.config_file = self.config / "omarchy/shell.json"
        self.config_file.parent.mkdir(parents=True)
        self.original = {"version": 1, "bar": {"id": "other.bar", "position": "bottom"}}
        self.config_file.write_text(json.dumps(self.original))
        self.repo = Path(__file__).resolve().parents[1]
        self.destination = self.config / "omarchy/plugins/surface.tablet"
        self.backup = self.state / "omarchy-tablet/install-backup.json"

    def test_marketplace_checkout_is_not_overwritten(self):
        self.destination.mkdir(parents=True)
        (self.destination / ".git").mkdir()
        entry = self.destination / "install.py"
        entry.write_text("original tracked installer")
        with self.assertRaisesRegex(RuntimeError, "managed by git"):
            install(self.config, self.state, self.repo, activate=False)
        self.assertEqual(entry.read_text(), "original tracked installer")
        self.assertEqual(json.loads(self.config_file.read_text()), self.original)
        self.assertFalse(self.backup.exists())

    def test_missing_payload_does_not_create_backup_or_installation(self):
        with self.assertRaises(FileNotFoundError):
            install(self.config, self.state, self.root / "missing-source", activate=False)
        self.assertFalse(self.backup.exists())
        self.assertFalse(self.destination.exists())
        self.assertEqual(json.loads(self.config_file.read_text()), self.original)

    def test_invalid_manifest_does_not_create_backup(self):
        source = self.root / "source"
        source.mkdir()
        for path in [*self.repo.glob("*.py"), *self.repo.glob("*.qml"), self.repo / "manifest.json"]:
            shutil.copy2(path, source / path.name)
        (source / "manifest.json").write_text("not json")
        with self.assertRaises(ValueError):
            install(self.config, self.state, source, activate=False)
        self.assertFalse(self.backup.exists())
        self.assertFalse(self.destination.exists())

    def test_missing_baseline_does_not_restore_tablet_to_itself(self):
        self.original["bar"]["id"] = "surface.tablet"
        self.config_file.write_text(json.dumps(self.original))
        install(self.config, self.state, self.repo, activate=False)
        restore(self.config, self.state, activate=False)
        self.assertEqual(json.loads(self.config_file.read_text())["bar"]["id"], "omarchy.bar")

    def test_legacy_self_referencing_backup_returns_to_stock(self):
        self.original["bar"]["id"] = "surface.tablet"
        self.config_file.write_text(json.dumps(self.original))
        self.backup.parent.mkdir(parents=True)
        self.backup.write_text(json.dumps({"bar": self.original["bar"]}))
        restore(self.config, self.state, activate=False)
        self.assertEqual(json.loads(self.config_file.read_text())["bar"]["id"], "omarchy.bar")

    def test_restore_rejects_unknown_config_version(self):
        self.original["version"] = 2
        self.config_file.write_text(json.dumps(self.original))
        with self.assertRaisesRegex(RuntimeError, "Unsupported"):
            restore(self.config, self.state, activate=False)
        self.assertEqual(json.loads(self.config_file.read_text()), self.original)
