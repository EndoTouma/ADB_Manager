import sys, os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_windows import ADBManager
from utils.data_management import DataManager

def resource_path(rel: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, rel)
    return os.path.join(os.path.abspath("."), rel)

def _prepend_tool_dir_to_path(subdir: str):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    tool_dir = base / subdir
    if tool_dir.exists():
        os.environ["PATH"] = str(tool_dir) + os.pathsep + os.environ.get("PATH", "")

_prepend_tool_dir_to_path("adb")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("resources/adb.ico")))
    devices, commands = DataManager.load_data()
    
    app.setStyle("WindowsVista")
    
    ex = ADBManager(devices, commands)
    ex.setWindowIcon(QIcon(resource_path("resources/adb.ico")))

    
    sys.exit(app.exec())
