"""등록된 키로 실제 ssh 로그인이 되는지 시스템 ssh 클라이언트로 검증한다."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VerifyResult:
    ok: bool
    message: str


def build_verify_command(
    host: str,
    port: int,
    username: str,
    identity_file: Path,
    timeout: int = 8,
) -> list[str]:
    """암호 폴백 없이 키 전용(BatchMode)으로 접속을 시도하는 ssh 명령을 만든다."""
    return [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", "PreferredAuthentications=publickey",
        "-o", "IdentitiesOnly=yes",
        "-o", f"ConnectTimeout={timeout}",
        "-o", "StrictHostKeyChecking=accept-new",
        "-i", str(identity_file),
        "-p", str(port),
        f"{username}@{host}",
        "true",
    ]


def verify_key_login(
    host: str,
    port: int,
    username: str,
    identity_file: Path,
    timeout: int = 8,
) -> VerifyResult:
    """등록된 키만으로 서버 로그인이 되는지 확인한다."""
    if shutil.which("ssh") is None:
        return VerifyResult(False, "키 로그인 검증 건너뜀: 시스템 ssh 클라이언트를 찾을 수 없습니다.")

    command = build_verify_command(host, port, username, identity_file, timeout)
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout + 7)
    except subprocess.TimeoutExpired:
        return VerifyResult(False, "키 로그인 검증 실패: 응답 시간 초과.")

    if proc.returncode == 0:
        return VerifyResult(True, "키 로그인 검증 성공: 암호 없이 키로 접속됩니다.")

    detail = (proc.stderr or "").strip().splitlines()
    reason = detail[-1].strip() if detail else f"exit {proc.returncode}"
    return VerifyResult(False, f"키 로그인 검증 실패: {reason}")
