@echo off
cd /d "%~dp0"
echo ====================================
echo RUNNING auto_snitcher.py
echo ====================================
py -3.11 -u auto_snitcher.py
echo.
echo ====================================
echo PRESS ANY KEY TO CLOSE
pause >nul