import socket
import unittest
from unittest.mock import Mock

from paramiko.ssh_exception import BadHostKeyException, NoValidConnectionsError, SSHException

from auto_ssh_auther.services.register import format_connection_error, key_exists_in_content


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


if __name__ == "__main__":
    unittest.main()
