"""PyInstaller 빌드 후 릴리즈용 zip 패키지까지 생성한다."""

from __future__ import annotations

import platform
import subprocess
import sys
import tomllib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def load_project_metadata(project_root: Path) -> tuple[str, str]:
    pyproject_path = project_root / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    project = data["project"]
    app_name = project["name"].replace("-", "_")
    version = project["version"]
    return app_name, version


def platform_tag() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    system_aliases = {
        "windows": "windows",
        "darwin": "macos",
        "linux": "linux",
    }
    machine_aliases = {
        "amd64": "x86_64",
        "x64": "x86_64",
        "x86_64": "x86_64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }

    normalized_system = system_aliases.get(system, system)
    normalized_machine = machine_aliases.get(machine, machine)
    return f"{normalized_system}_{normalized_machine}"


def build_release_zip(project_root: Path, app_name: str, version: str) -> Path:
    dist_root = project_root / "dist"
    release_root = project_root / "release"
    bundle_dir = dist_root / app_name
    app_bundle = dist_root / f"{app_name}.app"

    if bundle_dir.exists():
        source_path = bundle_dir
    elif app_bundle.exists():
        source_path = app_bundle
    else:
        raise FileNotFoundError(
            f"빌드 결과물을 찾을 수 없습니다: {bundle_dir} 또는 {app_bundle}"
        )

    zip_name = f"{app_name}_{platform_tag()}_{version}.zip"
    release_root.mkdir(exist_ok=True)
    zip_path = release_root / zip_name
    legacy_zip_path = dist_root / zip_name

    if zip_path.exists():
        zip_path.unlink()
    if legacy_zip_path.exists():
        legacy_zip_path.unlink()

    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
        for file_path in source_path.rglob("*"):
            if file_path.is_file():
                archive.write(file_path, arcname=file_path.relative_to(dist_root))

    return zip_path


def main() -> int:
    project_root = Path(__file__).resolve().parent
    spec_path = project_root / "auto_ssh_auther.spec"
    app_name, version = load_project_metadata(project_root)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_path),
    ]
    result = subprocess.run(command, cwd=project_root)
    if result.returncode != 0:
        return result.returncode

    zip_path = build_release_zip(project_root, app_name, version)
    print(f"Release package created: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
