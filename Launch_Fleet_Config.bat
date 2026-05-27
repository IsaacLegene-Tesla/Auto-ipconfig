@echo off
cd /d "%~dp0"

set PY=
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
  set PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
) else (
  where python >nul 2>&1 && set PY=python
)

if "%PY%"=="" (
  echo Python not found. Install Python 3.12+ and run: pip install flask
  pause
  exit /b 1
)

"%PY%" -m pip install flask -q
"%PY%" generator\fleet_app.py
pause
