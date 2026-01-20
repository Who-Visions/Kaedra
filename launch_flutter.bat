@echo off
REM Flutter Web Launch Script for Kaedra Mobile

echo ========================================
echo Kaedra Mobile - Weighted Lore Test
echo ========================================
echo.

cd /d "%~dp0kaedra_mobile"

echo [1/3] Installing dependencies...
call flutter pub get
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Building for web...
call flutter build web --release
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo [3/3] Launching web app...
echo.
echo Opening Chrome with Flutter web app...
echo Backend should be running at: http://192.168.1.187:8000
echo.

call flutter run -d chrome

pause
