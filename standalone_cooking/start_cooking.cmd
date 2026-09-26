@echo off
cd /d "%~dp0"
py -3 server.py --open
if errorlevel 1 (
    echo.
    echo Could not start the cooking game. Keep this window open to see the error.
    pause
)
