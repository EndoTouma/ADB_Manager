from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QComboBox
)


class SSHConnectDialog(QDialog):
    
    def __init__(self, parent=None, saved_connections: list[dict] | None = None):
        super().__init__(parent)
        self.setWindowTitle("New SSH Connection")
        self._result = None

        self.name = QLineEdit(self)
        self.host = QLineEdit(self)
        self.port = QLineEdit(self); self.port.setText("22")
        self.user = QLineEdit(self); self.user.setText("Administrator")
        self.password = QLineEdit(self); self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.hostkey = QLineEdit(self)

        form = QFormLayout(self)

        self.saved = QComboBox(self)
        self.saved.addItem("— choose saved —")
        for c in saved_connections or []:
            self.saved.addItem(
                c.get("name") or f"{c.get('host')}:{c.get('port')} ({c.get('user')})", c
            )
        self.saved.currentIndexChanged.connect(self._apply_saved)

        form.addRow("Saved:", self.saved)
        form.addRow("Name (optional):", self.name)
        form.addRow("Host:", self.host)
        form.addRow("Port:", self.port)
        form.addRow("User:", self.user)
        form.addRow("Password:", self.password)
        form.addRow("Host key (optional):", self.hostkey)  # ← НОВОЕ

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self
        )
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

        self.setLayout(form)
        self.resize(440, 260)

    def _apply_saved(self, idx: int):
        data = self.saved.itemData(idx)
        if not data:
            return
        self.name.setText(data.get("name", ""))
        self.host.setText(data["host"])
        self.port.setText(str(data.get("port", 22)))
        self.user.setText(data.get("user", "Administrator"))
        self.password.setText(data.get("password", ""))
        self.hostkey.setText(data.get("hostkey", ""))

    def _accept(self):
        h = self.host.text().strip()
        p = int(self.port.text() or "22")
        u = self.user.text().strip() or "Administrator"
        if not h:
            self.host.setFocus(); return
        self._result = {
            "name": self.name.text().strip(),
            "host": h,
            "port": p,
            "user": u,
            "password": self.password.text().strip(),
            "hostkey": self.hostkey.text().strip(),
        }
        self.accept()

    def get_result(self) -> dict:
        return self._result or {}
