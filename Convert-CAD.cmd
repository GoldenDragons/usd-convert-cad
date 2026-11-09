@echo off
setlocal
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo Missing local Python environment: %~dp0.venv 1>&2
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" -m usd_convert_cad %*
exit /b %errorlevel%
