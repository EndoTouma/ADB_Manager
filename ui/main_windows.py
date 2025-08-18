from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QIcon, QAction, QKeySequence
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QApplication, QHBoxLayout,
    QLabel, QMenuBar, QMessageBox
)

from ui.about_tab import AboutTab
from ui.control_tab import ControlTab
from utils.data_management import DataManager

APP_ORG = "ADBTools"
APP_NAME = "ADB Manager"
SETTINGS_FILE = "adb_manager.ini"


class ADBManager(QWidget):
    def __init__(self, devices=None, commands=None):
        super().__init__()

        if devices is None or commands is None:
            devices, commands = DataManager.load_data()

        self.devices = devices
        self.commands = commands

        self.tab_control = ControlTab(self.devices, self.commands)
        self._tab_about_cached = None  # отложенное создание

        self.status_label = QLabel("Ready")
        self.tabs = QTabWidget()
        self.menubar = QMenuBar()

        self.settings = QSettings(APP_ORG, APP_NAME)

        self.init_ui()
        self.init_menu()
        self.restore_state()

        self.tab_control.refresh_device_list()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.tabs.addTab(self.tab_control, "Control")
        self.tabs.addTab(QWidget(), "About")
        self.tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self.menubar)

        layout.addWidget(self.tabs)

        status_bar = QHBoxLayout()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setStyleSheet("#statusLabel { color: #666; padding: 4px; }")
        status_bar.addWidget(self.status_label, 1)
        layout.addLayout(status_bar)

        self.setLayout(layout)
        self.setWindowTitle(APP_NAME)
        try:
            self.setWindowIcon(QIcon('resources/adb.ico'))
        except Exception:
            pass

        self.resize(700, 900)
        self.setMinimumSize(640, 720)

        self.show()

    def init_menu(self):
        file_menu = self.menubar.addMenu("&File")

        act_refresh = QAction("Refresh Status\tF5", self)
        act_refresh.setShortcut(QKeySequence(Qt.Key.Key_F5))
        act_refresh.triggered.connect(self._refresh_status_action)
        file_menu.addAction(act_refresh)

        act_restart_adb = QAction("Restart ADB server\tCtrl+R", self)
        act_restart_adb.setShortcut(QKeySequence("Ctrl+R"))
        act_restart_adb.triggered.connect(self._restart_adb_action)
        file_menu.addAction(act_restart_adb)

        file_menu.addSeparator()

        act_quit = QAction("Quit\tCtrl+Q", self)
        act_quit.setShortcut(QKeySequence("Ctrl+Q"))
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        help_menu = self.menubar.addMenu("&Help")
        act_about = QAction("About", self)
        act_about.triggered.connect(self._open_about_tab)
        help_menu.addAction(act_about)

    def _refresh_status_action(self):
        self.tab_control.refresh_device_list()
        self.set_status("Device status refreshed")

    def _restart_adb_action(self):
        try:
            from subprocess import run, CalledProcessError
            run(["adb", "kill-server"], check=True)
            run(["adb", "start-server"], check=True)
            self.set_status("ADB server restarted")
            self.tab_control.refresh_device_list()
        except Exception as e:
            QMessageBox.critical(self, "ADB Error", f"Failed to restart ADB: {e}")
            self.set_status("ADB restart failed")

    def _open_about_tab(self):
        idx = 1
        self.tabs.setCurrentIndex(idx)

    def _on_tab_changed(self, index: int):
        if index == 1 and self._tab_about_cached is None:
            self._tab_about_cached = AboutTab()
            self.tabs.removeTab(1)
            self.tabs.addTab(self._tab_about_cached, "About")
            self.tabs.setCurrentIndex(1)
        self.set_status(f"Active tab: {self.tabs.tabText(index)}")

    def set_status(self, text: str):
        self.status_label.setText(text)

    def restore_state(self):
        geo = self.settings.value("window/geometry")
        if geo:
            self.restoreGeometry(geo)
        else:
            pass

        idx = int(self.settings.value("tabs/last_index", 0))
        if 0 <= idx < self.tabs.count():
            self.tabs.setCurrentIndex(idx)

    def save_state(self):
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("tabs/last_index", self.tabs.currentIndex())

    def closeEvent(self, event):
        try:
            if hasattr(self.tab_control, "logcat_threads"):
                for dev, th in list(self.tab_control.logcat_threads.items()):
                    try:
                        th.stop()
                    except Exception:
                        pass
                self.tab_control.logcat_threads.clear()
        except Exception:
            pass

        self.save_state()
        super().closeEvent(event)
