from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel,
    QCheckBox, QLineEdit, QTabWidget, QGridLayout,QMessageBox, QComboBox,QFrame
)
from utils.adb_executor import execute_adb_command
from utils.data_management import save_data, load_data
from PyQt5.QtCore import Qt


class ADBController(QWidget):
    def __init__(self):
        super().__init__()

        # Load saved data
        self.load_data_method()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        tabs = QTabWidget()
        self.device_checkboxes = []

        tab_control = QWidget()
        tab_manage = QWidget()
        tab_about = QWidget()

        tabs.addTab(tab_control, "Control")
        tabs.addTab(tab_manage, "Manage")
        tabs.addTab(tab_about, "About")

        # Control Tab
        layout_control = QVBoxLayout(tab_control)

        devices_label = QLabel("Available devices: ")
        devices_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.devices_grid = QGridLayout()
        self.device_checkboxes = [QCheckBox(device) for device in self.devices]

        for index, checkbox in enumerate(self.device_checkboxes):
            row = index // 4
            col = index % 4
            self.devices_grid.addWidget(checkbox, row, col)

        execute_button = QPushButton("Execute")
        execute_button.clicked.connect(self.execute_adb_command_method)

        self.command_combobox = QComboBox()
        self.command_combobox.setEditable(False)
        self.command_combobox.addItems(self.commands)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        layout_control.addWidget(devices_label)
        layout_control.addLayout(self.devices_grid)
        command_label = QLabel("Command: ")
        command_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout_control.addWidget(command_label)
        layout_control.addWidget(self.command_combobox)
        layout_control.addWidget(execute_button)
        output_label = QLabel("Output: ")
        output_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout_control.addWidget(output_label)

        # Adding the text output widget
        layout_control.addWidget(self.output_text)

        # Manage Tab
        manage_tabs = QTabWidget(tab_manage)
        tab_manage_devices = QWidget()
        tab_manage_commands = QWidget()
        manage_tabs.addTab(tab_manage_devices, "Manage Devices")
        manage_tabs.addTab(tab_manage_commands, "Manage Commands")

        # Manage Devices Tab
        layout_manage_devices = QVBoxLayout(tab_manage_devices)

        # Add Device
        add_device_layout = QHBoxLayout()
        self.new_device_entry = QLineEdit()
        self.new_device_entry.setFixedWidth(200)
        add_device_button = QPushButton("Add Device")
        add_device_button.setFixedWidth(100)
        add_device_button.setFixedHeight(20)
        add_device_button.clicked.connect(self.add_device)
        add_device_layout.addWidget(self.new_device_entry)
        add_device_layout.addWidget(add_device_button)

        # Remove Device
        remove_device_layout = QHBoxLayout()
        self.remove_device_combo_box = QComboBox()
        self.remove_device_combo_box.setFixedWidth(200)
        self.remove_device_combo_box.addItems(self.devices)
        remove_device_button = QPushButton("Remove Device")
        remove_device_button.setFixedWidth(100)
        remove_device_button.setFixedHeight(20)
        remove_device_button.clicked.connect(self.remove_device)
        remove_device_layout.addWidget(self.remove_device_combo_box)
        remove_device_layout.addWidget(remove_device_button)

        layout_manage_devices.addLayout(add_device_layout)
        layout_manage_devices.addLayout(remove_device_layout)

        # Manage Commands Tab
        layout_manage_commands = QVBoxLayout(tab_manage_commands)

        # Add Command
        add_command_layout = QHBoxLayout()
        self.new_command_entry = QLineEdit()
        self.new_command_entry.setFixedWidth(300)

        add_command_button = QPushButton("Add Command")
        add_command_button.clicked.connect(self.add_command)
        add_command_layout.addWidget(self.new_command_entry)
        add_command_layout.addWidget(add_command_button)

        # Remove Command
        remove_command_layout = QHBoxLayout()
        self.remove_command_combobox = QComboBox()
        self.remove_command_combobox.setFixedWidth(300)
        self.remove_command_combobox.addItems(self.commands)
        remove_command_button = QPushButton("Remove Command")
        remove_command_button.clicked.connect(self.remove_command)
        remove_command_layout.addWidget(self.remove_command_combobox)
        remove_command_layout.addWidget(remove_command_button)

        layout_manage_commands.addLayout(add_command_layout)
        layout_manage_commands.addLayout(remove_command_layout)

        # About Tab
        layout_about = QVBoxLayout(tab_about)

        # App Name
        app_name_label = QLabel("ADB Controller")
        app_name_font = app_name_label.font()
        app_name_font.setPointSize(16)
        app_name_font.setBold(True)
        app_name_label.setFont(app_name_font)
        layout_about.addWidget(app_name_label)

        # App Version
        app_version_label = QLabel("Version: 0.0.1")
        layout_about.addWidget(app_version_label)

        # Horizontal Line
        horizontal_line = QFrame()
        horizontal_line.setFrameShape(QFrame.HLine)
        horizontal_line.setFrameShadow(QFrame.Sunken)
        layout_about.addWidget(horizontal_line)

        # Author Label
        author_label = QLabel("Author: Eugene Vervai")
        layout_about.addWidget(author_label)

        # Contact
        contact_label = QLabel("Contact: delspin1@gmail.com")
        layout_about.addWidget(contact_label)

        # License
        license_label = QLabel("License: MIT License")
        layout_about.addWidget(license_label)

        # Description
        description_label = QLabel("Description:")
        layout_about.addWidget(description_label)

        description_text = QTextEdit()
        description_text.setText(
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
        description_text.setReadOnly(True)
        layout_about.addWidget(description_text)

        # Adjust spacings, alignments, etc.
        layout_about.setAlignment(Qt.AlignTop)

        layout.addWidget(tabs)
        self.setLayout(layout)

        self.setWindowTitle("ADB Controller")
        self.setGeometry(100, 100, 500, 550)
        self.show()
    
    def execute_adb_command_method(self):
        try:
            selected_command = self.command_combobox.currentText()
            selected_devices = [checkbox.text() for checkbox in self.device_checkboxes if checkbox.isChecked()]
            for device in selected_devices:
                execute_adb_command(device, selected_command, self.output_text)
        except Exception as e:
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle("Ошибка")
            error_dialog.setText("Произошла ошибка во время выполнения ADB команды")
            error_dialog.setInformativeText(str(e))
            error_dialog.addButton(QMessageBox.Ok)
            error_dialog.exec()

    def show_message(self, title, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()
    
    def add_device(self):
        try:
            new_device = self.new_device_entry.text()
            if new_device and new_device not in self.devices:
                self.devices.append(new_device)
                new_checkbox = QCheckBox(new_device)
                self.device_checkboxes.append(new_checkbox)
                row = (len(self.device_checkboxes) - 1) // 4
                col = (len(self.device_checkboxes) - 1) % 4
                self.devices_grid.addWidget(new_checkbox, row, col)
                self.new_device_entry.clear()
                self.remove_device_combo_box.addItem(new_device)
                self.save_data_method()
                QMessageBox.information(self, "Success", "Device added successfully!")
            else:
                QMessageBox.warning(self, "Warning", "Device is empty or already exists!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def remove_device(self):
        try:
            remove_device = self.remove_device_combo_box.currentText()
            if remove_device and remove_device in self.devices:
                device_index = self.devices.index(remove_device)
                self.devices.remove(remove_device)
                self.remove_device_combo_box.removeItem(device_index)
                removed_checkbox = self.device_checkboxes.pop(device_index)
                self.devices_grid.removeWidget(removed_checkbox)
                removed_checkbox.deleteLater()
                self.save_data_method()
                QMessageBox.information(self, "Success", "Device removed successfully!")
            else:
                QMessageBox.warning(self, "Warning", "Device doesn't exist or input is empty!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def add_command(self):
        try:
            new_command = self.new_command_entry.text()
            if new_command and new_command not in self.commands:
                self.commands.append(new_command)
                self.new_command_entry.clear()
                self.save_data_method()
                self.command_combobox.addItem(new_command)
                self.remove_command_combobox.addItem(new_command)
                QMessageBox.information(self, "Success", "Command added successfully!")
            else:
                QMessageBox.warning(self, "Warning", "Command is empty or already exists!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def remove_command(self):
        try:
            remove_command = self.remove_command_combobox.currentText()
            if remove_command and remove_command in self.commands:
                self.commands.remove(remove_command)
                index_to_remove = self.command_combobox.findText(remove_command)
                self.command_combobox.removeItem(index_to_remove)
                index_to_remove_remove_section = self.remove_command_combobox.findText(remove_command)
                self.remove_command_combobox.removeItem(index_to_remove_remove_section)
                self.save_data_method()
                QMessageBox.information(self, "Success", "Command successfully removed!")
            else:
                QMessageBox.warning(self, "Error", "Command doesn't exist!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def save_data_method(self):
        save_data(self.devices, self.commands)

    def load_data_method(self):
        self.devices, self.commands = load_data()