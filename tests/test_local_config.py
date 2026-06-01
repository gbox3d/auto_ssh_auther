import tempfile
import unittest
from pathlib import Path

from ssh_auther.ssh.local_config import (
    SSHConfigStatus,
    ensure_host_config,
    find_alias_collisions,
)


class LocalSSHConfigTests(unittest.TestCase):
    def test_adds_new_host_block(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home_dir = Path(temp_dir)
            config_path = home_dir / ".ssh" / "config"
            identity_file = home_dir / ".ssh" / "id_ed25519_prod"

            update = ensure_host_config(
                host="prod",
                port=2222,
                username="ubuntu",
                identity_file=identity_file,
                config_path=config_path,
                home_dir=home_dir,
            )

            self.assertEqual(update.status, SSHConfigStatus.ADDED)
            content = config_path.read_text(encoding="utf-8")
            self.assertIn("Host prod", content)
            self.assertIn("  HostName prod", content)
            self.assertIn("  Port 2222", content)
            self.assertIn("  User ubuntu", content)
            self.assertIn("  IdentityFile ~/.ssh/id_ed25519_prod", content)
            self.assertIn("  IdentitiesOnly yes", content)
            self.assertIn("  PreferredAuthentications publickey", content)

    def test_updates_existing_host_block(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home_dir = Path(temp_dir)
            config_path = home_dir / ".ssh" / "config"
            config_path.parent.mkdir()
            config_path.write_text(
                "\n".join(
                    [
                        "Host prod",
                        "  HostName old.example.com",
                        "  Port 22",
                        "  User root",
                        "  IdentityFile ~/.ssh/old_key",
                        "  IdentitiesOnly no",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            identity_file = home_dir / ".ssh" / "id_ed25519_prod"

            update = ensure_host_config(
                host="prod",
                port=2222,
                username="ubuntu",
                identity_file=identity_file,
                config_path=config_path,
                home_dir=home_dir,
            )

            self.assertEqual(update.status, SSHConfigStatus.UPDATED)
            content = config_path.read_text(encoding="utf-8")
            self.assertIn("  HostName prod", content)
            self.assertIn("  Port 2222", content)
            self.assertIn("  User ubuntu", content)
            self.assertIn("  IdentityFile ~/.ssh/id_ed25519_prod", content)
            self.assertIn("  IdentitiesOnly yes", content)
            self.assertIn("  PreferredAuthentications publickey", content)
            self.assertNotIn("old.example.com", content)
            self.assertNotIn("~/.ssh/old_key", content)

    def test_leaves_matching_host_block_unchanged(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home_dir = Path(temp_dir)
            config_path = home_dir / ".ssh" / "config"
            identity_file = home_dir / ".ssh" / "id_ed25519_prod"

            first = ensure_host_config(
                host="prod",
                port=2222,
                username="ubuntu",
                identity_file=identity_file,
                config_path=config_path,
                home_dir=home_dir,
            )
            before = config_path.read_text(encoding="utf-8")
            second = ensure_host_config(
                host="prod",
                port=2222,
                username="ubuntu",
                identity_file=identity_file,
                config_path=config_path,
                home_dir=home_dir,
            )
            after = config_path.read_text(encoding="utf-8")

            self.assertEqual(first.status, SSHConfigStatus.ADDED)
            self.assertEqual(second.status, SSHConfigStatus.UNCHANGED)
            self.assertEqual(after, before)

    def test_inserts_new_host_before_wildcard_host_block(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home_dir = Path(temp_dir)
            config_path = home_dir / ".ssh" / "config"
            config_path.parent.mkdir()
            config_path.write_text(
                "\n".join(
                    [
                        "# user config",
                        "Host *",
                        "  IdentityFile ~/.ssh/default_key",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            identity_file = home_dir / ".ssh" / "id_ed25519_prod"

            update = ensure_host_config(
                host="prod",
                port=2222,
                username="ubuntu",
                identity_file=identity_file,
                config_path=config_path,
                home_dir=home_dir,
            )

            content = config_path.read_text(encoding="utf-8")
            self.assertEqual(update.status, SSHConfigStatus.ADDED)
            self.assertLess(content.index("Host prod"), content.index("Host *"))


class FindAliasCollisionsTests(unittest.TestCase):
    def _write(self, home_dir: Path, body: str) -> Path:
        config_path = home_dir / ".ssh" / "config"
        config_path.parent.mkdir()
        config_path.write_text(body, encoding="utf-8")
        return config_path

    def test_detects_alias_pointing_to_same_host_without_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home_dir = Path(temp_dir)
            config_path = self._write(
                home_dir,
                "\n".join(
                    [
                        "Host 192.168.0.220",
                        "  HostName 192.168.0.220",
                        "  User u",
                        "  IdentityFile ~/.ssh/key",
                        "",
                        "Host gb-dgx-01",
                        "  HostName 192.168.0.220",
                        "  Port 22",
                        "  User u",
                    ]
                )
                + "\n",
            )

            collisions = find_alias_collisions(
                "192.168.0.220", config_path=config_path, home_dir=home_dir
            )

            self.assertEqual(collisions, ["gb-dgx-01"])

    def test_ignores_block_that_already_has_identity_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home_dir = Path(temp_dir)
            config_path = self._write(
                home_dir,
                "\n".join(
                    [
                        "Host gb-dgx-01",
                        "  HostName 192.168.0.220",
                        "  IdentityFile ~/.ssh/key",
                    ]
                )
                + "\n",
            )

            collisions = find_alias_collisions(
                "192.168.0.220", config_path=config_path, home_dir=home_dir
            )

            self.assertEqual(collisions, [])

    def test_ignores_blocks_for_other_hosts_and_wildcard(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home_dir = Path(temp_dir)
            config_path = self._write(
                home_dir,
                "\n".join(
                    [
                        "Host other",
                        "  HostName 10.0.0.1",
                        "Host *",
                        "  IdentitiesOnly yes",
                    ]
                )
                + "\n",
            )

            collisions = find_alias_collisions(
                "192.168.0.220", config_path=config_path, home_dir=home_dir
            )

            self.assertEqual(collisions, [])

    def test_returns_empty_when_config_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home_dir = Path(temp_dir)
            config_path = home_dir / ".ssh" / "config"

            collisions = find_alias_collisions(
                "192.168.0.220", config_path=config_path, home_dir=home_dir
            )

            self.assertEqual(collisions, [])


if __name__ == "__main__":
    unittest.main()
