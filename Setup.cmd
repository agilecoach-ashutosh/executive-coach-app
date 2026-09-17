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

if not exist "assets\presence.ico.b64" (
  echo Presence icon asset is missing.
  goto failed
)
powershell -NoProfile -Command "$b64=Get-Content 'assets\presence.ico.b64' -Raw; [IO.File]::WriteAllBytes([IO.Path]::Combine((Get-Location).Path,'assets','presence.ico'),[Convert]::FromBase64String($b64.Trim()))"
if errorlevel 1 goto failed

py -3.12 -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
powershell -NoProfile -Command "$root=(Get-Location).Path; $w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut([IO.Path]::Combine([Environment]::GetFolderPath('Desktop'),'Presence Coach.lnk')); $s.TargetPath=[IO.Path]::Combine($root,'.venv\Scripts\pythonw.exe'); $s.Arguments='session_export_mode.py'; $s.WorkingDirectory=$root; $s.IconLocation=([IO.Path]::Combine($root,'assets','presence.ico') + ',0'); $s.Save()"
if errorlevel 1 goto failed
echo Setup complete. Use the Presence Coach desktop shortcut or Start.cmd.
pause
exit /b 0
:failed
echo Setup failed. Read the error above and retry after fixing it.
pause
exit /b 1
