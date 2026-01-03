@echo off
REM Simple KAEDRA v0.0.6 Launcher

cd /d "%~dp0"

echo.
echo ===============================================================================
echo     KAEDRA v0.0.6 - Shadow Tactician
echo     Who Visions LLC
echo ===============================================================================
echo.

REM Try Python 3.12 specifically (avoid 3.14 compatibility issues)
py -3.12 run.py 2>nul && goto :SUCCESS
py -3.11 run.py 2>nul && goto :SUCCESS
python3.12 run.py 2>nul && goto :SUCCESS
python run.py 2>nul && goto :SUCCESS

echo [ERROR] Python not found or launch failed.
echo.
echo Try installing dependencies:
echo   py -3 -m pip install -r requirements.txt
echo.
pause
exit /b 1

:SUCCESS
exit /b 0
