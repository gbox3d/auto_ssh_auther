import socket
import unittest
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

from paramiko.ssh_exception import BadHostKeyException, NoValidConnectionsError, SSHException

from ssh_auther.keys import PublicKeyInfo
from ssh_auther.ssh.local_config import SSHConfigStatus, SSHConfigUpdate
from ssh_auther.ssh.verify import VerifyResult
from ssh_auther.services.register import format_connection_error, key_exists_in_content
from ssh_auther.services.register import register_key, run_key_login_verification, RegisterResult


class RegisterServiceTests(unittest.TestCase):
    def test_key_exists_ignores_comment_differences(self):
        key_line = "ssh-ed25519 AAAATESTKEY local-comment"
        content = "ssh-ed25519 AAAATESTKEY other-comment\n"
        self.assertTrue(key_exists_in_content(key_line, content))

    def test_known_hosts_error_is_explained_clearly(self):
        message = format_connection_error(SSHException("Server 'example.com' not found in known_hosts"))
        self.assertIn("known_hosts", message)
        self.assertIn("알 수 없는 호스트", message)

    def test_bad_host_key_error_is_explained_clearly(self):
        message = format_connection_error(BadHostKeyException("example.com", Mock(), Mock()))
        self.assertIn("호스트 키 검증 실패", message)

    def test_socket_timeout_maps_to_timeout_message(self):
        message = format_connection_error(socket.timeout("timed out"))
        self.assertIn("연결 시간 초과", message)

    def test_connection_refused_maps_to_connection_message(self):
        message = format_connection_error(NoValidConnectionsError({("127.0.0.1", 22): ConnectionRefusedError("refused")}))
        self.assertIn("서버에 연결할 수 없습니다", message)

    def test_register_success_includes_local_config_message(self):
        key_info = PublicKeyInfo(
            path=Path("id_ed25519_prod.pub"),
            filename="id_ed25519_prod.pub",
            key_type="ssh-ed25519",
            key_data="AAAATESTKEY",
            comment="prod",
            full_line="ssh-ed25519 AAAATESTKEY prod",
        )

        with (
            patch("ssh_auther.services.register.run_with_host_trust_fallback") as run_fallback,
            patch("ssh_auther.services.register.ensure_host_config") as ensure_config,
            patch("ssh_auther.services.register.verify_key_login") as verify,
            patch("ssh_auther.services.register.find_alias_collisions", return_value=[]),
        ):
            run_fallback.return_value = ((RegisterResult.SUCCESS, "키가 성공적으로 등록되었습니다."), None)
            ensure_config.return_value = SSHConfigUpdate(
                status=SSHConfigStatus.ADDED,
                path=Path("config"),
                host="prod",
                identity_file=Path("id_ed25519_prod"),
            )
            verify.return_value = VerifyResult(True, "키 로그인 검증 성공: 암호 없이 키로 접속됩니다.")

            status, message = register_key(key_info, "prod", 2222, "ubuntu", "password")

        self.assertEqual(status, RegisterResult.SUCCESS)
        self.assertIn("키가 성공적으로 등록되었습니다.", message)
        self.assertIn("로컬 SSH config: added", message)
        ensure_config.assert_called_once_with(
            host="prod",
            port=2222,
            username="ubuntu",
            identity_file=Path("id_ed25519_prod"),
        )
        self.assertIn("키 로그인 검증 성공", message)

    def test_run_key_login_verification_uses_private_key_and_delegates(self):
        key_info = PublicKeyInfo(
            path=Path("/home/u/.ssh/id_ed25519_prod.pub"),
            filename="id_ed25519_prod.pub",
            key_type="ssh-ed25519",
            key_data="AAAA",
            comment="",
            full_line="ssh-ed25519 AAAA",
        )

        with patch("ssh_auther.services.register.verify_key_login") as verify:
            verify.return_value = VerifyResult(True, "ok-msg")
            ok, message = run_key_login_verification(key_info, "h", 22, "u")

        self.assertTrue(ok)
        self.assertEqual(message, "ok-msg")
        verify.assert_called_once_with("h", 22, "u", Path("/home/u/.ssh/id_ed25519_prod"))


if __name__ == "__main__":
    unittest.main()
