"""등록된 키로 실제 ssh 로그인이 되는지 시스템 ssh 클라이언트로 검증한다."""

from __future__ import annotations

import os
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
    """암호 폴백 없이 키 전용(BatchMode)으로 접속을 시도하는 ssh 명령을 만든다.

    `-F os.devnull`로 사용자 `~/.ssh/config`를 무시한다. 그렇지 않으면 접속 호스트와
    매칭되는 config 블록의 `IdentityFile`이 함께 시도되어, 지정한 키가 미등록이어도
    config의 다른 키로 접속에 성공해 거짓 양성이 난다. config를 무시하면 `-i`로 지정한
    그 키 하나만 검증된다(`IdentitiesOnly=yes`는 agent만 막고 config IdentityFile은 못 막는다).
    """
    return [
        "ssh",
        "-F", os.devnull,
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
