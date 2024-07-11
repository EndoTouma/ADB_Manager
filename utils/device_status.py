import subprocess
from PyQt6.QtGui import QPalette, QColor


def update_device_status_ui(checkbox, status):
    palette = QPalette()
    if status == "device":
        palette.setColor(QPalette.ColorRole.WindowText, QColor('green'))
    elif status == "offline":
        palette.setColor(QPalette.ColorRole.WindowText, QColor('red'))
    else:
        palette.setColor(QPalette.ColorRole.WindowText, QColor('black'))
    checkbox.setPalette(palette)


def get_device_status():
    device_status = {}
    active_devices = []
    result = subprocess.run(['adb', 'devices', '-l'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    lines = result.split('\n')
    for line in lines[1:]:
        if line.strip():
            parts = line.split()
            device_name = parts[0]
            device_state = parts[1]
            device_status[device_name] = device_state
            active_devices.append(device_name)
    return device_status, active_devices
