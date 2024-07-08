import requests
import logging
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QTextEdit, QGroupBox, QPushButton, QMessageBox, \
    QProgressDialog
from packaging import version


class AboutTab(QWidget):
    APP_INFO_LABELS = [
        ("ADB Controller", 12, True),
        ("Version: 2.0.0-rc.3", 9, False),
        ("Author: Eugene Vervai", 9, False),
        ("Contact: delspin1@gmail.com", 9, False),
        ("License: MIT License", 9, False)
    ]
    
    DESCRIPTION_TEXT = (
        "ADB Controller is an easy-to-use application designed to help you manage and control "
        "your devices using Android Debug Bridge (ADB) commands. With this app, you can effortlessly "
        "add and remove devices and commands to fit your specific needs, all through a user-friendly "
        "interface that eliminates the need for manual command line input.\n\n"
        "Key Features:\n"
        "    - Manage and execute ADB commands on multiple devices at the same time.\n"
        "    - Add and remove devices and commands easily through a simple UI.\n"
        "    - Monitor command execution output directly within the app.\n"
        "    - Real-time log monitoring and filtering.\n\n"
        "Whether you're a developer, tester, or tech enthusiast, ADB Controller is designed to "
        "streamline your workflow by providing a convenient interface for managing devices and executing "
        "ADB commands with ease."
    )
    
    CURRENT_VERSION = "2.0.0-rc.3"  # текущая версия приложения
    REPO_API_URL = "https://api.github.com/repos/EndoTouma/ADB_Controller/releases/latest"
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout_about = QVBoxLayout(self)
        
        app_info_group = self.create_group("App Information", self.app_info_ui())
        layout_about.addWidget(app_info_group)
        
        description_group = self.create_group("Description", self.description_ui())
        layout_about.addWidget(description_group)
        
        update_button = QPushButton("Check for Updates")
        update_button.clicked.connect(self.check_for_updates)
        layout_about.addWidget(update_button)
        
        layout_about.setAlignment(Qt.AlignmentFlag.AlignTop)
    
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
    
    def description_ui(self):
        layout = QVBoxLayout()
        
        description_text = QTextEdit()
        description_text.setText(self.DESCRIPTION_TEXT)
        description_text.setReadOnly(True)
        
        layout.addWidget(description_text)
        
        return layout
    
    def check_for_updates(self):
        self.progress_dialog = QProgressDialog("Checking for updates...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowTitle("Update")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()
        
        self.update_thread = UpdateCheckThread(self.REPO_API_URL, self.CURRENT_VERSION)
        self.update_thread.progress.connect(self.progress_dialog.setValue)
        self.update_thread.finished.connect(self.on_update_check_finished)
        self.update_thread.start()
    
    def on_update_check_finished(self, result):
        self.progress_dialog.close()
        if result["status"] == "error":
            QMessageBox.critical(self, "Error", result["message"])
        elif result["status"] == "latest":
            QMessageBox.information(self, "Check for Updates", "You have the latest version.")
        elif result["status"] == "new_version":
            reply = QMessageBox.question(self, "Update Available",
                                         "A new version is available. Do you want to download and install it?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Yes:
                self.download_and_replace(result["download_url"])
    
    def is_newer_version(self, latest_version):
        is_newer = version.parse(latest_version) > version.parse(self.CURRENT_VERSION)
        print(f"Current version: {self.CURRENT_VERSION}, Latest version: {latest_version}, Is newer: {is_newer}")
        return is_newer
    
    def download_and_replace(self, url):
        self.progress_dialog = QProgressDialog("Downloading update...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowTitle("Update")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()
        
        self.download_thread = UpdateDownloadThread(url)
        self.download_thread.progress.connect(self.progress_dialog.setValue)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()
    
    def on_download_finished(self, result):
        self.progress_dialog.close()
        if result["status"] == "error":
            QMessageBox.critical(self, "Error", result["message"])
        else:
            QMessageBox.information(self, "Update", "New version downloaded. Please restart the application to update.")


class UpdateCheckThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    
    def __init__(self, api_url, current_version):
        super().__init__()
        self.api_url = api_url
        self.current_version = current_version
    
    def run(self):
        try:
            self.progress.emit(10)
            response = requests.get(self.api_url)
            response.raise_for_status()
            self.progress.emit(50)
            latest_release = response.json()
            latest_version = latest_release["tag_name"]
            
            is_newer = version.parse(latest_version) > version.parse(self.current_version)
            print(f"Current version: {self.current_version}, Latest version: {latest_version}, Is newer: {is_newer}")
            
            if is_newer:
                download_url = latest_release["assets"][0]["browser_download_url"]
                self.finished.emit({"status": "new_version", "download_url": download_url})
            else:
                self.finished.emit({"status": "latest"})
        except requests.RequestException as e:
            self.finished.emit({"status": "error", "message": str(e)})


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
            
            with open("ADB_Controller.exe", "wb") as file:
                for data in response.iter_content(chunk_size=4096):
                    downloaded += len(data)
                    file.write(data)
                    self.progress.emit(int(100 * downloaded / total_length))
            
            self.finished.emit({"status": "success"})
        except requests.RequestException as e:
            self.finished.emit({"status": "error", "message": str(e)})