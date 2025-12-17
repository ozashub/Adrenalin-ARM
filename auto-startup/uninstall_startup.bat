@echo off
setlocal EnableDelayedExpansion

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo =============================================
echo  Startup Uninstaller (removes startup task)
echo =============================================
echo.

set "TASK_NAME=Elevated_run_bat"

echo Removing scheduled task: %TASK_NAME%
echo.

schtasks /delete /tn "%TASK_NAME%" /f

if %errorlevel% neq 0 (
    echo.
    echo Failed to remove scheduled task. It may not exist.
    pause
    exit /b
)

echo.
echo Success - Startup task removed
pause
exit /b

