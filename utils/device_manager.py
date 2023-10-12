from PyQt5.QtWidgets import QMessageBox


class DeviceManager:
    
    @staticmethod
    def add_device(devices, control_tab, new_device_entry, remove_device_combo_box, save_data_method):
        try:
            new_device = new_device_entry.text()
            if new_device and new_device not in devices:
                devices.append(new_device)
                control_tab.update_device_grid(devices, remove_device_combo_box)
                new_device_entry.clear()
                save_data_method()
                QMessageBox.information(None, "Success", "Device added successfully!")
            else:
                QMessageBox.warning(None, "Warning", "Device is empty or already exists!")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}")
    
    @staticmethod
    def remove_device(devices, control_tab, remove_device_combo_box, save_data_method):
        try:
            remove_device = remove_device_combo_box.currentText()
            if remove_device and remove_device in devices:
                devices.remove(remove_device)
                control_tab.update_device_grid(devices, remove_device_combo_box)
                save_data_method()
                QMessageBox.information(None, "Success", "Device removed successfully!")
            else:
                QMessageBox.warning(None, "Warning", "Device doesn't exist or input is empty!")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}")
