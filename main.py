import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon  # Добавляем необходимый импорт
from ui.main_windows import ADBController

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('adb.svg'))
    ex = ADBController()
    sys.exit(app.exec_())