@echo off
REM Install KAEDRA v0.0.6 Dependencies

cd /d "%~dp0"

echo.
echo ===============================================================================
echo     KAEDRA v0.0.6 - Dependency Installation
echo     Who Visions LLC
echo ===============================================================================
echo.

REM Detect Python (prefer 3.12, avoid 3.14)
py -3.12 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=py -3.12
    goto :INSTALL
)

py -3.11 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=py -3.11
    goto :INSTALL
)

python3.12 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python3.12
    goto :INSTALL
)

python --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python
    goto :INSTALL
)

echo [ERROR] Python not found!
echo Please install Python 3.10+ from https://www.python.org/downloads/
echo.
pause
exit /b 1

:INSTALL
for /f "tokens=*" %%i in ('%PYTHON_CMD% --version') do set PYTHON_VERSION=%%i
echo [*] Using: %PYTHON_VERSION%
echo.

echo [*] Installing KAEDRA Dependencies...
echo.
echo This will install:
echo   - google-cloud-aiplatform (Vertex AI)
echo   - google-generativeai (Gemini)
echo   - python-dotenv (Environment variables)
echo.

%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Installation failed!
    echo.
    pause
    exit /b 1
)

echo.
echo ===============================================================================
echo [OK] Installation Complete!
echo ===============================================================================
echo.
echo You can now launch KAEDRA with:
echo   Launch_Kaedra_v006.bat  (full launcher)
echo   Launch_Simple.bat       (quick launch)
echo   python run.py           (direct)
echo.
pause
exit /b 0
