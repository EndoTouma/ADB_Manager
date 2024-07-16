import subprocess
import time
import chardet
from PyQt6.QtWidgets import QMessageBox


def decode_output(output_bytes):
    detected_encoding = chardet.detect(output_bytes)['encoding'] or 'utf-8'
    return output_bytes.decode(detected_encoding, errors='replace')


def execute_adb_command(device, command, output_text_widget):
    execution_time = 0
    try:
        output_text_widget.append(f"\n<strong>Executing</strong> '{command}' on device: {device}\n")
        
        if command.startswith("connect"):
            adb_command = f"adb {command} {device}"
        elif command.startswith("disconnect"):
            adb_command = f"adb {command} {device}"
        else:
            adb_command = f"adb -s {device} {command}"
        
        start_time = time.time()
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        process = subprocess.Popen(
            adb_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW
        )
        output, error = process.communicate()
        
        end_time = time.time()
        execution_time = round(end_time - start_time, 2)
        
        message = error if error else output
        output_text_widget.append(f"<strong>Result</strong>: {decode_output(message)}\n")
    
    except Exception as e:
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText("An error occurred while attempting to execute the ADB command.")
        error_dialog.setInformativeText(str(e))
        error_dialog.addButton(QMessageBox.StandardButton.Ok)
        error_dialog.exec()
    
    return execution_time


def execute_adb_commands(device, command):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        result = subprocess.run(['adb', '-s', device] + command.split(), capture_output=True, text=True,
                                startupinfo=startupinfo)
        if result.returncode == 0:
            return result.stdout
        else:
            raise Exception(result.stderr)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error executing command: {str(e)}")
