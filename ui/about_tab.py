from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QTextEdit, QGroupBox


class AboutTab(QWidget):
    """
    A tab widget that displays information about the application.
    """
    APP_INFO_LABELS = [
        ("ADB Controller", 12, True),
        ("Version: 0.5.0", 9, False),
        ("Author: Eugene Vervai", 9, False),
        ("Contact: delspin1@gmail.com", 9, False),
        ("License: MIT License", 9, False)
    ]

    DESCRIPTION_TEXT = (
        "ADB Controller is a user-friendly application designed to facilitate "
        "the management and control of devices via Android Debug Bridge (ADB) "
        "commands. The app allows users to easily add and remove devices and "
        "commands to suit their specific requirements, providing an intuitive "
        "graphical user interface to execute various ADB commands without the need "
        "for manual command line input.\n\n"
        "Key Features:\n"
        "    - Manage and execute ADB commands on multiple devices simultaneously.\n"
        "    - Add and remove devices and commands through a straightforward UI.\n"
        "    - Monitor command execution outputs conveniently within the application.\n\n"
        "Whether you are a developer, tester, or tech enthusiast, ADB Controller "
        "aims to enhance your workflow by providing a convenient interface for "
        "managing devices and executing ADB commands effortlessly."
    )

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """
        Initialize UI components.
        """
        layout_about = QVBoxLayout(self)

        app_info_group = self.create_group("App Information", self.app_info_ui())
        layout_about.addWidget(app_info_group)

        description_group = self.create_group("Description", self.description_ui())
        layout_about.addWidget(description_group)

        layout_about.setAlignment(Qt.AlignTop)

    def create_group(self, title, layout):
        """
        Create a QGroupBox with a specified title and layout.

        Parameters:
            title (str): The title of the group box.
            layout (QLayout): The layout to set on the group box.

        Returns:
            QGroupBox: The configured group box.
        """
        group = QGroupBox(title)
        group.setLayout(layout)
        layout.setSpacing(10)  # Consistent spacing
        layout.setContentsMargins(10, 10, 10, 10)  # Consistent margins
        return group

    def create_label(self, text, size, bold):
        """
        Create a QLabel with specified text and font properties.

        Parameters:
            text (str): The text of the label.
            size (int): The size of the font.
            bold (bool): Bold font flag.

        Returns:
            QLabel: The configured label.
        """
        label = QLabel(text)
        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)
        label.setFont(font)
        return label

    def app_info_ui(self):
        """
        Create a layout with application information labels.

        Returns:
            QVBoxLayout: The layout containing app info labels.
        """
        layout = QVBoxLayout()

        for text, size, bold in self.APP_INFO_LABELS:
            label = self.create_label(text, size, bold)
            layout.addWidget(label)

        horizontal_line = QFrame()
        horizontal_line.setFrameShape(QFrame.HLine)
        horizontal_line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(horizontal_line)

        return layout

    def description_ui(self):
        """
        Create a layout with a description QTextEdit widget.

        Returns:
            QVBoxLayout: The layout containing the description text.
        """
        layout = QVBoxLayout()

        description_text = QTextEdit()
        description_text.setText(self.DESCRIPTION_TEXT)
        description_text.setReadOnly(True)

        layout.addWidget(description_text)

        return layout
