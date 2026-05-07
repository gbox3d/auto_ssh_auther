"""로컬 OpenSSH config 파일을 추가/갱신한다."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class SSHConfigStatus(Enum):
    ADDED = "added"
    UPDATED = "updated"
    UNCHANGED = "unchanged"


@dataclass(frozen=True)
class SSHConfigUpdate:
    status: SSHConfigStatus
    path: Path
    host: str
    identity_file: Path


MANAGED_OPTIONS = (
    "HostName",
    "Port",
    "User",
    "IdentityFile",
    "IdentitiesOnly",
    "PreferredAuthentications",
)


def private_key_path_from_public_key(public_key_path: Path) -> Path:
    """`.pub` 공개키 경로에서 대응하는 비밀키 경로를 계산한다."""
    if public_key_path.suffix.lower() == ".pub":
        return public_key_path.with_suffix("")
    return public_key_path


def ensure_host_config(
    *,
    host: str,
    port: int,
    username: str,
    identity_file: Path,
    config_path: Path | None = None,
    home_dir: Path | None = None,
) -> SSHConfigUpdate:
    """Host별 접속 정보를 `~/.ssh/config`에 idempotent하게 반영한다."""
    host = host.strip()
    username = username.strip()
    if not host:
        raise ValueError("Host가 비어 있습니다.")
    if not username:
        raise ValueError("User가 비어 있습니다.")
    if not 1 <= port <= 65535:
        raise ValueError(f"Port 범위가 올바르지 않습니다: {port}")

    if home_dir is None:
        home_dir = Path.home()
    if config_path is None:
        config_path = home_dir / ".ssh" / "config"

    ssh_dir = config_path.parent
    ssh_dir.mkdir(mode=0o700, exist_ok=True)

    identity_file = Path(identity_file)
    desired = _desired_options(host, port, username, identity_file, home_dir)
    original_lines = _read_lines(config_path)

    block = _find_host_block(original_lines, host)
    if block is None:
        next_lines = _insert_host_block(original_lines, host, desired)
        status = SSHConfigStatus.ADDED
        _write_lines(config_path, next_lines)
    else:
        start, end = block
        next_lines, changed = _update_host_block(original_lines, start, end, desired)
        status = SSHConfigStatus.UPDATED if changed else SSHConfigStatus.UNCHANGED
        if changed:
            _write_lines(config_path, next_lines)

    return SSHConfigUpdate(
        status=status,
        path=config_path,
        host=host,
        identity_file=identity_file,
    )


def _desired_options(host: str, port: int, username: str, identity_file: Path, home_dir: Path) -> dict[str, str]:
    return {
        "HostName": host,
        "Port": str(port),
        "User": username,
        "IdentityFile": _format_identity_file(identity_file, home_dir),
        "IdentitiesOnly": "yes",
        "PreferredAuthentications": "publickey",
    }


def _format_identity_file(identity_file: Path, home_dir: Path) -> str:
    path = identity_file.expanduser()
    try:
        resolved_path = path.resolve(strict=False)
        resolved_home = home_dir.expanduser().resolve(strict=False)
        relative = resolved_path.relative_to(resolved_home)
        return f"~/{relative.as_posix()}"
    except ValueError:
        return path.as_posix()


def _read_lines(config_path: Path) -> list[str]:
    if not config_path.exists():
        return []
    return config_path.read_text(encoding="utf-8").splitlines()


def _write_lines(config_path: Path, lines: list[str]) -> None:
    content = "\n".join(lines)
    if content:
        content += "\n"
    config_path.write_text(content, encoding="utf-8")
    try:
        config_path.chmod(0o600)
    except OSError:
        pass


def _parse_directive(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    parts = stripped.split(None, 1)
    key = parts[0]
    value = parts[1].strip() if len(parts) == 2 else ""
    return key, value


def _is_section_start(line: str) -> bool:
    parsed = _parse_directive(line)
    return parsed is not None and parsed[0].lower() in {"host", "match"}


def _find_host_block(lines: list[str], host: str) -> tuple[int, int] | None:
    index = 0
    while index < len(lines):
        parsed = _parse_directive(lines[index])
        if parsed is None or parsed[0].lower() != "host":
            index += 1
            continue

        start = index
        end = _next_section_index(lines, start + 1)
        patterns = parsed[1].split()
        if host in patterns:
            return start, end
        index = end

    return None


def _next_section_index(lines: list[str], start: int) -> int:
    for index in range(start, len(lines)):
        if _is_section_start(lines[index]):
            return index
    return len(lines)


def _insert_host_block(lines: list[str], host: str, desired: dict[str, str]) -> list[str]:
    block = _render_host_block(host, desired)
    insert_at = _first_section_index(lines)

    prefix = lines[:insert_at]
    suffix = lines[insert_at:]

    if prefix and prefix[-1].strip():
        prefix.append("")
    prefix.extend(block)
    if suffix:
        prefix.append("")
        prefix.extend(suffix)
    return prefix


def _first_section_index(lines: list[str]) -> int:
    for index, line in enumerate(lines):
        if _is_section_start(line):
            return index
    return len(lines)


def _render_host_block(host: str, desired: dict[str, str]) -> list[str]:
    return [f"Host {host}", *(f"  {key} {desired[key]}" for key in MANAGED_OPTIONS)]


def _update_host_block(
    lines: list[str],
    start: int,
    end: int,
    desired: dict[str, str],
) -> tuple[list[str], bool]:
    block = lines[start:end]
    desired_by_lower = {key.lower(): key for key in MANAGED_OPTIONS}
    indent = _detect_option_indent(block)
    seen: set[str] = set()
    changed = False
    next_block = [block[0]]

    for line in block[1:]:
        parsed = _parse_directive(line)
        if parsed is None or parsed[0].lower() not in desired_by_lower:
            next_block.append(line)
            continue

        key = desired_by_lower[parsed[0].lower()]
        if key in seen:
            changed = True
            continue

        seen.add(key)
        if _same_value(parsed[1], desired[key]):
            next_block.append(line)
        else:
            next_block.append(f"{indent}{key} {desired[key]}")
            changed = True

    for key in MANAGED_OPTIONS:
        if key not in seen:
            next_block.append(f"{indent}{key} {desired[key]}")
            changed = True

    return lines[:start] + next_block + lines[end:], changed


def _detect_option_indent(block: list[str]) -> str:
    for line in block[1:]:
        parsed = _parse_directive(line)
        if parsed is not None:
            return line[: len(line) - len(line.lstrip())]
    return "  "


def _same_value(current: str, desired: str) -> bool:
    return _unquote(current.strip()) == desired


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
