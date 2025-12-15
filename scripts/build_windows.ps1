[CmdletBinding()]
param(
  [string]$AppName = "intenserp-next-v2",
  [string]$PackageName = "intenserp-next-v2-win32-x64"
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

$EntryPoint = Join-Path $RepoRoot "main.py"
$IconPath = Join-Path $RepoRoot "ui/assets/brand/newlogo.ico"
$VersionPath = Join-Path $RepoRoot "version.txt"

if (!(Test-Path $EntryPoint)) { throw "Entry point not found: $EntryPoint" }
if (!(Test-Path $IconPath)) { throw "Icon not found: $IconPath" }
if (!(Test-Path $VersionPath)) { throw "version.txt not found: $VersionPath" }

$BuildDir = Join-Path $RepoRoot "build"
$DistDir = Join-Path $RepoRoot "dist"
$SpecPath = Join-Path $RepoRoot "$AppName.spec"

foreach ($path in @($BuildDir, $DistDir, $SpecPath)) {
  if (Test-Path $path) {
    Remove-Item -Recurse -Force $path
  }
}

$pyinstallerArgs = @(
  "--noconfirm"
  "--clean"
  "--onedir"
  "--noconsole"
  "--name", $AppName
  "--icon", $IconPath
  "--add-data", "version.txt;."
  "--add-data", "ui/assets;ui/assets"
  "--add-data", "ui/fonts;ui/fonts"
  "--collect-all", "patchright"
  "--collect-all", "playwright"
  $EntryPoint
)

python -m PyInstaller @pyinstallerArgs

$BuiltAppDir = Join-Path $DistDir $AppName
if (!(Test-Path $BuiltAppDir)) { throw "PyInstaller output folder not found: $BuiltAppDir" }

# version.txt must be present at the package root (convenience copy; runtime uses bundled data).
Copy-Item -Force $VersionPath (Join-Path $BuiltAppDir "version.txt")

# Make sure logs/configs are not shipped (even if present locally).
foreach ($root in @($BuiltAppDir, (Join-Path $BuiltAppDir "_internal"))) {
  if (!(Test-Path $root)) { continue }
  foreach ($forbiddenDir in @("logs", "config_data")) {
    $p = Join-Path $root $forbiddenDir
    if (Test-Path $p) { Remove-Item -Recurse -Force $p }
  }
  foreach ($forbiddenFile in @("config_dir.txt", ".env")) {
    $p = Join-Path $root $forbiddenFile
    if (Test-Path $p) { Remove-Item -Force $p }
  }
}

$StagingDir = Join-Path $DistDir $PackageName
if (Test-Path $StagingDir) { Remove-Item -Recurse -Force $StagingDir }
New-Item -ItemType Directory -Path $StagingDir | Out-Null

Copy-Item -Recurse -Force (Join-Path $BuiltAppDir "*") $StagingDir

$ZipPath = Join-Path $DistDir "$PackageName.zip"
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
Compress-Archive -Path $StagingDir -DestinationPath $ZipPath -Force

Write-Output "Created release asset: $ZipPath"
