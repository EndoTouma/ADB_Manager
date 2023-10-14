from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtCore import Qt

from utils.adb_executor import execute_adb_command


class ControlTab(QWidget):
    BUTTON_WIDTH = 150
    BUTTON_HEIGHT = 23
    SMALL_BUTTON_WIDTH = 150
    SMALL_BUTTON_HEIGHT = 23
    
    def __init__(self, devices, commands):
        """Initialize ControlTab widget with specified devices and commands."""
        super().__init__()
        self.devices = devices
        self.commands = commands
        self.device_checkboxes = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout_control = QVBoxLayout(self)
        
        # Create UI groups and add them to the main layout.
        devices_group = self.create_group("Available Devices", self.devices_ui())
        commands_group = self.create_group("ADB Commands", self.commands_ui())
        output_group = self.create_group("Output", self.output_ui())
        
        layout_control.addWidget(devices_group)
        layout_control.addWidget(commands_group)
        layout_control.addWidget(output_group)
    
    def create_group(self, title, layout):
        """Create a UI group with a given title and layout."""
        group = QGroupBox(title)
        group.setLayout(layout)
        return group
    
    def devices_ui(self):
        """Create and configure UI for device management."""
        layout = QVBoxLayout()
        self.devices.sort()
        self.devices_grid = QGridLayout()
        self.device_checkboxes = [QCheckBox(device) for device in self.devices]
        
        num_rows = (len(self.device_checkboxes) + 3) // 4  # Ceiling division
        
        # Distribute checkboxes across the grid.
        for index, checkbox in enumerate(self.device_checkboxes):
            col = index // num_rows
            row = index % num_rows
            self.devices_grid.addWidget(checkbox, row, col)
        
        layout.addLayout(self.devices_grid)
        
        # Create and add control buttons.
        buttons = [
            ("Select All", self.select_all_devices),
            ("Add Device", self.add_device),
            ("Delete Device", self.delete_device)
        ]
        button_layout = self.create_button_layout(buttons)
        layout.addLayout(button_layout)
        
        self.apply_standard_margins_and_spacing(layout)
        return layout
    
    def commands_ui(self):
        """Create and configure UI for command management."""
        layout = QVBoxLayout()
        self.command_combobox = QComboBox()
        self.command_combobox.setEditable(False)
        self.command_combobox.addItems(self.commands)
        self.command_combobox.setCurrentIndex(-1)
        self.command_combobox.setFixedWidth(550)
        
        layout.addWidget(self.command_combobox)
        
        # Create and add control buttons.
        buttons = [
            ("Execute", self.execute_adb_command_method),
            ("Add Command", self.add_command),
            ("Delete Command", self.delete_command)
        ]
        button_layout = self.create_button_layout(buttons)
        layout.addLayout(button_layout)
        
        self.apply_standard_margins_and_spacing(layout)
        return layout
    
    def output_ui(self):
        """Create and configure UI for output display."""
        layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)
        self.apply_standard_margins_and_spacing(layout)
        return layout
    
    def create_button_layout(self, buttons):
        """Create a button layout based on a list of pairs (button text, callback function)."""
        button_layout = QHBoxLayout()
        for text, callback in buttons:
            button = self.create_button(text, callback)
            button.setFixedSize(self.SMALL_BUTTON_WIDTH, self.SMALL_BUTTON_HEIGHT)
            button_layout.addWidget(button)
        return button_layout
    
    def create_button(self, text, callback, width=None, height=None):
        """Create a button with specified text and callback function."""
        button = QPushButton(text)
        button.setFixedSize(width if width is not None else self.BUTTON_WIDTH,
                            height if height is not None else self.BUTTON_HEIGHT)
        button.clicked.connect(callback)
        return button
    
    def apply_standard_margins_and_spacing(self, layout):
        """
        Apply standard spacing between widgets in the layout.

        :param layout: The layout to which the spacing is applied.
        """
        layout.setSpacing(10)
    
    def add_device(self):
        """
        Add a new device by IP and Port after validating the input.
        If the input format is wrong, show a warning message.
        """
        text, ok = QInputDialog.getText(self, "Add Device", "Enter IP and Port (format: IP:Port):")
        if ok and text:
            try:
                ip, port = text.split(":")
            except ValueError:
                QMessageBox.warning(self, "Invalid input", "Please use format: IP:Port.")
                return
            
            # Appending the new device and updating the grid layout.
            self.devices.append(f"{ip}:{port}")
            self.update_device_grid(self.devices)
    
    def execute_adb_command_method(self):
        """
        Execute the selected ADB command on the selected devices.
        Append the output and any errors to the output_text QTextEdit.
        """
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.output_text.append(f"NEW COMMAND: {current_time}\n")
        
        selected_command = self.command_combobox.currentText()
        selected_devices = [checkbox.text() for checkbox in self.device_checkboxes if checkbox.isChecked()]
        
        if not selected_command or not selected_devices:
            QMessageBox.warning(None, "Warning", "Please select at least one device and a command to execute.")
            return
        
        total_execution_time = 0
        for device in selected_devices:
            try:
                total_execution_time += execute_adb_command(device, selected_command, self.output_text)
            except Exception as e:
                self.output_text.append(f"ERROR executing on {device}: {str(e)}\n")
        
        self.output_text.append(f"Total execution time: {total_execution_time} seconds\n")
        self.output_text.append("-" * 120 + "\n")
    
    def update_device_grid(self, devices, remove_device_combo_box=None):
        """
        Update the grid layout which shows devices checkboxes.

        :param devices: List of devices to be shown on the grid.
        :param remove_device_combo_box: (Optional) QComboBox that might need updating with the new device list.
        """
        # Clearing existing widgets in the layout.
        for i in reversed(range(self.devices_grid.count())):
            widget_to_remove = self.devices_grid.itemAt(i).widget()
            self.devices_grid.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)
            widget_to_remove.deleteLater()
        
        devices.sort()
        self.device_checkboxes = [QCheckBox(device) for device in devices]
        
        num_rows = len(self.device_checkboxes) // 4 + (len(self.device_checkboxes) % 4 != 0)
        
        # Adding checkboxes to the layout.
        for index, checkbox in enumerate(self.device_checkboxes):
            col = index // num_rows
            row = index % num_rows
            self.devices_grid.addWidget(checkbox, row, col)
        
        # Updating the remove_device_combo_box if provided.
        if remove_device_combo_box:
            remove_device_combo_box.clear()
            remove_device_combo_box.addItems(devices)
            remove_device_combo_box.setCurrentIndex(-1)
    
    def delete_device(self):
        """
        Open a dialog for the user to select and delete devices.
        Update the device grid upon deletion.
        """
        dialog = DeleteDeviceDialog(self.devices, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            devices_to_delete = dialog.get_selected_devices()
            self.devices = [dev for dev in self.devices if dev not in devices_to_delete]
            self.update_device_grid(self.devices)
    
    def select_all_devices(self):
        """
        Toggles the selection of all device checkboxes. If all are selected,
        all checkboxes will be deselected, and vice versa.
        """
        all_selected = all(cb.isChecked() for cb in self.device_checkboxes)
        for checkbox in self.device_checkboxes:
            checkbox.setChecked(not all_selected)
    
    def add_command(self):
        """
        Open a dialog to add a new ADB command.
        Add the command to the combobox and commands list if the input is valid.
        """
        dialog = QInputDialog(self)
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setLabelText("Enter ADB Command:")
        dialog.setWindowTitle("Add Command")
        dialog.resize(400, 200)
        
        ok = dialog.exec_()
        text = dialog.textValue()
        
        if ok and text:
            self.commands.append(text)
            self.command_combobox.addItem(text)
    
    def delete_command(self):
        """
        Open a dialog for the user to select and delete ADB commands.
        Update the command combobox upon deletion.
        """
        dialog = DeleteCommandDialog(self.commands, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            commands_to_delete = dialog.get_selected_commands()
            self.commands = [cmd for cmd in self.commands if cmd not in commands_to_delete]
            self.command_combobox.clear()
            self.command_combobox.addItems(self.commands)


class DeleteDeviceDialog(QDialog):
    def __init__(self, devices, parent=None):
        """
        Initialize the DeleteDeviceDialog.

        :param devices: a list of device names.
        :param parent: parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Delete Devices")

        self.devices = devices
        self.checkboxes = []

        layout = QVBoxLayout(self)

        self.setup_devices_layout(layout)
        self.setup_buttons(layout)

        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

    def setup_devices_layout(self, parent_layout):
        """
        Set up the layout for device checkboxes.

        :param parent_layout: layout to which device layout is added.
        """
        devices_layout = QGridLayout()
        self.checkboxes = [QCheckBox(device) for device in self.devices]

        num_rows = len(self.checkboxes) // 4 + (len(self.checkboxes) % 4 != 0)

        for index, checkbox in enumerate(self.checkboxes):
            col = index // num_rows
            row = index % num_rows
            devices_layout.addWidget(checkbox, row, col)

        parent_layout.addLayout(devices_layout)

    def setup_buttons(self, parent_layout):
        """
        Set up the dialog buttons.

        :param parent_layout: layout to which buttons are added.
        """
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        select_all_button = QPushButton("Select All")
        select_all_button.clicked.connect(self.select_all_devices)

        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(select_all_button)
        buttons_layout.addWidget(button_box)

        parent_layout.addLayout(buttons_layout)

    def select_all_devices(self):
        """
        Check or uncheck all device checkboxes based on the current state.
        """
        all_selected = all(checkbox.isChecked() for checkbox in self.checkboxes)

        for checkbox in self.checkboxes:
            checkbox.setChecked(not all_selected)

    def get_selected_devices(self):
        """
        Get all selected devices.

        :return: a list of selected device names.
        """
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]


class DeleteCommandDialog(QDialog):
    def __init__(self, commands, parent=None):
        """
        Initialize the DeleteCommandDialog.

        :param commands: a list of command names.
        :param parent: parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Delete Commands")
        
        self.commands = commands
        self.checkboxes = []
        
        layout = QVBoxLayout(self)
        
        self.setup_scroll_area(layout)
        self.setup_buttons(layout)
        
        self.setLayout(layout)
        
        self.setMinimumWidth(400)  # Set the minimum width of the window to 400 pixels
        self.setMaximumWidth(self.calculate_max_checkbox_width())  # Set the max width based on the content
    
    def setup_scroll_area(self, parent_layout):
        """
        Set up the scroll area for command checkboxes.

        :param parent_layout: layout to which the scroll area is added.
        """
        scroll_area = QScrollArea(self)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        parent_layout.addWidget(scroll_area)
        
        self.checkboxes = [QCheckBox(command) for command in self.commands]
        
        max_width = self.calculate_max_checkbox_width()
        
        max_window_width = 500
        if max_width > max_window_width:
            max_width = max_window_width
        
        self.setMaximumWidth(max_width)
        
        for checkbox in self.checkboxes:
            checkbox.setFixedHeight(20)
            scroll_layout.addWidget(checkbox)
    
    def calculate_max_checkbox_width(self):
        """
        Calculate the maximum width needed for the checkboxes based on their label texts.

        :return: max width.
        """
        max_width = 350
        metrics = QFontMetrics(self.font())
        for checkbox in self.checkboxes:
            text_width = metrics.boundingRect(checkbox.text()).width()
            max_width = max(max_width, text_width)
        max_width += 50  # Adding some padding
        return max_width
    
    def setup_buttons(self, parent_layout):
        """
        Set up the dialog buttons.

        :param parent_layout: layout to which buttons are added.
        """
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        select_all_button = QPushButton("Select All")
        select_all_button.clicked.connect(self.select_all_commands)
        
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(select_all_button)
        buttons_layout.addWidget(button_box)
        
        parent_layout.addLayout(buttons_layout)
        parent_layout.setAlignment(button_box, Qt.AlignRight)
    
    def select_all_commands(self):
        """
        Check or uncheck all command checkboxes based on the current state.
        """
        all_selected = all(checkbox.isChecked() for checkbox in self.checkboxes)
        
        for checkbox in self.checkboxes:
            checkbox.setChecked(not all_selected)
    
    def get_selected_commands(self):
        """
        Get all selected commands.

        :return: a list of selected command names.
        """
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]