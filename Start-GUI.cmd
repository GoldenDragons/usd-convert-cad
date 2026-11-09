@echo off
if not exist "%~dp0.venv\Scripts\pythonw.exe" (
  echo Missing local Python environment. See LOCAL-DEPLOYMENT.md.
  pause
  exit /b 1
)
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0desktop\main.py"
