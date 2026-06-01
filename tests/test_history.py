import tempfile
import unittest
from pathlib import Path

from ssh_auther.history import (
    ConnectionProfile,
    add_profile,
    load_history,
    save_history,
)


class HistoryTests(unittest.TestCase):
    def test_load_missing_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(load_history(Path(d) / "nope.json"), [])

    def test_save_then_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sub" / "history.json"
            profiles = [
                ConnectionProfile("192.168.0.220", 22, "gblab-dgx-01"),
                ConnectionProfile("example.com", 2222, "ubuntu"),
            ]
            save_history(path, profiles)
            self.assertEqual(load_history(path), profiles)

    def test_save_does_not_store_password_keys(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "history.json"
            save_history(path, [ConnectionProfile("h", 22, "u")])
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("password", text)

    def test_add_profile_moves_to_front_and_dedupes_by_host(self):
        profiles = [
            ConnectionProfile("a", 22, "ua"),
            ConnectionProfile("b", 22, "ub"),
        ]
        updated = add_profile(profiles, "b", 2200, "ub2")
        self.assertEqual(updated[0], ConnectionProfile("b", 2200, "ub2"))
        self.assertEqual([p.host for p in updated], ["b", "a"])

    def test_add_profile_caps_length(self):
        profiles = [ConnectionProfile(f"h{i}", 22, "u") for i in range(30)]
        updated = add_profile(profiles, "new", 22, "u", max_profiles=30)
        self.assertEqual(len(updated), 30)
        self.assertEqual(updated[0].host, "new")
        self.assertNotIn("h29", [p.host for p in updated])

    def test_add_profile_ignores_blank(self):
        self.assertEqual(add_profile([], "", 22, "u"), [])
        self.assertEqual(add_profile([], "h", 22, ""), [])


if __name__ == "__main__":
    unittest.main()
