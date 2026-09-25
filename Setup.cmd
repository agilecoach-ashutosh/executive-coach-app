@echo off
setlocal
cd /d "%~dp0"
echo Presence Coach - first-time setup
echo Requires Python 3.12 and internet for dependencies.
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo Python 3.12 is required alongside any existing Python version.
  echo Install Python 3.12 from python.org with the Python launcher, then run this again.
  echo Alternatively run: winget install -e --id Python.Python.3.12
  pause
  exit /b 1
)

py -3.12 -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt -c constraints.txt
if errorlevel 1 goto failed

".venv\Scripts\python.exe" windows_setup.py
if errorlevel 1 (
  echo.
  echo WARNING: Presence Coach installed successfully, but the desktop shortcut could not be created.
  echo You can still start Presence Coach by double-clicking Start.cmd.
  echo.
) else (
  echo Desktop shortcut created successfully.
)

echo Setup complete. Use the Presence Coach desktop/Start Menu shortcut or Start.cmd.\necho Uninstall Presence Coach is available from the Windows Start Menu.
pause
exit /b 0

:failed
echo Setup failed. Read the error above and retry after fixing it.
pause
exit /b 1
