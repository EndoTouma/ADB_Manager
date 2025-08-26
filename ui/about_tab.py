from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QMessageBox, QProgressDialog, QLabel,
    QGroupBox, QTextEdit, QFrame, QApplication
)
import os
import sys
import shutil
import tempfile
import subprocess
import requests
from packaging import version


class AboutTab(QWidget):
    APP_INFO_LABELS = [
        ("ADB Manager", 9, False),
        ("Author: Eugene Vervai", 9, False),
        ("Contact: delspin1@gmail.com", 9, False),
        ("License: MIT License", 9, False)
    ]

    DESCRIPTION_TEXT = (
        "ADB Manager is an easy-to-use application designed to help you manage and control "
        "your devices using Android Debug Bridge (ADB) commands. With this app, you can effortlessly "
        "add and remove devices and commands to fit your specific needs, all through a user-friendly "
        "interface that eliminates the need for manual command line input.\n\n"
        "Key Features:\n"
        "    - Manage and execute ADB commands on multiple devices at the same time.\n"
        "    - Add and remove devices and commands easily through a simple UI.\n"
        "    - Monitor command execution output directly within the app.\n"
        "    - Real-time log monitoring and filtering.\n\n"
        "Whether you're a developer, tester, or tech enthusiast, ADB Manager is designed to "
        "streamline your workflow by providing a convenient interface for managing devices and executing "
        "ADB commands with ease."
    )

    CURRENT_VERSION = "3.0.1"
    REPO_API_URL = "https://api.github.com/repos/EndoTouma/ADB_Manager/releases/latest"

    def __init__(self):
        super().__init__()
        self._download_url = None
        self.update_thread: UpdateCheckThread | None = None
        self.download_thread: UpdateDownloadThread | None = None
        self.progress_dialog: QProgressDialog | None = None
        self._checked_once = False
        self.init_ui()

    def init_ui(self):
        layout_about = QVBoxLayout(self)

        app_info_group = self.create_group("App Information", self.app_info_ui())
        layout_about.addWidget(app_info_group)

        update_group = self.create_group("Update Information", self.update_ui())
        layout_about.addWidget(update_group)

        description_group = self.create_group("Description", self.description_ui())
        layout_about.addWidget(description_group)

        layout_about.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout_about)

    def create_group(self, title, layout):
        group = QGroupBox(title)
        group.setLayout(layout)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        return group

    def create_label(self, text, size, bold):
        label = QLabel(text)
        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)
        label.setFont(font)
        return label

    def app_info_ui(self):
        layout = QVBoxLayout()

        for text, size, bold in self.APP_INFO_LABELS:
            label = self.create_label(text, size, bold)
            layout.addWidget(label)

        horizontal_line = QFrame()
        horizontal_line.setFrameShape(QFrame.Shape.HLine)
        horizontal_line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(horizontal_line)

        return layout

    def update_ui(self):
        layout = QVBoxLayout()
        self.current_version_label = QLabel(f"Current Version: {self.CURRENT_VERSION}")
        self.current_version_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.latest_version_label = QLabel("Latest Version: Checking...")
        self.latest_version_label.setStyleSheet("color:#555;")
        self.latest_version_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.update_status_label = QLabel("Status: Checking...")
        self.update_status_label.setStyleSheet("color:#888;")

        self.update_button = QPushButton("Update")
        self.update_button.setEnabled(False)
        self.update_button.clicked.connect(self.update_application)

        layout.addWidget(self.current_version_label)
        layout.addWidget(self.latest_version_label)
        layout.addWidget(self.update_status_label)
        layout.addWidget(self.update_button)
        return layout

    def description_ui(self):
        layout = QVBoxLayout()
        description_text = QTextEdit()
        description_text.setText(self.DESCRIPTION_TEXT)
        description_text.setReadOnly(True)
        layout.addWidget(description_text)
        return layout

    def showEvent(self, event):
        super().showEvent(event)
        if not self._checked_once:
            self._checked_once = True
            self.check_for_updates()

    def closeEvent(self, event):
        try:
            if self.download_thread and self.download_thread.isRunning():
                self.download_thread.abort()
                self.download_thread.wait(2000)
        except Exception:
            pass
        super().closeEvent(event)

    def check_for_updates(self):
        self.update_thread = UpdateCheckThread(self.REPO_API_URL, self.CURRENT_VERSION)
        self.update_thread.done.connect(self.on_update_check_finished)  # <-- НЕ finished!
        self.update_thread.start()

    def on_update_check_finished(self, result: dict):
        status = result.get("status")
        if status == "error":
            self.update_status_label.setText("Status: Error checking for updates.")
            self.update_status_label.setStyleSheet("color:#c00;")
            QMessageBox.critical(self, "Error", result.get("message", "Unknown error"))
        elif status == "latest":
            latest = result.get("latest_version") or self.CURRENT_VERSION
            self.update_status_label.setText("Status: You have the latest version.")
            self.update_status_label.setStyleSheet("color:#2e7d32;")
            self.latest_version_label.setText(f"Latest Version: {latest}")
        elif status == "new_version":
            latest = result['latest_version']
            self.update_status_label.setText("Status: A new version is available.")
            self.update_status_label.setStyleSheet("color:#e65100;")
            self.latest_version_label.setText(f"Latest Version: {latest}")
            notes = result.get("notes") or ""
            if notes:
                QMessageBox.information(self, "Release notes", notes)
            self.update_button.setEnabled(True)
            self._download_url = result.get("download_url")

    def update_application(self):
        if not self._download_url:
            QMessageBox.warning(self, "Update", "Download URL is missing.")
            return
        reply = QMessageBox.question(
            self,
            "Update Available",
            "A new version is available. Do you want to download and install it?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.download_and_replace()

    def download_and_replace(self):
        self.progress_dialog = QProgressDialog("Downloading update...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowTitle("Update")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setValue(0)
        self.progress_dialog.canceled.connect(self._cancel_download)
        self.progress_dialog.show()

        self.download_thread = UpdateDownloadThread(self._download_url)
        self.download_thread.progress.connect(self.progress_dialog.setValue)
        self.download_thread.done.connect(self.on_download_finished)
        self.download_thread.start()

    def _cancel_download(self):
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.abort()

    def on_download_finished(self, result: dict):
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        if result.get("status") == "error":
            QMessageBox.critical(self, "Error", result.get("message", "Unknown error"))
        else:
            self.replace_and_restart(result["file_path"])

    def replace_and_restart(self, new_file_path):
        old_path = None
        try:
            app_path = os.path.abspath(sys.argv[0])
            target_path = app_path
            old_path = app_path + ".old"

            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass

            try:
                os.replace(app_path, old_path)
            except Exception:
                pass

            try:
                os.replace(new_file_path, target_path)
            except PermissionError:
                shutil.copyfile(new_file_path, target_path)

            QMessageBox.information(self, "Update", "New version installed. The application will now restart.")

            try:
                if sys.executable and sys.executable.lower().endswith(("python.exe", "pythonw.exe")):
                    subprocess.Popen([sys.executable, target_path] + sys.argv[1:], close_fds=True)
                else:
                    subprocess.Popen([target_path] + sys.argv[1:], close_fds=True)
            except Exception as e:
                QMessageBox.warning(self, "Restart", f"Failed to auto-restart: {e}\nPlease start the app manually.")

            QApplication.quit()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to replace the application file: {str(e)}")
            try:
                if old_path and os.path.exists(old_path):
                    os.replace(old_path, app_path)
            except Exception:
                pass

class UpdateCheckThread(QThread):
    progress = pyqtSignal(int)
    done = pyqtSignal(dict)

    def __init__(self, api_url, current_version):
        super().__init__()
        self.api_url = api_url
        self.current_version = current_version
        self.download_url = ""
        self.release_notes = ""

    def _normalize_ver(self, s: str) -> str:
        return (s or "").lstrip("vV").strip()

    def _pick_asset_url(self, assets):
        if not assets:
            return None
        exe = next((a for a in assets if str(a.get("name", "")).lower().endswith(".exe")), None)
        picked = exe or assets[0]
        return picked.get("browser_download_url")

    def run(self):
        try:
            headers = {
                "Accept": "application/vnd.github+json",
                "User-Agent": "ADB-Manager-Updater"
            }
            resp = requests.get(self.api_url, headers=headers, timeout=10)
            resp.raise_for_status()
            latest = resp.json()

            tag = latest.get("tag_name", "")
            latest_version = self._normalize_ver(tag)
            current_norm = self._normalize_ver(self.current_version)

            body = latest.get("body") or ""
            self.release_notes = body[:4000]

            is_newer = version.parse(latest_version) > version.parse(current_norm)

            if is_newer:
                assets = latest.get("assets", [])
                url = self._pick_asset_url(assets)
                if not url:
                    self.done.emit({"status": "error", "message": "No downloadable assets found."})
                    return
                self.download_url = url
                self.done.emit({
                    "status": "new_version",
                    "latest_version": latest_version,
                    "download_url": self.download_url,
                    "notes": self.release_notes
                })
            else:
                self.done.emit({"status": "latest", "latest_version": latest_version})
        except requests.Timeout:
            self.done.emit({"status": "error", "message": "Update check timed out."})
        except requests.RequestException as e:
            self.done.emit({"status": "error", "message": f"Network error: {e}"})
        except ValueError as e:
            self.done.emit({"status": "error", "message": f"JSON parsing error: {e}"})
        except Exception as e:
            self.done.emit({"status": "error", "message": str(e)})


class UpdateDownloadThread(QThread):
    progress = pyqtSignal(int)
    done = pyqtSignal(dict)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self._abort = False

    def abort(self):
        self._abort = True

    def run(self):
        try:
            with requests.get(self.url, stream=True, timeout=10) as response:
                response.raise_for_status()
                total_length = response.headers.get('content-length')
                if total_length is None:
                    self.done.emit({"status": "error", "message": "Unable to determine file size."})
                    return

                total_length = int(total_length)
                downloaded = 0
                new_file_path = os.path.join(tempfile.gettempdir(), "adb_manager_update.new")

                with open(new_file_path, "wb") as file:
                    for data in response.iter_content(chunk_size=64 * 1024):
                        if self._abort:
                            self.done.emit({"status": "error", "message": "Download cancelled."})
                            try:
                                os.remove(new_file_path)
                            except Exception:
                                pass
                            return
                        if not data:
                            continue
                        downloaded += len(data)
                        file.write(data)
                        self.progress.emit(int(100 * downloaded / total_length))

            self.done.emit({"status": "success", "file_path": new_file_path})
        except requests.Timeout:
            self.done.emit({"status": "error", "message": "Download timed out."})
        except requests.RequestException as e:
            self.done.emit({"status": "error", "message": f"Network error: {e}"})
        except Exception as e:
            self.done.emit({"status": "error", "message": str(e)})
