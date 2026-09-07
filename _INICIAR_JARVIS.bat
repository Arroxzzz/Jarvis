@echo off
setlocal
set PENDRIVE_ROOT=%~dp0
"%PENDRIVE_ROOT%python-embed\python.exe" "%PENDRIVE_ROOT%boot_stage0.py"
exit /b 0

