import os
import sys
import shutil
import requests
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox, QProgressDialog, QLabel, QHBoxLayout, \
    QGroupBox, QApplication
from packaging import version

from utils.data_management import DataManager


class SettingsTab(QWidget):
    CURRENT_VERSION = "2.0.0-rc.11"
    REPO_API_URL = "https://api.github.com/repos/EndoTouma/ADB_Controller/releases/latest"
    
    def __init__(self, devices, commands, theme, controller):
        super().__init__()
        self.devices = devices
        self.commands = commands
        self.theme = theme
        self.controller = controller
        self.is_initializing = True  # Начинаем с инициализации
        self.init_ui()
        self.is_initializing = False  # Закончили инициализацию
    
    def init_ui(self):
        layout_settings = QVBoxLayout(self)
        
        # Update block
        update_group = QGroupBox("Update Information")
        update_layout = QVBoxLayout()
        self.current_version_label = QLabel(f"Current Version: {self.CURRENT_VERSION}")
        self.latest_version_label = QLabel("Latest Version: Checking...")
        self.update_status_label = QLabel("Status: You have the latest version.")
        self.update_button = QPushButton("Update")
        self.update_button.setEnabled(False)
        self.update_button.clicked.connect(self.update_application)
        update_layout.addWidget(self.current_version_label)
        update_layout.addWidget(self.latest_version_label)
        update_layout.addWidget(self.update_status_label)
        update_layout.addWidget(self.update_button)
        update_group.setLayout(update_layout)
        layout_settings.addWidget(update_group)
        
        # Theme toggle block
        theme_group = QGroupBox("Application Theme")
        theme_layout = QHBoxLayout()
        self.theme_toggle = QPushButton("Toggle Dark Theme")
        self.theme_toggle.setCheckable(True)
        self.theme_toggle.setChecked(self.theme == "Fusion")
        self.update_theme_toggle_text(self.theme_toggle.isChecked())
        self.theme_toggle.toggled.connect(self.change_theme)  # Connect to the toggled signal
        theme_layout.addWidget(self.theme_toggle)
        theme_group.setLayout(theme_layout)
        layout_settings.addWidget(theme_group)
        
        layout_settings.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout_settings)
    
    def update_theme_toggle_text(self, checked):
        if checked:
            self.theme_toggle.setText("Switch to Light Theme")
        else:
            self.theme_toggle.setText("Switch to Dark Theme")
    
    def change_theme(self, checked):
        if self.is_initializing:
            return  # Не делаем ничего, если идет инициализация
        
        self.update_theme_toggle_text(checked)
        
        new_theme = "Fusion" if checked else "WindowsVista"
        if self.theme != new_theme:
            self.theme = new_theme
            QApplication.instance().setStyle(self.theme)
            DataManager.save_data(self.devices, self.commands, self.theme)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.check_for_updates()
    
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
            # Backup the current executable
            if os.path.exists(app_path):
                os.rename(app_path, old_path)
            # Move the new file to the application path
            shutil.move(new_file_path, app_path)
            QMessageBox.information(self, "Update", "New version installed. The application will now restart.")
            QTimer.singleShot(0, lambda: QApplication.quit())
            QTimer.singleShot(1000, lambda: os.execl(sys.executable, sys.executable, *sys.argv))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to replace the application file: {str(e)}")
            # If an error occurs, attempt to restore the backup
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
            self.progress.emit(10)
            response = requests.get(self.api_url)
            response.raise_for_status()
            self.progress.emit(50)
            latest_release = response.json()
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

