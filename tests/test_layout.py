import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from layout import SingleApp, eligible


def client(address="0xab", **changes):
    return dict(dict(address=address, stableId=address, pid=1, initialClass="test", mapped=True,
                     hidden=False, floating=False, pinned=False, monitor=0, workspace={"id": 1},
                     fullscreen=0, fullscreenClient=0, grouped=[]), **changes)


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "lease.json"
        self.layout = SingleApp(self.path)
        self.active = client()
        self.clients = [self.active]
        self.calls = []
        self.patch = patch("layout.run", side_effect=self.run_command)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def run_command(self, *args):
        self.calls.append(args)
        values = {"monitors": [{"id": 0, "name": "eDP-1"}], "clients": self.clients, "activewindow": self.active}
        if args[1] == "-j":
            return SimpleNamespace(stdout=json.dumps(values[args[2]]))
        return SimpleNamespace(stdout="ok")

    def test_single_app_and_restore_preserves_client_state(self):
        self.active["fullscreenClient"] = 1
        self.layout.reconcile(True)
        self.assertIn("internal=1, client=1", self.calls[-1][-1])
        self.assertTrue(self.path.exists())
        self.layout.reconcile(False)
        self.assertIn("internal=0, client=1", self.calls[-1][-1])
        self.assertFalse(self.layout.windows)

    def test_dialog_external_pinned_special_and_group_not_modified(self):
        for updates in ({"floating": True}, {"monitor": 1}, {"pinned": True},
                        {"workspace": {"id": -2}}, {"grouped": ["0xaa"]}, {"fullscreen": 2}):
            self.active = client(**updates)
            self.clients = [self.active]
            self.layout.reconcile(True)
        self.assertFalse(any(c[1] == "eval" for c in self.calls))

    def test_recover_reload_and_ignore_reused_address(self):
        self.layout.reconcile(True)
        self.layout = SingleApp(self.path)
        self.layout.restore(self.clients)
        self.assertIn("internal=0", self.calls[-1][-1])
        self.layout.reconcile(True)
        self.active["stableId"] = "replacement"
        before = len(self.calls)
        self.layout.restore(self.clients)
        self.assertEqual(before, len(self.calls))
        self.assertFalse(self.layout.windows)

    def test_window_moved_to_external_is_restored(self):
        self.layout.reconcile(True)
        self.active["monitor"] = 1
        self.layout.reconcile(True)
        self.assertFalse(self.layout.windows)
        self.assertTrue(any("internal=0" in str(c) for c in self.calls))

    def test_failed_dispatch_keeps_write_ahead_journal(self):
        with patch.object(self.layout, "set_state", side_effect=RuntimeError("failed")):
            with self.assertRaises(RuntimeError):
                self.layout.reconcile(True)
        self.assertIn("0xab", json.loads(self.path.read_text())["windows"])

    def test_restore_original_maximized_after_normal_states(self):
        self.clients.append(client("0xcd", fullscreen=1))
        self.layout.reconcile(True)
        self.layout.restore(self.clients)
        self.assertIn('address:0xcd', self.calls[-1][-1])
        self.assertIn('internal=1', self.calls[-1][-1])

    def test_preexisting_fullscreen_sibling_is_not_managed_when_focused(self):
        sibling = client("0xcd", fullscreen=2)
        self.clients.append(sibling)
        self.layout.reconcile(True)
        self.active = sibling
        before = len([c for c in self.calls if c[1] == "eval"])
        self.layout.reconcile(True)
        self.assertEqual(before, len([c for c in self.calls if c[1] == "eval"]))

    def test_wrong_session_never_replays_addresses(self):
        self.layout.reconcile(True)
        with patch.dict("os.environ", {"HYPRLAND_INSTANCE_SIGNATURE": "new-session"}):
            other = SingleApp(self.path)
        self.assertFalse(other.windows)

    def test_dispatch_address_validation(self):
        with self.assertRaises(ValueError):
            self.layout.set_state('bad"address', 0, 0)


if __name__ == "__main__":
    unittest.main()
