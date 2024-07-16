import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_windows import ADBManager
from utils.data_management import DataManager
import resources.icons_rc

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(':/adb.ico'))
    
    # Загрузка данных об устройствах и командах
    devices, commands = DataManager.load_data()
    
    # Загрузка токена и идентификатора чата
    token, chat_id = DataManager.load_credentials()
    
    app.setStyle("WindowsVista")
    
    ex = ADBManager(devices, commands, token, chat_id)
    ex.setWindowIcon(QIcon(':/adb.ico'))
    
    sys.exit(app.exec())
