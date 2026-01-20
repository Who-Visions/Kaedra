@echo off
REM Kaedra Backend Server Launcher

echo ========================================
echo Kaedra Backend Server
echo ========================================
echo.
echo Starting server on http://0.0.0.0:8080
echo Local IP: 192.168.1.187
echo.
echo Mobile access: http://192.168.1.187:8080
echo.

cd /d "%~dp0"

REM Start the server
python -m uvicorn kaedra.api.main:app --host 0.0.0.0 --port 8080 --reload

pause
