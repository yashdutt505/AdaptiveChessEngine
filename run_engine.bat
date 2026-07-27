@echo off
where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 "%~dp0main.py"
    exit /b
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python "%~dp0main.py"
    exit /b
)

set "CODEX_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%CODEX_PYTHON%" (
    "%CODEX_PYTHON%" "%~dp0main.py"
    exit /b
)

echo Python 3 was not found. Install Python or update run_engine.bat with its path. 1>&2
exit /b 1
