# Adrenalin ARM

Voice-activated launcher for Adrenalin. Listens for trigger phrases and automatically launches Adrenalin when detected.

## Prerequisites

1. Download Python 3.8 or later from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"

## Installation

1. Extract or clone this repository to your desired location
2. Run `build-dependencies.bat` to install required Python packages
3. Run `run.bat` to start the macro.

## Usage

Run `run.bat` to start the application. The console window will hide automatically and the application will appear in the system tray. You can show the console to ensure your microphone is selected by going to the tray and selecting "Show Console".

The application listens for the following trigger phrases:
- "start the macro"
- "start macro"
- "launch macro"
- "fire up the macro"
- "start adrenalin"

When a trigger phrase is detected, Adrenalin will launch automatically if it is not already running.

## System Tray Menu

Right-click the tray icon to access:
- Start Macro: Manually launch Adrenalin
- Show Console: Display the console window
- Quit: Exit the application

## Startup Installation

To run Adrenalin ARM automatically on Windows login, run `install_startup.bat` as administrator and provide the full path to the folder containing `run.bat`.

## Common Issues

**Wrong microphone is being used**

The application uses your Windows default microphone. To fix this, set your desired microphone as the default recording device in Windows Sound Settings (Settings > System > Sound > Input).

**Windows error sound plays when triggering**

This indicates Adrenalin is already running. The application will not launch a second instance if Adrenalin is already active.

## Requirements

- Windows 10 or later
- Python 3.8 or later
- Microphone access
- Internet connection (for speech recognition)

