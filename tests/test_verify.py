import os
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from ssh_auther.ssh.verify import VerifyResult, build_verify_command, verify_key_login


class BuildVerifyCommandTests(unittest.TestCase):
    def test_builds_key_only_batch_command(self):
        command = build_verify_command(
            host="192.168.0.220",
            port=22,
            username="gblab-dgx-01",
            identity_file=Path("/home/u/.ssh/id_ed25519_admin"),
        )

        self.assertEqual(command[0], "ssh")
        self.assertIn("BatchMode=yes", command)
        self.assertIn("PreferredAuthentications=publickey", command)
        self.assertIn("IdentitiesOnly=yes", command)
        # 사용자 ssh config를 무시해 -i로 지정한 키만 격리 검증 (config IdentityFile 거짓 양성 방지)
        f = command.index("-F")
        self.assertEqual(command[f + 1], os.devnull)
        self.assertEqual(command[-2:], ["gblab-dgx-01@192.168.0.220", "true"])
        i = command.index("-i")
        self.assertEqual(command[i + 1], str(Path("/home/u/.ssh/id_ed25519_admin")))
        p = command.index("-p")
        self.assertEqual(command[p + 1], "22")


class VerifyKeyLoginTests(unittest.TestCase):
    def _identity(self) -> Path:
        return Path("/home/u/.ssh/id_ed25519_admin")

    def test_skips_when_ssh_client_missing(self):
        with mock.patch("ssh_auther.ssh.verify.shutil.which", return_value=None):
            result = verify_key_login("h", 22, "u", self._identity())

        self.assertFalse(result.ok)
        self.assertIn("건너뜀", result.message)

    def test_reports_success_on_zero_exit(self):
        completed = SimpleNamespace(returncode=0, stdout="", stderr="")
        with mock.patch("ssh_auther.ssh.verify.shutil.which", return_value="ssh"), mock.patch(
            "ssh_auther.ssh.verify.subprocess.run", return_value=completed
        ):
            result = verify_key_login("h", 22, "u", self._identity())

        self.assertTrue(result.ok)
        self.assertIn("성공", result.message)

    def test_reports_failure_reason_from_stderr(self):
        completed = SimpleNamespace(
            returncode=255,
            stdout="",
            stderr="some noise\nPermission denied (publickey).",
        )
        with mock.patch("ssh_auther.ssh.verify.shutil.which", return_value="ssh"), mock.patch(
            "ssh_auther.ssh.verify.subprocess.run", return_value=completed
        ):
            result = verify_key_login("h", 22, "u", self._identity())

        self.assertFalse(result.ok)
        self.assertIn("Permission denied (publickey).", result.message)
        self.assertEqual(result.reason, "auth_failed")

    def test_classifies_connection_failure_as_unreachable(self):
        completed = SimpleNamespace(
            returncode=255,
            stdout="",
            stderr="ssh: connect to host h port 22: Connection timed out",
        )
        with mock.patch("ssh_auther.ssh.verify.shutil.which", return_value="ssh"), mock.patch(
            "ssh_auther.ssh.verify.subprocess.run", return_value=completed
        ):
            result = verify_key_login("h", 22, "u", self._identity())

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "unreachable")

    def test_missing_client_reason(self):
        with mock.patch("ssh_auther.ssh.verify.shutil.which", return_value=None):
            result = verify_key_login("h", 22, "u", self._identity())
        self.assertEqual(result.reason, "no_client")

    def test_reports_timeout(self):
        with mock.patch("ssh_auther.ssh.verify.shutil.which", return_value="ssh"), mock.patch(
            "ssh_auther.ssh.verify.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=8),
        ):
            result = verify_key_login("h", 22, "u", self._identity())

        self.assertFalse(result.ok)
        self.assertIn("시간 초과", result.message)


if __name__ == "__main__":
    unittest.main()
