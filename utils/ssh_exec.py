import os
import subprocess
import sys
import shutil


def _creationflags_no_window() -> int:
    if sys.platform.startswith("win"):
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return 0


def _find_plink() -> str:
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    local = os.path.join(base_dir, "plink.exe")
    if os.path.exists(local):
        return local
    exe = shutil.which("plink.exe")
    if exe:
        return exe
    raise FileNotFoundError(
        "Не найден plink.exe. Положите plink.exe рядом с программой или добавьте его в PATH."
    )


def _ensure_remote(remote_argv: list[str]) -> str:
    if not remote_argv or not any(part.strip() for part in remote_argv):
        raise ValueError("Пустая удалённая команда: интерактивная SSH/Plink-сессия запрещена.")
    return " ".join(part for part in remote_argv if part is not None)


def ssh_command(cfg: dict, remote_argv: list[str]) -> list[str]:
    host = cfg["host"]
    port = int(cfg.get("port", 22))
    user = (cfg.get("user") or "admin").strip()
    password = (cfg.get("password") or "").strip()
    hostkey = (cfg.get("hostkey") or "").strip()  # ← НОВОЕ поле

    remote = _ensure_remote(remote_argv)

    if password:
        plink_path = _find_plink()
        cmd = [
            plink_path,
            "-batch",
            "-P", str(port),
            "-l", user,
            "-pw", password,
        ]
        if hostkey:
            cmd += ["-hostkey", hostkey]
        cmd += [host, remote]
        return cmd

    return [
        "ssh",
        "-p", str(port),
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "BatchMode=yes",
        "-o", "NumberOfPasswordPrompts=0",
        "-o", "ConnectTimeout=10",
        f"{user}@{host}",
        remote,
    ]


def ssh_popen(cfg: dict, remote_argv: list[str]) -> subprocess.Popen:
    args = ssh_command(cfg, remote_argv)
    return subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=_creationflags_no_window(),
    )
