"""로컬 ~/.ssh 디렉터리에서 공개키 파일을 탐색, 파싱, 생성, 삭제한다."""

import subprocess
from dataclasses import dataclass
from pathlib import Path


VALID_KEY_TYPES = {
    "ssh-rsa",
    "ssh-ed25519",
    "ssh-dss",
    "ecdsa-sha2-nistp256",
    "ecdsa-sha2-nistp384",
    "ecdsa-sha2-nistp521",
    "sk-ssh-ed25519@openssh.com",
    "sk-ecdsa-sha2-nistp256@openssh.com",
}


@dataclass
class PublicKeyInfo:
    path: Path
    filename: str
    key_type: str
    key_data: str  # base64 부분
    comment: str
    full_line: str  # authorized_keys에 추가할 전체 문자열

    def display_name(self) -> str:
        if self.comment:
            return f"{self.filename} ({self.key_type}, {self.comment})"
        return f"{self.filename} ({self.key_type})"


def parse_public_key(path: Path) -> PublicKeyInfo | None:
    """공개키 파일을 읽어 파싱한다. 유효하지 않으면 None을 반환한다."""
    try:
        content = path.read_text().strip()
    except (OSError, UnicodeDecodeError):
        return None

    if not content:
        return None

    # 첫 번째 줄만 사용 (멀티라인 키 파일 방지)
    line = content.splitlines()[0].strip()
    parts = line.split(None, 2)

    if len(parts) < 2:
        return None

    key_type = parts[0]
    if key_type not in VALID_KEY_TYPES:
        return None

    key_data = parts[1]
    comment = parts[2] if len(parts) > 2 else ""

    return PublicKeyInfo(
        path=path,
        filename=path.name,
        key_type=key_type,
        key_data=key_data,
        comment=comment,
        full_line=line,
    )


SUPPORTED_KEY_ALGORITHMS = ["ed25519", "rsa", "ecdsa"]


def generate_key(
    name: str,
    key_type: str = "ed25519",
    comment: str = "",
    bits: int | None = None,
    ssh_dir: Path | None = None,
) -> Path:
    """ssh-keygen으로 새 키 쌍을 생성한다. 생성된 공개키 경로를 반환한다."""
    if ssh_dir is None:
        ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)

    if key_type not in SUPPORTED_KEY_ALGORITHMS:
        raise ValueError(f"지원하지 않는 키 타입: {key_type} (지원: {SUPPORTED_KEY_ALGORITHMS})")

    key_path = ssh_dir / name
    if key_path.exists() or key_path.with_suffix(".pub").exists():
        raise FileExistsError(f"이미 존재하는 키 파일: {key_path}")

    cmd = ["ssh-keygen", "-t", key_type, "-f", str(key_path), "-N", ""]
    if comment:
        cmd += ["-C", comment]
    if bits and key_type == "rsa":
        cmd += ["-b", str(bits)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ssh-keygen 실패: {result.stderr.strip()}")

    return key_path.with_suffix(".pub")


def delete_key(key_info: PublicKeyInfo) -> list[Path]:
    """공개키와 대응하는 비밀키 파일을 삭제한다. 삭제된 파일 목록을 반환한다."""
    deleted = []
    pub_path = key_info.path
    # 비밀키는 .pub 확장자를 제거한 경로
    private_path = pub_path.with_suffix("")

    for p in [pub_path, private_path]:
        if p.exists():
            p.unlink()
            deleted.append(p)

    return deleted


def find_public_keys(ssh_dir: Path | None = None) -> list[PublicKeyInfo]:
    """~/.ssh 디렉터리에서 .pub 파일을 찾아 파싱된 목록을 반환한다."""
    if ssh_dir is None:
        ssh_dir = Path.home() / ".ssh"

    if not ssh_dir.is_dir():
        return []

    keys = []
    for pub_file in sorted(ssh_dir.glob("*.pub")):
        info = parse_public_key(pub_file)
        if info is not None:
            keys.append(info)

    return keys
