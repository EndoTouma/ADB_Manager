import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ui.main_windows import ADBController
from resources import icons_rc

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(':adb.ico'))
    ex = ADBController()
    ex.setWindowIcon(QIcon(':adb.ico'))
    sys.exit(app.exec_())
