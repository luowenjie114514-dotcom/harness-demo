@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY=%~dp0runtime\python\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" make_mess.py
echo.
pause
