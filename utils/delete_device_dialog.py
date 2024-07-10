from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox


class DeleteDeviceDialog(QDialog):
    def __init__(self, devices, device_statuses, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Delete Devices")
        self.devices = devices
        self.device_statuses = device_statuses
        self.selected_devices = []

        layout = QVBoxLayout(self)

        self.checkboxes = []
        for device in devices:
            status = device_statuses.get(device)
            checkbox = QCheckBox(device)
            if status == "offline":
                checkbox.setStyleSheet("color: red;")
            else:
                checkbox.setStyleSheet("color: green;")
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_selected_devices(self):
        return [checkbox.text() for checkbox in self.checkboxes if checkbox.isChecked()]
