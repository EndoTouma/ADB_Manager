import subprocess
from PyQt5.QtWidgets import QMessageBox

def execute_adb_command(device, command, output_text_widget):
    try:
        output_text_widget.append(f"\nExecuting '{command}' on device: {device}\n")
        adb_command = f"adb -s {device} {command}"
        process = subprocess.Popen(adb_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        output_text_widget.append(f"Output: {output.decode()}\n")
        output_text_widget.append(f"Error: {error.decode()}\n")
    except Exception as e:
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Ошибка")
        error_dialog.setText("Произошла ошибка во время выполнения ADB команды")
        error_dialog.setInformativeText(str(e))
        error_dialog.addButton(QMessageBox.Ok)
        error_dialog.exec()