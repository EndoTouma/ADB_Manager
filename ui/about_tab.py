from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox, QProgressDialog, QLabel, QGroupBox, QTextEdit, QFrame, QApplication
import os
import sys
import shutil
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

    CURRENT_VERSION = "2.0.3"
    REPO_API_URL = "https://api.github.com/repos/EndoTouma/ADB_Manager/releases/latest"

    def __init__(self):
        super().__init__()
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
        self.latest_version_label = QLabel("Latest Version: Checking...")
        self.update_status_label = QLabel("Status: You have the latest version.")
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
        self.check_for_updates()

    def check_for_updates(self):
        self.update_thread = UpdateCheckThread(self.REPO_API_URL, self.CURRENT_VERSION)
        self.update_thread.finished.connect(self.on_update_check_finished)
        self.update_thread.start()

    def on_update_check_finished(self, result):
        if result["status"] == "error":
            self.update_status_label.setText("Status: Error checking for updates.")
            QMessageBox.critical(self, "Error", result["message"])
        elif result["status"] == "latest":
            self.update_status_label.setText("Status: You have the latest version.")
            self.latest_version_label.setText(f"Latest Version: {self.CURRENT_VERSION}")
        elif result["status"] == "new_version":
            self.update_status_label.setText("Status: A new version is available.")
            self.latest_version_label.setText(f"Latest Version: {result['latest_version']}")
            self.update_button.setEnabled(True)

    def update_application(self):
        reply = QMessageBox.question(self, "Update Available",
                                     "A new version is available. Do you want to download and install it?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.Yes)
        if reply == QMessageBox.StandardButton.Yes:
            self.download_and_replace()

    def download_and_replace(self):
        self.progress_dialog = QProgressDialog("Downloading update...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowTitle("Update")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()

        self.download_thread = UpdateDownloadThread(self.update_thread.download_url)
        self.download_thread.progress.connect(self.progress_dialog.setValue)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()

    def on_download_finished(self, result):
        self.progress_dialog.close()
        if result["status"] == "error":
            QMessageBox.critical(self, "Error", result["message"])
        else:
            self.replace_and_restart(result["file_path"])

    def replace_and_restart(self, new_file_path):
        try:
            app_path = sys.argv[0]
            old_path = app_path + ".old"
            app_name = os.path.basename(app_path)
            new_app_name = app_name

            if "ADB_Controller" in app_name:
                new_app_name = app_name.replace("ADB_Controller", "ADB Manager")

            new_app_path = os.path.join(os.path.dirname(app_path), new_app_name)

            if os.path.exists(app_path):
                os.rename(app_path, old_path)
            shutil.move(new_file_path, new_app_path)
            QMessageBox.information(self, "Update",
                                    f"New version installed. The application will now restart as {new_app_name}.")
            QTimer.singleShot(0, lambda: QApplication.quit())
            QTimer.singleShot(1000, lambda: os.execl(sys.executable, new_app_path, *sys.argv))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to replace the application file: {str(e)}")
            if os.path.exists(old_path):
                os.rename(old_path, app_path)


class UpdateCheckThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)

    def __init__(self, api_url, current_version):
        super().__init__()
        self.api_url = api_url
        self.current_version = current_version
        self.download_url = ""

    def run(self):
        try:
            response = requests.get(self.api_url)
            response.raise_for_status()
            latest_release = response.json()
            print("API response:", latest_release)  # Debug log

            latest_version = latest_release["tag_name"]
            is_newer = version.parse(latest_version) > version.parse(self.current_version)

            if is_newer:
                self.download_url = latest_release["assets"][0]["browser_download_url"]
                self.finished.emit(
                    {"status": "new_version", "latest_version": latest_version, "download_url": self.download_url})
            else:
                self.finished.emit({"status": "latest"})
        except requests.RequestException as e:
            self.finished.emit({"status": "error", "message": str(e)})
        except ValueError as e:
            self.finished.emit({"status": "error", "message": f"JSON parsing error: {str(e)}"})


class UpdateDownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            total_length = response.headers.get('content-length')

            if total_length is None:
                self.finished.emit({"status": "error", "message": "Unable to determine file size."})
                return

            total_length = int(total_length)
            downloaded = 0
            new_file_path = sys.argv[0] + ".new"

            with open(new_file_path, "wb") as file:
                for data in response.iter_content(chunk_size=4096):
                    downloaded += len(data)
                    file.write(data)
                    self.progress.emit(int(100 * downloaded / total_length))

            self.finished.emit({"status": "success", "file_path": new_file_path})
        except requests.RequestException as e:
            self.finished.emit({"status": "error", "message": str(e)})
