@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" -m pip install -r requirements-build.txt
if errorlevel 1 exit /b %errorlevel%
".venv\Scripts\python.exe" tools\build_portable.py
exit /b %errorlevel%
