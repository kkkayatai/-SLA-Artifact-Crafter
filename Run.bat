@echo off
title SL:ARISE Artifact Unified Crafter
echo ==================================================
echo      SL:ARISE ARTIFACT UNIFIED CRAFTER
echo ==================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ and make sure to check "Add Python to PATH" during installation.
    echo Opening Python download page...
    start https://www.python.org/downloads/
    pause
    exit /b
)

:: Install dependencies silently
echo Checking and installing required dependencies...
pip install -r requirements.txt >nul 2>&1

:: Run the script
echo Starting the Crafter...
echo.
python auto_reroll_master.py
pause
