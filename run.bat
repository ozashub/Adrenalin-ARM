@echo off
cd /d "%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

REM try python first
where python >nul 2>&1
if %errorlevel% equ 0 (
    python src/main.py
) else (
    REM fallback to py launcher
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        py src/main.py
    ) else (
        echo Python is not installed or not in PATH
        pause
        exit /b 1
    )
)

pause
