from PyQt6.QtCore import Qt, QTimer, QSettings
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QDialogButtonBox, QPushButton, QLabel, QWidget, QSizePolicy, QMessageBox
)


class DeleteCommandDialog(QDialog):

    SETTINGS_ORG = "ADBManager"
    SETTINGS_APP = "ADBManagerApp"
    SETTINGS_KEY = "DeleteCommandDialog/geometry"

    def __init__(self, commands: list[str], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Delete Commands")
        self.setModal(True)

        self._commands = commands[:]  # копия
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(150)
        self._debounce.timeout.connect(self._apply_filter)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        search_row = QHBoxLayout()
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Filter commands...")
        self.search_edit.textChanged.connect(lambda _: self._debounce.start())
        clear_btn = QPushButton("Clear", self)
        clear_btn.clicked.connect(self.search_edit.clear)
        search_row.addWidget(QLabel("Search:", self))
        search_row.addWidget(self.search_edit, 1)
        search_row.addWidget(clear_btn)
        root.addLayout(search_row)

        self.list_widget = QListWidget(self)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.addWidget(self.list_widget, 1)

        select_row = QHBoxLayout()
        self.btn_all = QPushButton("Select All", self)
        self.btn_none = QPushButton("Select None", self)
        self.btn_invert = QPushButton("Invert", self)
        self.btn_all.clicked.connect(self.select_all_commands)
        self.btn_none.clicked.connect(self.select_none_commands)
        self.btn_invert.clicked.connect(self.invert_selection)
        select_row.addWidget(self.btn_all)
        select_row.addWidget(self.btn_none)
        select_row.addWidget(self.btn_invert)
        select_row.addStretch(1)
        root.addLayout(select_row)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self
        )
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        root.addWidget(self.button_box)

        self._populate(self._commands)
        self._update_ok_enabled()

        self._restore_geometry()

        self.list_widget.itemChanged.connect(lambda _: self._update_ok_enabled())

        self.resize(520, 420)

    def _restore_geometry(self):
        s = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        geom = s.value(self.SETTINGS_KEY)
        if geom:
            self.restoreGeometry(geom)

    def closeEvent(self, e):
        s = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        s.setValue(self.SETTINGS_KEY, self.saveGeometry())
        super().closeEvent(e)

    def _populate(self, items: list[str]):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for cmd in items:
            it = QListWidgetItem(cmd, self.list_widget)
            it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(Qt.CheckState.Unchecked)
        self.list_widget.blockSignals(False)

    def _apply_filter(self):
        query = self.search_edit.text().strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            text = item.text().lower()
            is_match = (query in text) if query else True
            item.setHidden(not is_match)

    def select_all_commands(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.CheckState.Checked)
        self._update_ok_enabled()

    def select_none_commands(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.CheckState.Unchecked)
        self._update_ok_enabled()

    def invert_selection(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not item.isHidden():
                item.setCheckState(
                    Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked
                    else Qt.CheckState.Checked
                )
        self._update_ok_enabled()

    def _update_ok_enabled(self):
        any_checked = any(
            self.list_widget.item(i).checkState() == Qt.CheckState.Checked
            for i in range(self.list_widget.count())
            if not self.list_widget.item(i).isHidden()
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(any_checked)

    def _on_accept(self):
        if not self.get_selected_commands():
            QMessageBox.information(self, "Delete Commands", "Please select at least one command.")
            return
        self.accept()

    def get_selected_commands(self) -> list[str]:
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.text())
        return selected