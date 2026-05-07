"""공개키 등록 흐름을 제어한다."""

import socket
from enum import Enum

import paramiko
from paramiko.ssh_exception import BadHostKeyException, NoValidConnectionsError, SSHException

from ssh_auther.keys import PublicKeyInfo
from ssh_auther.ssh import SSHConnection
from ssh_auther.ssh.local_config import ensure_host_config, private_key_path_from_public_key


class RegisterResult(Enum):
    SUCCESS = "success"
    ALREADY_EXISTS = "already_exists"
    FAILED = "failed"


UNKNOWN_HOST_WARNING = "주의: 미등록 호스트를 감지해 known_hosts에 자동 등록한 뒤 계속 진행했습니다."


def is_unknown_host_error(exc: Exception) -> bool:
    return isinstance(exc, SSHException) and "not found in known_hosts" in str(exc)


def format_connection_error(exc: Exception) -> str:
    """연결/등록 관련 예외를 사용자 메시지로 변환한다."""
    if isinstance(exc, paramiko.AuthenticationException):
        return "인증 실패: 계정 또는 비밀번호를 확인하세요."

    if isinstance(exc, BadHostKeyException):
        return "호스트 키 검증 실패: 서버의 호스트 키가 known_hosts 정보와 일치하지 않습니다."

    if isinstance(exc, NoValidConnectionsError):
        return "서버에 연결할 수 없습니다: 서버 주소, 포트, 방화벽 상태를 확인하세요."

    if isinstance(exc, socket.timeout):
        return "연결 시간 초과: 서버 주소와 포트를 확인하세요."

    if isinstance(exc, socket.gaierror):
        return "호스트 이름 해석 실패: 서버 주소를 다시 확인하세요."

    if isinstance(exc, SSHException):
        if is_unknown_host_error(exc):
            return "알 수 없는 호스트입니다: known_hosts 자동 등록 중 문제가 발생했습니다."
        return f"SSH 오류: {exc}"

    if isinstance(exc, OSError):
        return f"네트워크 오류: {exc}"

    if isinstance(exc, RuntimeError):
        return str(exc)

    return f"예상하지 못한 오류: {exc}"


def run_with_host_trust_fallback(host: str, port: int, username: str, password: str, operation):
    """엄격 검증으로 먼저 시도하고, 미등록 호스트면 1회 자동 등록 후 재시도한다."""
    try:
        with SSHConnection(host, port, username, password) as conn:
            return operation(conn), None
    except Exception as exc:
        if not is_unknown_host_error(exc):
            raise

    with SSHConnection(host, port, username, password, trust_unknown_host=True) as conn:
        return operation(conn), UNKNOWN_HOST_WARNING


def key_exists_in_content(key_line: str, content: str) -> bool:
    """authorized_keys 내용에 동일한 키가 이미 있는지 확인한다.

    키 타입과 base64 데이터만 비교하여 코멘트가 달라도 동일 키로 판별한다.
    """
    parts = key_line.split(None, 2)
    if len(parts) < 2:
        return False
    key_type, key_data = parts[0], parts[1]

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        line_parts = line.split(None, 2)
        if len(line_parts) >= 2 and line_parts[0] == key_type and line_parts[1] == key_data:
            return True
    return False


def apply_local_ssh_config(key_info: PublicKeyInfo, host: str, port: int, username: str) -> str:
    """등록된 키를 사용할 수 있도록 로컬 OpenSSH config를 반영한다."""
    try:
        identity_file = private_key_path_from_public_key(key_info.path)
        update = ensure_host_config(
            host=host,
            port=port,
            username=username,
            identity_file=identity_file,
        )
        return f"로컬 SSH config: {update.status.value} (Host {update.host}, IdentityFile {update.identity_file})"
    except Exception as exc:
        return f"경고: 로컬 SSH config 반영 실패: {exc}"


def register_key(
    key_info: PublicKeyInfo,
    host: str,
    port: int,
    username: str,
    password: str,
) -> tuple[RegisterResult, str]:
    """원격 서버에 공개키를 등록한다.

    Returns:
        (결과 상태, 메시지)
    """
    try:
        def operation(conn: SSHConnection) -> tuple[RegisterResult, str]:
            conn.ensure_ssh_dir()
            existing = conn.read_authorized_keys()

            if key_exists_in_content(key_info.full_line, existing):
                return RegisterResult.ALREADY_EXISTS, "이미 등록된 키입니다."

            conn.append_authorized_key(key_info.full_line, existing)
            return RegisterResult.SUCCESS, "키가 성공적으로 등록되었습니다."

        (status, message), warning = run_with_host_trust_fallback(host, port, username, password, operation)
        messages = []
        if warning:
            messages.append(warning)
        messages.append(message)
        if status in {RegisterResult.SUCCESS, RegisterResult.ALREADY_EXISTS}:
            messages.append(apply_local_ssh_config(key_info, host, port, username))
        return status, "\n".join(messages)
    except Exception as exc:
        return RegisterResult.FAILED, format_connection_error(exc)


def test_connection(host: str, port: int, username: str, password: str) -> tuple[bool, str]:
    """서버 접속 테스트."""
    try:
        hostname, warning = run_with_host_trust_fallback(
            host,
            port,
            username,
            password,
            lambda conn: conn.test_connection(),
        )
        message = f"접속 성공 (원격 호스트: {hostname})"
        if warning:
            return True, f"{warning}\n{message}"
        return True, message
    except Exception as exc:
        return False, format_connection_error(exc)
