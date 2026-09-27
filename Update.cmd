@echo off
setlocal
cd /d "%~dp0"
title Presence Coach - Update
echo Close Presence Coach before updating. This updater does not require Git.
echo.
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo Python 3.12 is required. Run Setup.cmd or install Python 3.12 first.
  pause
  exit /b 1
)
py -3.12 update_app.py
set "RESULT=%ERRORLEVEL%"
echo.
if not "%RESULT%"=="0" echo Your previous installation was left in place or restored. Read the message above.
pause
exit /b %RESULT%
