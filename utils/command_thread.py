from PyQt6.QtCore import QThread, pyqtSignal
from utils.apk_manager import APKManager


class CommandThread(QThread):
    command_finished = pyqtSignal(str, str, bool)
    command_output = pyqtSignal(str)

    def __init__(self, device, command, reinstall=False, parent=None):
        super().__init__(parent)
        self.device = device
        self.command = command
        self.reinstall = reinstall

    def run(self):
        try:
            if "install" in self.command:
                apk_path = self.command.split(" ")[1]
                output = APKManager.install(self.device, apk_path, self.reinstall)
            elif "uninstall" in self.command:
                package_name = self.command.split(" ")[1]
                output = APKManager.uninstall(self.device, package_name)
            self.command_output.emit(output)
            self.command_finished.emit(self.device, self.command, True)
        except Exception as e:
            self.command_output.emit(str(e))
            self.command_finished.emit(self.device, self.command, False)
