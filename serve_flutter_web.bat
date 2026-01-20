@echo off
REM Flutter Web Build and Serve Script

echo ========================================
echo Kaedra Mobile - Web Build
echo ========================================
echo.

cd /d "%~dp0kaedra_mobile"

echo [1/2] Building Flutter web app...
call flutter build web --release
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo [2/2] Starting web server...
echo.
echo ========================================
echo Flutter Web App Ready!
echo ========================================
echo.
echo Access from your phone:
echo   http://192.168.1.187:8080
echo.
echo Backend API:
echo   http://192.168.1.187:8000
echo.
echo Press CTRL+C to stop the server
echo ========================================
echo.

cd build\web
python -m http.server 8080

pause
