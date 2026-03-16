"""paramiko를 이용한 SSH 접속 및 원격 파일 조작."""

from pathlib import Path

import paramiko


def build_authorized_keys_payload(existing_content: str, key_line: str) -> str:
    """authorized_keys에 안전하게 append할 payload를 만든다."""
    normalized_key = key_line.strip()
    if not normalized_key:
        raise ValueError("추가할 공개키가 비어 있습니다.")

    prefix = "\n" if existing_content and not existing_content.endswith("\n") else ""
    return f"{prefix}{normalized_key}\n"


class SSHConnection:
    """원격 서버에 비밀번호 기반 SSH 접속을 관리한다."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        timeout: float = 10.0,
        trust_unknown_host: bool = False,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.trust_unknown_host = trust_unknown_host
        self._client: paramiko.SSHClient | None = None

    def _known_hosts_path(self) -> Path:
        return Path.home() / ".ssh" / "known_hosts"

    def _prepare_known_hosts(self) -> Path:
        known_hosts_path = self._known_hosts_path()
        ssh_dir = known_hosts_path.parent
        ssh_dir.mkdir(mode=0o700, exist_ok=True)

        if not known_hosts_path.exists():
            known_hosts_path.touch(mode=0o600)

        return known_hosts_path

    def connect(self) -> None:
        """SSH 접속을 수행한다."""
        client = paramiko.SSHClient()
        known_hosts_path = self._prepare_known_hosts()
        client.load_system_host_keys()
        client.load_host_keys(str(known_hosts_path))
        if self.trust_unknown_host:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        client.connect(
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=self.timeout,
            allow_agent=False,
            look_for_keys=False,
        )
        if self.trust_unknown_host:
            client.save_host_keys(str(known_hosts_path))
        self._client = client

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    def _exec(self, command: str) -> str:
        """명령을 실행하고 stdout을 반환한다."""
        if not self._client:
            raise RuntimeError("SSH 연결이 되어 있지 않습니다.")
        _, stdout, stderr = self._client.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        if exit_code != 0:
            err = stderr.read().decode().strip()
            raise RuntimeError(f"원격 명령 실패 (exit {exit_code}): {err}")
        return stdout.read().decode()

    def test_connection(self) -> str:
        """접속 테스트. 원격 호스트명을 반환한다."""
        return self._exec("hostname").strip()

    def ensure_ssh_dir(self) -> None:
        """원격 ~/.ssh 디렉터리가 없으면 생성한다."""
        self._exec("mkdir -p ~/.ssh && chmod 700 ~/.ssh")

    def read_authorized_keys(self) -> str:
        """원격 authorized_keys 내용을 반환한다. 파일이 없으면 빈 문자열."""
        if not self._client:
            raise RuntimeError("SSH 연결이 되어 있지 않습니다.")
        _, stdout, _ = self._client.exec_command("cat ~/.ssh/authorized_keys 2>/dev/null || true")
        stdout.channel.recv_exit_status()
        return stdout.read().decode()

    def append_authorized_key(self, key_line: str, existing_content: str = "") -> None:
        """authorized_keys에 키를 추가한다."""
        if not self._client:
            raise RuntimeError("SSH 연결이 되어 있지 않습니다.")

        payload = build_authorized_keys_payload(existing_content, key_line)
        command = "touch ~/.ssh/authorized_keys && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
        stdin, stdout, stderr = self._client.exec_command(command)
        stdin.write(payload)
        stdin.flush()
        stdin.channel.shutdown_write()
        exit_code = stdout.channel.recv_exit_status()
        if exit_code != 0:
            err = stderr.read().decode().strip()
            raise RuntimeError(f"키 추가 실패: {err}")
