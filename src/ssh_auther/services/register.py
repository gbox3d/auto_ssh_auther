"""공개키 등록 흐름을 제어한다."""

import socket
from enum import Enum

import paramiko
from paramiko.ssh_exception import BadHostKeyException, NoValidConnectionsError, SSHException

from ssh_auther.keys import PublicKeyInfo
from ssh_auther.ssh import SSHConnection
from ssh_auther.ssh.local_config import (
    ensure_host_config,
    find_alias_collisions,
    private_key_path_from_public_key,
)
from ssh_auther.ssh.verify import verify_key_login


class RegisterResult(Enum):
    SUCCESS = "success"
    ALREADY_EXISTS = "already_exists"
    FAILED = "failed"


class KeyStatus(Enum):
    REGISTERED = "registered"          # 키로 로그인 가능 → 해제 제안
    NOT_REGISTERED = "not_registered"  # 서버는 응답하나 키 거부 → 등록 제안
    UNREACHABLE = "unreachable"        # 서버 무응답/도달 불가 → 동작 비활성


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


def remove_key_from_content(key_line: str, content: str) -> tuple[str, int]:
    """authorized_keys 내용에서 동일한 키(타입+데이터)를 제거한 새 내용과 제거 건수를 반환한다.

    코멘트는 무시하고 타입+base64 데이터로 매칭한다. 주석/빈 줄/다른 키는 그대로 둔다.
    """
    parts = key_line.split(None, 2)
    if len(parts) < 2:
        return content, 0
    key_type, key_data = parts[0], parts[1]

    kept: list[str] = []
    removed = 0
    for line in content.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            line_parts = stripped.split(None, 2)
            if len(line_parts) >= 2 and line_parts[0] == key_type and line_parts[1] == key_data:
                removed += 1
                continue
        kept.append(line)

    new_content = "\n".join(kept)
    if kept:
        new_content += "\n"
    return new_content, removed


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
            identity_file = private_key_path_from_public_key(key_info.path)
            messages.append(verify_key_login(host, port, username, identity_file).message)
            collisions = find_alias_collisions(host)
            if collisions:
                names = ", ".join(collisions)
                messages.append(
                    f"주의: 같은 서버({host})를 가리키지만 키 설정이 없는 Host 별칭이 있습니다: {names}. "
                    "해당 별칭으로 접속하면 키가 아니라 암호를 묻습니다."
                )
        return status, "\n".join(messages)
    except Exception as exc:
        return RegisterResult.FAILED, format_connection_error(exc)


def detect_key_status(
    key_info: PublicKeyInfo,
    host: str,
    port: int,
    username: str,
) -> tuple[KeyStatus, str]:
    """선택한 키만으로(암호 없이) 서버 등록 상태를 감지한다."""
    identity_file = private_key_path_from_public_key(key_info.path)
    result = verify_key_login(host, port, username, identity_file)
    if result.ok:
        return KeyStatus.REGISTERED, "등록됨 (키로 접속 가능)"
    if result.reason == "auth_failed":
        return KeyStatus.NOT_REGISTERED, "미등록 (서버는 응답함)"
    return KeyStatus.UNREACHABLE, result.message


def unregister_key(
    key_info: PublicKeyInfo,
    host: str,
    port: int,
    username: str,
    password: str,
) -> tuple[bool, str]:
    """원격 authorized_keys에서 선택한 키를 제거한다.

    Returns:
        (성공 여부, 메시지). 이미 없으면 제거할 항목이 없다는 안내와 함께 성공으로 본다.
    """
    try:
        def operation(conn: SSHConnection) -> bool:
            existing = conn.read_authorized_keys()
            if not key_exists_in_content(key_info.full_line, existing):
                return False
            new_content, _ = remove_key_from_content(key_info.full_line, existing)
            conn.write_authorized_keys(new_content)
            return True

        was_present, warning = run_with_host_trust_fallback(host, port, username, password, operation)
        messages = []
        if warning:
            messages.append(warning)
        if was_present:
            messages.append("키를 원격 authorized_keys에서 제거했습니다.")
        else:
            messages.append("이미 등록돼 있지 않습니다 (제거할 항목 없음).")
        return True, "\n".join(messages)
    except Exception as exc:
        return False, format_connection_error(exc)


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
