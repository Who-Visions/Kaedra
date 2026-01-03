@echo off
REM Simple KAEDRA v0.0.6 Launcher - PYTHON 3.14 TEST

cd /d "%~dp0"

echo.
echo ===============================================================================
echo     KAEDRA v0.0.6 - Shadow Tactician
echo     Who Visions LLC
echo     [PYTHON 3.14 TEST VERSION]
echo ===============================================================================
echo.

REM Force Python 3.14
py -3.14 run.py 2>nul && goto :SUCCESS
python3.14 run.py 2>nul && goto :SUCCESS

echo [ERROR] Python 3.14 not found or launch failed.
echo.
echo Python 3.14 may have compatibility issues with some packages.
echo Try Launch_Simple.bat (uses Python 3.12) instead.
echo.
pause
exit /b 1

:SUCCESS
exit /b 0
