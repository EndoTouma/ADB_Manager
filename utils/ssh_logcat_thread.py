from PyQt6.QtCore import QThread, pyqtSignal
from utils.ssh_exec import ssh_popen

class SSHLogcatThread(QThread):
    logcat_output = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, ssh_cfg: dict, device: str, log_level: str = "V", output_file: str | None = None):
        super().__init__()
        self.ssh = ssh_cfg
        self.device = device
        self.log_level = (log_level or "V").strip().upper()
        self.output_file = output_file
        self._running = False
        self._proc = None

    def run(self):
        self._running = True
        cmd = ["adb", "-s", self.device, "logcat", f"*:{self.log_level}"]
        try:
            self._proc = ssh_popen(self.ssh, cmd)
            if self.output_file:
                with open(self.output_file, "w", encoding="utf-8", newline="") as f:
                    for line in self._iter_lines():
                        f.write(line)
            else:
                for line in self._iter_lines():
                    self.logcat_output.emit(line)
        finally:
            try:
                if self._proc and self._proc.poll() is None:
                    self._proc.terminate()
                    self._proc.wait(timeout=3)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None
            self._running = False
            self.finished.emit(self.device)

    def _iter_lines(self):
        if not self._proc or not self._proc.stdout:
            return
        for line in self._proc.stdout:
            if not self._running:
                break
            yield line

    def stop(self):
        self._running = False
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass
