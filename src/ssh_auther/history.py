"""접속 이력(프로파일) 저장/로드.

비밀번호는 절대 저장하지 않는다. host/port/user 같은 비밀 아닌 접속 메타데이터만 다룬다.
이 모듈은 Qt에 의존하지 않는다(저장 경로는 호출 측에서 결정해 Path로 넘긴다).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

MAX_PROFILES = 30


@dataclass(frozen=True)
class ConnectionProfile:
    host: str
    port: int
    user: str


def load_history(path: Path) -> list[ConnectionProfile]:
    """이력 파일을 읽어 프로파일 목록을 반환한다. 없거나 깨졌으면 빈 목록."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []

    items = raw.get("profiles", []) if isinstance(raw, dict) else []
    profiles: list[ConnectionProfile] = []
    for item in items:
        try:
            host = str(item["host"]).strip()
            port = int(item["port"])
            user = str(item["user"]).strip()
        except (KeyError, TypeError, ValueError):
            continue
        if host and user:
            profiles.append(ConnectionProfile(host, port, user))
    return profiles


def save_history(path: Path, profiles: list[ConnectionProfile]) -> None:
    """프로파일 목록을 JSON으로 저장한다(비밀번호 미포함)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": 1,
        "profiles": [{"host": p.host, "port": p.port, "user": p.user} for p in profiles],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_profile(
    profiles: list[ConnectionProfile],
    host: str,
    port: int,
    user: str,
    *,
    max_profiles: int = MAX_PROFILES,
) -> list[ConnectionProfile]:
    """host 기준으로 중복을 제거하고 최신 항목을 맨 앞에 둔 새 목록을 반환한다."""
    host = host.strip()
    user = user.strip()
    if not host or not user:
        return list(profiles)

    newest = ConnectionProfile(host, port, user)
    kept = [p for p in profiles if p.host != host]
    return [newest, *kept][:max_profiles]
