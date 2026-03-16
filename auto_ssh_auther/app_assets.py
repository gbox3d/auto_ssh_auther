"""앱 아이콘과 런타임 리소스 경로를 관리한다."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon


APP_NAME = "Auto SSH Auther"
APP_VERSION = "v1"
WINDOW_TITLE = f"{APP_NAME} {APP_VERSION}"
WINDOWS_APP_ID = "com.gbworks.auto-ssh-auther"


def _bundle_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]


def resource_path(name: str) -> Path:
    return _bundle_root() / name


def runtime_icon_path() -> Path:
    preferred = "icon_ssh_auther.ico" if sys.platform == "win32" else "icon_ssh_auther.png"
    fallback = "icon_ssh_auther.png" if preferred.endswith(".ico") else "icon_ssh_auther.ico"

    candidate = resource_path(preferred)
    if candidate.exists():
        return candidate
    return resource_path(fallback)


def build_icon_path() -> Path:
    if sys.platform == "win32":
        return resource_path("icon_ssh_auther.ico")
    return resource_path("icon_ssh_auther.png")


def load_app_icon() -> QIcon:
    return QIcon(str(runtime_icon_path()))


def configure_windows_app_id() -> None:
    if sys.platform != "win32":
        return

    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(WINDOWS_APP_ID)
    except (AttributeError, OSError):
        pass
