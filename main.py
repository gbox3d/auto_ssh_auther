import sys

from PySide6.QtWidgets import QApplication

from ssh_auther.app_assets import APP_NAME, WINDOW_TITLE, configure_windows_app_id, load_app_icon
from ssh_auther.ui.main_window import MainWindow


def main():
    configure_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(load_app_icon())

    window = MainWindow()
    window.setWindowTitle(WINDOW_TITLE)
    window.setWindowIcon(load_app_icon())
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
