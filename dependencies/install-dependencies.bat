@echo off
cd /d "%~dp0"

where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYEXEC=python"
) else (
    set "PYEXEC=py"
)

echo Updating pip, wheel and setuptools...
%PYEXEC% -m pip install --upgrade pip setuptools wheel

echo Installing requirements...
%PYEXEC% -m pip install -r requirements.txt
if %errorlevel% equ 0 (
    echo.
    echo Dependencies installed successfully.
    pause
    exit /b 0
)

echo.
echo Initial install failed. Attempting to install PyAudio using pipwin (prebuilt wheel)...
%PYEXEC% -m pip install --upgrade pip
%PYEXEC% -m pip install pipwin --upgrade
if %errorlevel% neq 0 (
    echo Failed to install pipwin automatically.
    goto pipwin_fail
)

%PYEXEC% -m pipwin install pyaudio
if %errorlevel% neq 0 (
    echo pipwin failed to install PyAudio automatically.
    goto pipwin_fail
)

echo Re-attempting requirements install...
%PYEXEC% -m pip install -r requirements.txt
if %errorlevel% equ 0 (
    echo.
    echo Dependencies installed successfully (PyAudio installed via pipwin).
    pause
    exit /b 0
)

:pipwin_fail
echo.
echo Automatic installation failed. Manual steps:
echo  1) Ensure you are running the same Python used by this script: %PYEXEC%
echo  2) Install a prebuilt PyAudio wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
echo     then run: %PYEXEC% -m pip install C:\path\to\PyAudio‑<version>-cp<XY>-cp<XY>-win_amd64.whl
echo  3) Or install Visual C++ Build Tools and try: %PYEXEC% -m pip install pyaudio
echo.
pause
exit /b 1
