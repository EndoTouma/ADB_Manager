import subprocess
from PyQt6.QtCore import QThread, pyqtSignal


class LogcatThread(QThread):
    logcat_output = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, device, log_level="V", output_file=None):
        super().__init__()
        self.device = device
        self.running = True
        self.output_file = output_file
        self.log_level = log_level

    def run(self):
        process = subprocess.Popen(
            ['adb', '-s', self.device, 'logcat', f'*:{self.log_level}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if self.output_file:
            with open(self.output_file, 'w') as file:
                while self.running:
                    output = process.stdout.readline().decode('utf-8')
                    if output:
                        file.write(output)
        else:
            while self.running:
                output = process.stdout.readline().decode('utf-8')
                if output:
                    self.logcat_output.emit(output)
        process.terminate()
        process.wait()
        self.finished.emit(self.device)

    def stop(self):
        self.running = False
