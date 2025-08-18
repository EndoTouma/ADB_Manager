import subprocess
from PyQt6.QtCore import QThread, pyqtSignal


class LogcatThread(QThread):
    logcat_output = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, device: str, log_level: str = "V", output_file: str | None = None):
        super().__init__()
        self.device = device
        self.log_level = (log_level or "V").strip().upper()  # 'V','D','I','W','E','F'
        self.output_file = output_file
        self._running = False
        self._proc: subprocess.Popen | None = None

    def run(self):
        self._running = True

        cmd = ["adb", "-s", self.device, "logcat", f"*:{self.log_level}"]

        try:
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )

            if self.output_file:
                with open(self.output_file, "w", encoding="utf-8", newline="") as f:
                    for line in self._iter_lines():
                        f.write(line)
            else:
                for line in self._iter_lines():
                    self.logcat_output.emit(line)

        finally:
            if self._proc:
                try:
                    if self._proc.poll() is None:
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