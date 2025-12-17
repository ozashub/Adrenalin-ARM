@echo off
cd /d "%~dp0"

where python >nul 2>&1 && (
    python -m pip install -r requirements.txt
) || (
    py -m pip install -r requirements.txt
)

pause
