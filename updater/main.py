from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QLabel, QProgressBar, QVBoxLayout, QWidget


class UpdateFailed(RuntimeError):
    pass


DEFAULT_PAYLOAD_DIRNAME = "intense-rp-next"
DEFAULT_OPTIONAL_DIRNAME = "optional"


@dataclass(frozen=True)
class UpdateArgs:
    install_dir: Path
    app_pid: int
    exe_name: Optional[str]
    payload_dir: Optional[Path]


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _resolve_updater_exe_path() -> Path:
    if _is_frozen():
        return Path(sys.executable).resolve()
    return Path(__file__).resolve()


def _default_payload_dir(updater_path: Path) -> Path:
    updater_dir = updater_path.parent
    if updater_dir.name.lower() == DEFAULT_OPTIONAL_DIRNAME.lower():
        return updater_dir.parent / DEFAULT_PAYLOAD_DIRNAME
    return updater_dir / DEFAULT_PAYLOAD_DIRNAME


def _wait_for_pid(pid: int, *, timeout_s: float = 120.0) -> None:
    if pid <= 0:
        return

    if not sys.platform.startswith("win"):
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except OSError:
                return
            time.sleep(0.25)
        raise UpdateFailed("Timed out waiting for the app to exit.")

    try:
        import ctypes

        SYNCHRONIZE = 0x00100000
        handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, int(pid))
        if not handle:
            raise OSError("OpenProcess failed")
        try:
            WAIT_OBJECT_0 = 0
            timeout_ms = int(timeout_s * 1000)
            result = ctypes.windll.kernel32.WaitForSingleObject(handle, timeout_ms)
            if result != WAIT_OBJECT_0:
                raise UpdateFailed("Timed out waiting for the app to exit.")
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    except UpdateFailed:
        raise
    except Exception:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except OSError:
                return
            time.sleep(0.25)
        raise UpdateFailed("Timed out waiting for the app to exit.")


def _retry(action, *, retries: int = 240, delay_s: float = 0.25) -> None:
    last_exc: Optional[BaseException] = None
    for attempt in range(retries):
        try:
            action()
            return
        except Exception as exc:
            last_exc = exc
            if attempt >= retries - 1:
                raise
            time.sleep(delay_s)
    if last_exc is not None:
        raise last_exc


def _merge_copy_dir(src: Path, dst: Path) -> None:
    if not src.exists() or not src.is_dir():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        dest = dst / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)


def _select_main_exe(install_dir: Path, preferred_name: Optional[str]) -> Path:
    if preferred_name:
        candidate = install_dir / preferred_name
        if candidate.exists():
            return candidate

    exes = [p for p in install_dir.glob("*.exe") if p.is_file() and p.name.lower() != "updater.exe"]
    if not exes:
        raise UpdateFailed(f"Could not locate an .exe in {install_dir}")

    exes.sort(key=lambda p: (p.stat().st_size, p.name.lower()), reverse=True)
    return exes[0]


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _compute_backup_dir(install_dir: Path) -> Path:
    base = install_dir.with_name(f"{install_dir.name}-backup")
    if not base.exists():
        return base
    return install_dir.with_name(f"{install_dir.name}-backup-{_timestamp()}")


