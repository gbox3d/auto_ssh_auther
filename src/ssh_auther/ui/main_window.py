"""메인 GUI 윈도우."""

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QLineEdit,
    QSpinBox,
    QPushButton,
    QTextEdit,
    QMessageBox,
    QDialog,
    QComboBox,
    QDialogButtonBox,
    QFormLayout,
)

from ssh_auther.app_assets import WINDOW_TITLE, load_app_icon
from ssh_auther.keys import find_public_keys, PublicKeyInfo, generate_key, delete_key, SUPPORTED_KEY_ALGORITHMS
from ssh_auther.services.register import register_key, test_connection, RegisterResult


class WorkerThread(QThread):
    """백그라운드에서 SSH 작업을 수행하는 스레드."""
    finished = Signal(object)  # 결과 tuple

    def __init__(self, func, *args):
        super().__init__()
        self.func = func
        self.args = args

    def run(self):
        result = self.func(*self.args)
        self.finished.emit(result)


class GenerateKeyDialog(QDialog):
    """SSH 키 생성 다이얼로그."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SSH 키 생성")
        self.setMinimumWidth(350)
        self.setWindowIcon(load_app_icon())

        layout = QFormLayout(self)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("예: id_ed25519_myserver")
        layout.addRow("키 파일명:", self.input_name)

        self.combo_type = QComboBox()
        self.combo_type.addItems(SUPPORTED_KEY_ALGORITHMS)
        self.combo_type.currentTextChanged.connect(self._on_type_changed)
        layout.addRow("키 타입:", self.combo_type)

        self.input_bits = QSpinBox()
        self.input_bits.setRange(2048, 8192)
        self.input_bits.setValue(4096)
        self.input_bits.setEnabled(False)
        layout.addRow("비트 수 (RSA):", self.input_bits)

        self.input_comment = QLineEdit()
        self.input_comment.setPlaceholderText("예: user@host (선택사항)")
        layout.addRow("코멘트:", self.input_comment)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_type_changed(self, text: str):
        self.input_bits.setEnabled(text == "rsa")

    def get_params(self) -> dict:
        return {
            "name": self.input_name.text().strip(),
            "key_type": self.combo_type.currentText(),
            "comment": self.input_comment.text().strip(),
            "bits": self.input_bits.value() if self.combo_type.currentText() == "rsa" else None,
        }


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(600, 500)
        self.setWindowIcon(load_app_icon())

        self._keys: list[PublicKeyInfo] = []
        self._worker: WorkerThread | None = None

        self._build_ui()
        self._load_keys()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # --- 공개키 목록 ---
        key_group = QGroupBox("로컬 공개키 (~/.ssh/*.pub)")
        key_layout = QVBoxLayout(key_group)

        self.key_list = QListWidget()
        key_layout.addWidget(self.key_list)

        key_btn_layout = QHBoxLayout()

        self.btn_reload = QPushButton("Reload Keys")
        self.btn_reload.clicked.connect(self._load_keys)
        key_btn_layout.addWidget(self.btn_reload)

        self.btn_generate = QPushButton("Generate Key")
        self.btn_generate.clicked.connect(self._on_generate_key)
        key_btn_layout.addWidget(self.btn_generate)

        self.btn_delete = QPushButton("Delete Key")
        self.btn_delete.clicked.connect(self._on_delete_key)
        key_btn_layout.addWidget(self.btn_delete)

        key_layout.addLayout(key_btn_layout)

        layout.addWidget(key_group)

        # --- 서버 입력 ---
        server_group = QGroupBox("서버 접속 정보")
        server_layout = QVBoxLayout(server_group)

        # Host
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Host:"))
        self.input_host = QLineEdit()
        self.input_host.setPlaceholderText("예: 192.168.1.100")
        row1.addWidget(self.input_host)
        server_layout.addLayout(row1)

        # Port
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Port:"))
        self.input_port = QSpinBox()
        self.input_port.setRange(1, 65535)
        self.input_port.setValue(22)
        row2.addWidget(self.input_port)
        server_layout.addLayout(row2)

        # Username
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Username:"))
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("예: root")
        row3.addWidget(self.input_username)
        server_layout.addLayout(row3)

        # Password
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Password:"))
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        row4.addWidget(self.input_password)
        server_layout.addLayout(row4)

        layout.addWidget(server_group)

        # --- 버튼 ---
        btn_layout = QHBoxLayout()

        self.btn_test = QPushButton("Test Connection")
        self.btn_test.clicked.connect(self._on_test_connection)
        btn_layout.addWidget(self.btn_test)

        self.btn_register = QPushButton("Register Key")
        self.btn_register.clicked.connect(self._on_register_key)
        btn_layout.addWidget(self.btn_register)

        layout.addLayout(btn_layout)

        # --- 결과 출력 ---
        result_group = QGroupBox("결과")
        result_layout = QVBoxLayout(result_group)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(120)
        result_layout.addWidget(self.result_text)

        layout.addWidget(result_group)

    def _load_keys(self):
        self.key_list.clear()
        self._keys = find_public_keys()

        if not self._keys:
            self.key_list.addItem("공개키 파일이 없습니다. (~/.ssh/*.pub)")
            return

        for key_info in self._keys:
            item = QListWidgetItem(key_info.display_name())
            self.key_list.addItem(item)

        self.key_list.setCurrentRow(0)

    def _get_selected_key(self) -> PublicKeyInfo | None:
        row = self.key_list.currentRow()
        if row < 0 or row >= len(self._keys):
            return None
        return self._keys[row]

    def _get_server_info(self) -> tuple[str, int, str, str] | None:
        host = self.input_host.text().strip()
        port = self.input_port.value()
        username = self.input_username.text().strip()
        password = self.input_password.text()

        if not host:
            self._log("오류: 서버 주소를 입력하세요.")
            return None
        if not username:
            self._log("오류: 사용자 이름을 입력하세요.")
            return None
        if not password:
            self._log("오류: 비밀번호를 입력하세요.")
            return None

        return host, port, username, password

    def _set_busy(self, busy: bool):
        self.btn_test.setEnabled(not busy)
        self.btn_register.setEnabled(not busy)
        self.btn_reload.setEnabled(not busy)
        self.btn_generate.setEnabled(not busy)
        self.btn_delete.setEnabled(not busy)

    def _log(self, message: str):
        self.result_text.append(message)

    # --- Generate Key ---
    def _on_generate_key(self):
        dialog = GenerateKeyDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        params = dialog.get_params()
        if not params["name"]:
            self._log("오류: 키 파일명을 입력하세요.")
            return

        try:
            pub_path = generate_key(**params)
            self._log(f"[성공] 키 생성 완료: {pub_path}")
            self._load_keys()
        except FileExistsError as e:
            self._log(f"[실패] {e}")
        except (RuntimeError, ValueError) as e:
            self._log(f"[실패] {e}")

    # --- Delete Key ---
    def _on_delete_key(self):
        key_info = self._get_selected_key()
        if not key_info:
            self._log("오류: 삭제할 공개키를 선택하세요.")
            return

        reply = QMessageBox.question(
            self,
            "키 삭제 확인",
            f"정말로 '{key_info.filename}' 키 쌍을 삭제하시겠습니까?\n"
            f"(비밀키도 함께 삭제됩니다)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            deleted = delete_key(key_info)
            names = ", ".join(p.name for p in deleted)
            self._log(f"[성공] 삭제됨: {names}")
            self._load_keys()
        except OSError as e:
            self._log(f"[실패] 삭제 오류: {e}")

    # --- Test Connection ---
    def _on_test_connection(self):
        info = self._get_server_info()
        if not info:
            return

        self._set_busy(True)
        self._log("접속 테스트 중...")

        self._worker = WorkerThread(test_connection, *info)
        self._worker.finished.connect(self._on_test_done)
        self._worker.start()

    def _on_test_done(self, result):
        success, message = result
        self._log(message)
        self._set_busy(False)

    # --- Register Key ---
    def _on_register_key(self):
        key_info = self._get_selected_key()
        if not key_info:
            self._log("오류: 등록할 공개키를 선택하세요.")
            return

        server_info = self._get_server_info()
        if not server_info:
            return

        self._set_busy(True)
        self._log(f"키 등록 중... ({key_info.filename})")

        self._worker = WorkerThread(register_key, key_info, *server_info)
        self._worker.finished.connect(self._on_register_done)
        self._worker.start()

    def _on_register_done(self, result):
        status, message = result
        if status == RegisterResult.SUCCESS:
            self._log(f"[성공] {message}")
        elif status == RegisterResult.ALREADY_EXISTS:
            self._log(f"[안내] {message}")
        else:
            self._log(f"[실패] {message}")
        self._set_busy(False)
