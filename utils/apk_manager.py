from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from typing import Tuple


def _startupinfo():
    if sys.platform.startswith("win"):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return si
    return None


def _creationflags_no_window() -> int:
    if sys.platform.startswith("win"):
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return 0


def _run(args: list[str], timeout: float = 600.0) -> Tuple[int, str, str]:
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        startupinfo=_startupinfo(),
        creationflags=_creationflags_no_window(),
    )
    try:
        out_b, err_b = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out_b, err_b = proc.communicate()

    out = (out_b or b"").decode("utf-8", errors="replace")
    err = (err_b or b"").decode("utf-8", errors="replace")
    return proc.returncode, out, err


class APKManager:
    @staticmethod
    def install(device: str, apk_path: str, reinstall: bool = False) -> str:
        device = (device or "").strip()
        path = Path(apk_path).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"APK not found: {path}")

        remote = f"/data/local/tmp/{path.name}"
        rc_p, out_p, err_p = _run(["adb", "-s", device, "push", str(path), remote])
        if rc_p != 0:
            raise RuntimeError(f"adb push failed:\n{out_p}\n{err_p}")

        pm_args = ["adb", "-s", device, "shell", "pm", "install"]
        if reinstall:
            pm_args.append("-r")
        pm_args.append(remote)

        rc_i, out_i, err_i = _run(pm_args)

        _run(["adb", "-s", device, "shell", "rm", "-f", remote])

        if rc_i != 0:
            raise RuntimeError(f"pm install failed:\n{out_i}\n{err_i}")

        return out_i or err_i or "Install OK (via push + pm)"

    @staticmethod
    def uninstall(device: str, package_name: str, keep_data: bool = False) -> str:
        device = (device or "").strip()
        package_name = (package_name or "").strip()
        if not package_name:
            raise ValueError("Package name is empty")

        pm_args = ["adb", "-s", device, "shell", "pm", "uninstall"]
        if keep_data:
            pm_args.append("-k")
        pm_args.append(package_name)

        rc, out, err = _run(pm_args)
        if rc != 0:
            raise RuntimeError(f"pm uninstall failed:\n{out}\n{err}")

        return out or err or "Uninstall OK (pm)"