def _perform_update(args: UpdateArgs, *, status_cb, progress_cb) -> None:
    install_dir = args.install_dir.resolve()
    updater_path = _resolve_updater_exe_path()
    payload_dir = (args.payload_dir or _default_payload_dir(updater_path)).resolve()

    status_cb("Waiting for the app to close…")
    progress_cb(5)
    _wait_for_pid(args.app_pid, timeout_s=240.0)

    if not install_dir.exists() or not install_dir.is_dir():
        raise UpdateFailed(f"Install directory not found: {install_dir}")

    if not payload_dir.exists() or not payload_dir.is_dir():
        raise UpdateFailed(f"Update payload directory not found: {payload_dir}")

    status_cb("Preparing backup…")
    progress_cb(15)
    backup_dir = _compute_backup_dir(install_dir)

    def do_backup() -> None:
        install_dir.rename(backup_dir)

    _retry(do_backup)

    try:
        status_cb("Installing new version…")
        progress_cb(35)

        def do_install() -> None:
            shutil.move(str(payload_dir), str(install_dir))

        _retry(do_install, retries=40, delay_s=0.5)

        status_cb("Restoring configs and logs…")
        progress_cb(60)
        _merge_copy_dir(backup_dir / "config_data", install_dir / "config_data")
        _merge_copy_dir(backup_dir / "logs", install_dir / "logs")

        copied_any = False
        for txt_path in backup_dir.glob("*_dir.txt"):
            if txt_path.is_file():
                shutil.copy2(txt_path, install_dir / txt_path.name)
                copied_any = True
        legacy_pointer = backup_dir / "config_dir.txt"
        if legacy_pointer.exists() and legacy_pointer.is_file():
            shutil.copy2(legacy_pointer, install_dir / legacy_pointer.name)
            copied_any = True
        if not copied_any:
            pass

        status_cb("Cleaning up old version…")
        progress_cb(75)

        def do_cleanup() -> None:
            shutil.rmtree(backup_dir)

        try:
            _retry(do_cleanup, retries=60, delay_s=0.5)
        except Exception:
            pass

        status_cb("Launching updated app…")
        progress_cb(90)
        exe_path = _select_main_exe(install_dir, args.exe_name)

        cmd = [str(exe_path)]
        if _is_frozen():
            cmd += ["--deleteupdater", "--updaterpath", str(updater_path)]

        subprocess.Popen(
            cmd,
            cwd=str(install_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )

        status_cb("Done.")
        progress_cb(100)
    except Exception:
        try:
            if backup_dir.exists() and not install_dir.exists():
                backup_dir.rename(install_dir)
        except Exception:
            pass
        raise


class _Worker(QObject):
    status = Signal(str)
    progress = Signal(int)
    finished = Signal()
    failed = Signal(str)

    def __init__(self, args: UpdateArgs):
        super().__init__()
        self._args = args

    def run(self) -> None:
        try:
            _perform_update(
                self._args,
                status_cb=lambda s: self.status.emit(s),
                progress_cb=lambda p: self.progress.emit(int(p)),
            )
            self.finished.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


class UpdateWindow(QWidget):
    def __init__(self, args: UpdateArgs):
        super().__init__()
        self.setWindowTitle("Updating…")
        self.setFixedWidth(420)
        self.setMinimumHeight(140)

        icon = _find_default_icon()
        if icon is not None:
            self.setWindowIcon(icon)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        self._label = QLabel("Starting…")
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        layout.addWidget(self._bar)

        self._thread = QThread(self)
        self._worker = _Worker(args)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.status.connect(self._label.setText)
        self._worker.progress.connect(self._bar.setValue)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._thread.start()

    def _on_finished(self) -> None:
        self._label.setText("Update complete. Launching…")
        self._bar.setValue(100)
        self._thread.quit()
        self._thread.wait(1000)
        QApplication.instance().quit()

    def _on_failed(self, message: str) -> None:
        self._label.setText(f"Update failed:\n{message}")
        self._thread.quit()
        self._thread.wait(1000)


def _find_default_icon() -> Optional[QIcon]:
    candidates: list[Path] = []
    try:
        base = Path(__file__).resolve().parent.parent
        candidates.append(base / "ui" / "assets" / "brand" / "newlogo.ico")
    except Exception:
        pass

    for p in candidates:
        if p.exists():
            icon = QIcon(str(p))
            if not icon.isNull():
                return icon
    return None


def _parse_args(argv: list[str]) -> UpdateArgs:
    parser = argparse.ArgumentParser(prog="updater", add_help=True)
    parser.add_argument("--install-dir", required=True)
    parser.add_argument("--app-pid", type=int, default=0)
    parser.add_argument("--exe-name", default=None)
    parser.add_argument("--payload-dir", default=None)
    ns = parser.parse_args(argv)

    install_dir = Path(ns.install_dir).expanduser()
    exe_name = (ns.exe_name or "").strip() or None
    payload_dir = Path(ns.payload_dir).expanduser() if ns.payload_dir else None
    return UpdateArgs(
        install_dir=install_dir,
        app_pid=int(ns.app_pid or 0),
        exe_name=exe_name,
        payload_dir=payload_dir,
    )


def main() -> int:
    if not sys.platform.startswith("win"):
        print("This updater currently supports Windows only.", file=sys.stderr)
        return 2

    args = _parse_args(sys.argv[1:])
    app = QApplication(sys.argv[:1])
    window = UpdateWindow(args)
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())

