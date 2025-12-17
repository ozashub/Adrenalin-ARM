@echo off
setlocal EnableDelayedExpansion

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo ==========================================
echo  Startup Installer (runs run.bat at startup)
echo ==========================================
echo.

set /p TARGET_DIR=Enter FULL path to the folder containing run.bat: 

if not exist "%TARGET_DIR%" (
    echo.
    echo Folder does not exist.
    pause
    exit /b
)

if not exist "%TARGET_DIR%\run.bat" (
    echo.
    echo run.bat was not found in that folder.
    pause
    exit /b
)

set "TARGET_BAT=%TARGET_DIR%\run.bat"
set "TASK_NAME=Elevated_run_bat"

echo.
echo Found: %TARGET_BAT%
echo Creating scheduled task: %TASK_NAME%
echo.

:: basically just sets up auto run on login w/ highest privelages
schtasks /create ^
 /tn "%TASK_NAME%" ^
 /tr "\"%TARGET_BAT%\"" ^
 /sc onlogon ^
 /rl highest ^
 /f

if %errorlevel% neq 0 (
    echo.
    echo Failed to create scheduled task.
    pause
    exit /b
)

echo.
echo Success
pause
exit /b