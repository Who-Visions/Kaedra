@echo off
REM Kaedra Mobile - Multi-Platform Build Script

echo ========================================
echo Kaedra Mobile - Platform Builds
echo ========================================
echo.

cd /d "%~dp0kaedra_mobile"

REM Clean previous builds
echo [1/4] Cleaning previous builds...
call flutter clean
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Clean failed
    pause
    exit /b 1
)

REM Get dependencies
echo.
echo [2/4] Installing dependencies...
call flutter pub get
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Dependency installation failed
    pause
    exit /b 1
)

REM Build Web
echo.
echo [3/4] Building for Web...
call flutter build web --release
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Web build failed
) else (
    echo ✅ Web build complete: build\web\
)

REM Build Android
echo.
echo [4/4] Building for Android...
call flutter build apk --release
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Android build failed
) else (
    echo ✅ Android build complete: build\app\outputs\flutter-apk\app-release.apk
)

REM Build iOS (if on macOS or with iOS toolchain)
echo.
echo [5/5] Building for iOS...
call flutter build ios --release --no-codesign
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ iOS build skipped (requires macOS or iOS toolchain)
) else (
    echo ✅ iOS build complete: build\ios\iphoneos\Runner.app
)

echo.
echo ========================================
echo Build Summary
echo ========================================
echo.
echo Web: build\web\
echo Android: build\app\outputs\flutter-apk\app-release.apk
echo iOS: build\ios\iphoneos\Runner.app (if available)
echo.
echo To serve web build:
echo   cd build\web
echo   python -m http.server 8081
echo.
echo To install Android:
echo   adb install build\app\outputs\flutter-apk\app-release.apk
echo.

pause
