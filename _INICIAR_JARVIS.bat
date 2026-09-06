@echo off
setlocal
set JARVIS_HOME=%~dp0
set JARVIS_PORTABLE=1

if not exist "%JARVIS_HOME%python-embed\python.exe" (
    echo ERRO: python-embed nao encontrado.
    pause & exit /b 1
)
if not exist "%JARVIS_HOME%config\api_keys.enc" (
    echo ERRO: config\api_keys.enc nao encontrado. Rode tools\encrypt_keys.py no PC principal.
    pause & exit /b 1
)

"%JARVIS_HOME%python-embed\python.exe" "%JARVIS_HOME%core\boot_terminal.py"
exit /b 0
