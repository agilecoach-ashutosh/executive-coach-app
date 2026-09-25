@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Presence Coach - Uninstall

echo.
echo Presence Coach - uninstall
echo ==========================
echo.
echo This removes the local Python environment and Presence Coach shortcuts.
echo It does NOT remove Python, system tools, or exported transcripts/reports/audio.
echo The project folder and source files will remain.
echo.

choice /C YN /N /M "Continue with uninstall? [Y/N]: "
if errorlevel 2 (
  echo Uninstall cancelled.
  exit /b 0
)

echo.
choice /C YN /N /M "Remove saved Gemini/Groq API keys from Windows Credential Manager? [Y/N]: "
if errorlevel 2 goto skip_credentials

echo.
echo Removing saved Presence Coach API keys...
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" uninstall_cleanup.py
  if errorlevel 1 echo WARNING: One or more saved API keys could not be removed automatically.
) else (
  py -3.12 -c "import keyring" >nul 2>&1
  if errorlevel 1 (
    echo WARNING: Presence Coach's local Python environment is missing, so saved API keys could not be removed automatically.
    echo Remove any PresenceCoach entries manually from Windows Credential Manager if needed.
  ) else (
    py -3.12 uninstall_cleanup.py
    if errorlevel 1 echo WARNING: One or more saved API keys could not be removed automatically.
  )
)

:skip_credentials
echo.
echo Removing Presence Coach shortcuts...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$desktop=[Environment]::GetFolderPath('Desktop');" ^
  "Remove-Item -LiteralPath (Join-Path $desktop 'Presence Coach.lnk') -Force -ErrorAction SilentlyContinue;" ^
  "$programs=[Environment]::GetFolderPath('Programs');" ^
  "Remove-Item -LiteralPath (Join-Path $programs 'Presence Coach') -Recurse -Force -ErrorAction SilentlyContinue"

echo Removing local application environment...
if exist ".venv" rmdir /s /q ".venv"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$root=(Get-Location).Path;" ^
  "Get-ChildItem -LiteralPath $root -Directory -Recurse -Force -ErrorAction SilentlyContinue |" ^
  "Where-Object { $_.Name -eq '__pycache__' } |" ^
  "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue;" ^
  "Remove-Item -LiteralPath (Join-Path $root '.pytest_cache') -Recurse -Force -ErrorAction SilentlyContinue"

echo.
echo Presence Coach has been removed from this Windows account.
echo Your exported transcripts, reports, and audio files were not deleted.
echo.
echo The source/project folder is still here:
echo %CD%
echo You may delete that folder manually if you no longer want the source files.
echo.
pause
exit /b 0
