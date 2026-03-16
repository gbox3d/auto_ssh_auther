"""PyInstaller 빌드를 실행한다."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent
    spec_path = project_root / "auto_ssh_auther.spec"

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_path),
    ]
    return subprocess.run(command, cwd=project_root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
