@echo off
REM Su-Chef GUI Launcher for Windows
REM Sets proper encoding and runs the GUI

echo Starting Su-Chef GUI...

REM Set UTF-8 encoding
chcp 65001 > nul

REM Set Python encoding
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

REM Run the GUI
python su_chef_gui.py

pause
