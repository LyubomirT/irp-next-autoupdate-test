from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path


class WindowsUpdateScriptError(RuntimeError):
    pass


@dataclass(frozen=True)
class WindowsUpdatePlan:
    install_dir: Path
    staged_app_root: Path
    exe_name: str
    preserve_paths: tuple[str, ...]


DEFAULT_PRESERVE_PATHS: tuple[str, ...] = ("logs", "config_data", "config_dir.txt")


def write_apply_update_powershell_script(
    *,
    plan: WindowsUpdatePlan,
    app_pid: int,
    output_dir: Path | None = None,
) -> Path:
    install_dir = plan.install_dir.resolve()
    staged_root = plan.staged_app_root.resolve()
    exe_name = plan.exe_name

    if not exe_name.lower().endswith(".exe"):
        raise WindowsUpdateScriptError(f"Unexpected exe name: {exe_name}")

    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="intenserp-update-apply-"))
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    script_path = output_dir / "apply_update.ps1"

    preserve_list = list(plan.preserve_paths or DEFAULT_PRESERVE_PATHS)
    preserve_ps = "@(" + ", ".join([f"'{p}'" for p in preserve_list]) + ")"

    # Keep this script self-contained and robust; it runs after the GUI closes.
    script = f"""\
$ErrorActionPreference = "Stop"

$InstallDir = "{_ps_escape(str(install_dir))}"
$StagedDir  = "{_ps_escape(str(staged_root))}"
$ExeName    = "{_ps_escape(exe_name)}"
$AppPid     = {int(app_pid)}
$Preserve   = {preserve_ps}

function Write-UpdateLog([string]$Message) {{
  $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  try {{
    Add-Content -Path (Join-Path $InstallDir "update_install.log") -Value "[$stamp] $Message"
  }} catch {{
    # best-effort
  }}
}}

function Wait-ForProcessExit([int]$Pid, [int]$TimeoutSec = 120) {{
  if ($Pid -le 0) {{ return }}
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  while ((Get-Date) -lt $deadline) {{
    $p = Get-Process -Id $Pid -ErrorAction SilentlyContinue
    if (-not $p) {{ return }}
    Start-Sleep -Milliseconds 250
  }}
  throw "Timed out waiting for the app to exit."
}}

function Merge-Dir([string]$From, [string]$To) {{
  if (-not (Test-Path -LiteralPath $From)) {{ return }}
  if (-not (Test-Path -LiteralPath $To)) {{
    New-Item -ItemType Directory -Path $To | Out-Null
  }}
  Copy-Item -Recurse -Force -Path (Join-Path $From "*") -Destination $To -ErrorAction SilentlyContinue
}}

try {{
  Write-UpdateLog "Starting update. StagedDir=$StagedDir"
  Wait-ForProcessExit -Pid $AppPid

  if (-not (Test-Path -LiteralPath $InstallDir)) {{
    throw "Install directory not found: $InstallDir"
  }}
  if (-not (Test-Path -LiteralPath $StagedDir)) {{
    throw "Staged directory not found: $StagedDir"
  }}
  $stagedExe = Join-Path $StagedDir $ExeName
  if (-not (Test-Path -LiteralPath $stagedExe)) {{
    throw "Staged build does not contain expected executable: $stagedExe"
  }}

  $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $BackupDir = "$InstallDir.__backup_$timestamp"

  Write-UpdateLog "Renaming install dir to backup: $BackupDir"
  Rename-Item -LiteralPath $InstallDir -NewName (Split-Path -Leaf $BackupDir)

  Write-UpdateLog "Moving staged build into place."
  Move-Item -LiteralPath $StagedDir -Destination $InstallDir

  foreach ($p in $Preserve) {{
    $oldPath = Join-Path $BackupDir $p
    $newPath = Join-Path $InstallDir $p
    if (Test-Path -LiteralPath $oldPath) {{
      $item = Get-Item -LiteralPath $oldPath -ErrorAction SilentlyContinue
      if ($item -and $item.PSIsContainer) {{
        Write-UpdateLog "Restoring directory: $p"
        Merge-Dir -From $oldPath -To $newPath
      }} else {{
        Write-UpdateLog "Restoring file: $p"
        Copy-Item -Force -LiteralPath $oldPath -Destination $newPath -ErrorAction SilentlyContinue
      }}
    }}
  }}

  Write-UpdateLog "Launching updated app."
  Start-Process -WorkingDirectory $InstallDir -FilePath (Join-Path $InstallDir $ExeName) | Out-Null
  Write-UpdateLog "Update finished successfully."
  exit 0
}}
catch {{
  $err = $_.Exception.Message
  Write-UpdateLog ("Update failed: " + $err)

  try {{
    # Roll back: restore backup if present.
    if (Test-Path -LiteralPath $BackupDir) {{
      if (Test-Path -LiteralPath $InstallDir) {{
        Remove-Item -Recurse -Force -LiteralPath $InstallDir
      }}
      Rename-Item -LiteralPath $BackupDir -NewName (Split-Path -Leaf $InstallDir)
      Write-UpdateLog "Rollback complete."
      Start-Process -WorkingDirectory $InstallDir -FilePath (Join-Path $InstallDir $ExeName) | Out-Null
    }}
  }} catch {{
    Write-UpdateLog ("Rollback failed: " + $_.Exception.Message)
  }}

  try {{
    Add-Content -Path (Join-Path $InstallDir "update_failed.txt") -Value $err
  }} catch {{
    # best-effort
  }}
  exit 1
}}
"""

    script_path.write_text(script, encoding="utf-8")
    return script_path


def _ps_escape(value: str) -> str:
    # Double-quote escaping for PowerShell string literals.
    return value.replace("`", "``").replace('"', '`"')


def default_windows_update_plan(*, staged_app_root: Path) -> WindowsUpdatePlan:
    install_dir = Path(sys_executable_dir()).resolve()
    exe_name = Path(sys_executable_path()).name
    return WindowsUpdatePlan(
        install_dir=install_dir,
        staged_app_root=staged_app_root,
        exe_name=exe_name,
        preserve_paths=DEFAULT_PRESERVE_PATHS,
    )


def sys_executable_path() -> str:
    import sys

    return str(Path(sys.executable).resolve())


def sys_executable_dir() -> str:
    return str(Path(sys_executable_path()).parent)
