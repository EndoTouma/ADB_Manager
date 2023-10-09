from PyQt5.QtWidgets import QMessageBox, QCheckBox


class DeviceManager:
    
    @staticmethod
    def add_device(devices, device_checkboxes, devices_grid, new_device_entry, remove_device_combo_box,
                   save_data_method):
        try:
            new_device = new_device_entry.text()
            if new_device and new_device not in devices:
                devices.append(new_device)
                new_checkbox = QCheckBox(new_device)
                device_checkboxes.append(new_checkbox)
                row = (len(device_checkboxes) - 1) // 4
                col = (len(device_checkboxes) - 1) % 4
                devices_grid.addWidget(new_checkbox, row, col)
                new_device_entry.clear()
                remove_device_combo_box.addItem(new_device)
                save_data_method()
                QMessageBox.information(None, "Success", "Device added successfully!")
            else:
                QMessageBox.warning(None, "Warning", "Device is empty or already exists!")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}")
    
    @staticmethod
    def remove_device(devices, device_checkboxes, devices_grid, remove_device_combo_box, save_data_method):
        try:
            remove_device = remove_device_combo_box.currentText()
            if remove_device and remove_device in devices:
                device_index = devices.index(remove_device)
                devices.remove(remove_device)
                remove_device_combo_box.removeItem(device_index)
                removed_checkbox = device_checkboxes.pop(device_index)
                devices_grid.removeWidget(removed_checkbox)
                removed_checkbox.deleteLater()
                save_data_method()
                QMessageBox.information(None, "Success", "Device removed successfully!")
            else:
                QMessageBox.warning(None, "Warning", "Device doesn't exist or input is empty!")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}")