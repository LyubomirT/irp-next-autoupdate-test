from __future__ import annotations

import os
import sys
import shutil
from pathlib import Path
from typing import Optional, Tuple, List


APP_NAME = "IntenseRP Next"
CONFIG_DIRNAME = "config_data"
POINTER_FILENAME = "config_dir.txt"


def is_windows() -> bool:
    return sys.platform.startswith("win")


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def get_local_anchor_dir() -> Path:
    """
    Local anchor directory used for:
      - pointer file storage (always local)
      - relative preset base directory

    Prefer the directory containing the current entrypoint (script/executable).
    Fallback to the repo/app root (two levels above this file).
    """
    try:
        argv0 = sys.argv[0] if sys.argv else ""
        if argv0:
            candidate = Path(argv0).expanduser()
            try:
                resolved = candidate.resolve()
            except Exception:
                resolved = candidate.absolute()
            if resolved.exists():
                return resolved.parent
    except Exception:
        pass

    try:
        return Path(__file__).resolve().parent.parent
    except Exception:
        return Path.cwd()


def get_pointer_file_path() -> Path:
    return get_local_anchor_dir() / POINTER_FILENAME


def get_relative_config_dir() -> Path:
    return get_local_anchor_dir() / CONFIG_DIRNAME


def get_windows_appdata_config_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else (Path.home() / "AppData" / "Roaming")
    return base / APP_NAME / CONFIG_DIRNAME


def get_linux_user_data_config_dir() -> Path:
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data_home) if xdg_data_home else (Path.home() / ".local" / "share")
    return base / APP_NAME / CONFIG_DIRNAME


def get_config_storage_options() -> List[str]:
    options = ["Relative"]
    if is_windows():
        options.append("Windows AppData")
    elif is_linux():
        options.append("Linux User Data")
    options.append("Custom")
    return options


def resolve_config_dir(preset: Optional[str], custom_path: Optional[str]) -> Path:
    preset_value = (preset or "Relative").strip()

    if preset_value == "Relative":
        return get_relative_config_dir()

    if preset_value == "Windows AppData":
        return get_windows_appdata_config_dir()

    if preset_value == "Linux User Data":
        return get_linux_user_data_config_dir()

    if preset_value == "Custom":
        custom_value = (custom_path or "").strip()
        if not custom_value:
            raise ValueError("Custom config directory is empty.")

        path = Path(custom_value).expanduser()
        if not path.is_absolute():
            path = (get_local_anchor_dir() / path)
        try:
            return path.resolve()
        except Exception:
            return path.absolute()

    return get_relative_config_dir()


def read_pointer_file() -> Optional[Path]:
    pointer_path = get_pointer_file_path()
    if not pointer_path.exists():
        return None

    try:
        content = pointer_path.read_text(encoding="utf-8").strip()
        if not content:
            return None
        path = Path(content).expanduser()
        if not path.is_absolute():
            path = get_local_anchor_dir() / path
        try:
            return path.resolve()
        except Exception:
            return path.absolute()
    except Exception:
        return None


def write_pointer_file(config_dir: Path) -> None:
    pointer_path = get_pointer_file_path()
    pointer_path.write_text(str(config_dir), encoding="utf-8")


def get_active_config_dir(create_pointer_if_missing: bool = True) -> Path:
    config_dir = read_pointer_file()
    if config_dir is not None:
        return config_dir

    default_dir = get_relative_config_dir()
    if create_pointer_if_missing:
        try:
            write_pointer_file(default_dir)
        except Exception:
            pass
    return default_dir


def infer_preset_from_config_dir(config_dir: Path) -> Tuple[str, str]:
    resolved = config_dir.resolve()

    relative = get_relative_config_dir().resolve()
    if resolved == relative:
        return ("Relative", "")

    if is_windows():
        appdata = get_windows_appdata_config_dir().resolve()
        if resolved == appdata:
            return ("Windows AppData", "")

    if is_linux():
        linux_data = get_linux_user_data_config_dir().resolve()
        if resolved == linux_data:
            return ("Linux User Data", "")

    return ("Custom", str(resolved))


def _looks_like_config_dir(path: Path) -> bool:
    return (
        (path / "settings.json.enc").exists()
        or (path / "settings.key").exists()
        or (path / "playwright_profiles").exists()
    )


def _is_subpath(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def migrate_config_dir(from_dir: Path, to_dir: Path) -> None:
    """
    Migrate the entire config directory by replacing the destination contents.

    Safety notes:
      - refuses overlapping source/target directories
      - refuses targeting the application directory or any of its parents
      - refuses targeting filesystem roots
      - refuses deleting non-empty directories that don't look like our config dir
    """
    src = from_dir.resolve()
    dst = to_dir.resolve()

    if src == dst:
        return

    if not src.exists() or not src.is_dir():
        raise ValueError(f"Source config directory does not exist: {src}")

    # Prevent recursion / accidental deletions.
    if _is_subpath(dst, src) or _is_subpath(src, dst):
        raise ValueError("Source/target directories overlap.")

    anchor = get_local_anchor_dir().resolve()

    # Never allow wiping the application directory or any directory containing it.
    if dst == anchor or _is_subpath(anchor, dst):
        raise ValueError("Target directory contains the application directory.")

    # Never allow filesystem root targets.
    if dst == Path(dst.anchor):
        raise ValueError("Target directory is a filesystem root.")

    if dst.exists():
        if not dst.is_dir():
            raise ValueError("Target path exists and is not a directory.")

        try:
            dst_has_any = any(dst.iterdir())
        except Exception:
            dst_has_any = True

        if dst_has_any and not _looks_like_config_dir(dst):
            raise ValueError(
                "Target directory is not empty and does not look like an IntenseRP Next config directory."
            )

        shutil.rmtree(dst)

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)

