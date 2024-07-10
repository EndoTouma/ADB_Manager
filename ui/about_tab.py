from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QTextEdit, QGroupBox


class AboutTab(QWidget):
    APP_INFO_LABELS = [
        ("ADB Controller", 12, True),
        ("Version: 2.0.0-rc.6", 9, False),
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
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout_about = QVBoxLayout(self)
        
        app_info_group = self.create_group("App Information", self.app_info_ui())
        layout_about.addWidget(app_info_group)
        
        description_group = self.create_group("Description", self.description_ui())
        layout_about.addWidget(description_group)
        
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
