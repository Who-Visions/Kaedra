@echo off
chcp 65001 >nul 2>&1
REM ===================================================================
REM   KAEDRA v0.0.6 Launcher
REM   Shadow Tactician | Who Visions LLC
REM ===================================================================

echo.
echo ===============================================================================
echo.
echo    ██╗  ██╗ █████╗ ███████╗██████╗ ██████╗  █████╗      █████╗ ██╗
echo    ██║ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██╗    ██╔══██╗██║
echo    █████╔╝ ███████║█████╗  ██║  ██║██████╔╝███████║    ███████║██║
echo    ██╔═██╗ ██╔══██║██╔══╝  ██║  ██║██╔══██╗██╔══██║    ██╔══██║██║
echo    ██║  ██╗██║  ██║███████╗██████╔╝██║  ██║██║  ██║    ██║  ██║██║
echo    ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝
echo.
echo    v0.0.6 - Shadow Tactician - us-east4
echo    Who Visions LLC
echo.
echo ===============================================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check for Python (prioritize 3.12, avoid 3.14 compatibility issues)
py -3.12 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=py -3.12
    goto :FOUND_PYTHON
)

py -3.11 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=py -3.11
    goto :FOUND_PYTHON
)

python3.12 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python3.12
    goto :FOUND_PYTHON
)

python --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python
    goto :FOUND_PYTHON
)

echo [ERROR] Python not found. Please install Python 3.10 or higher.
echo.
echo Download from: https://www.python.org/downloads/
echo.
pause
exit /b 1

:FOUND_PYTHON
REM Display Python version
for /f "tokens=*" %%i in ('%PYTHON_CMD% --version') do set PYTHON_VERSION=%%i
echo [*] Using: %PYTHON_VERSION%
echo.

REM Check if run.py exists
if not exist "run.py" (
    echo [ERROR] run.py not found in current directory.
    echo Expected: %CD%\run.py
    echo.
    echo Make sure you're running this from the kaedra_v006 directory.
    echo.
    pause
    exit /b 1
)

REM Check for required packages
echo [*] Checking dependencies...
%PYTHON_CMD% -c "import vertexai" >nul 2>&1
if errorlevel 1 goto :MISSING_DEPS
goto :DEPS_OK

:MISSING_DEPS
echo.
echo [!] Missing required packages detected!
echo.
echo Required packages:
echo   - google-cloud-aiplatform (vertexai)
echo   - google-generativeai
echo   - python-dotenv
echo.
set /p INSTALL_DEPS="Would you like to install them now? (Y/N) > "

if /i "%INSTALL_DEPS%"=="Y" goto :DO_INSTALL
if /i "%INSTALL_DEPS%"=="y" goto :DO_INSTALL
echo.
echo [!] Cannot launch without required packages.
echo.
echo To install manually, run:
echo   %PYTHON_CMD% -m pip install -r requirements.txt
echo.
pause
exit /b 1

:DO_INSTALL
echo.
echo [*] Installing dependencies...
echo.
%PYTHON_CMD% -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Package installation failed.
    echo Try running manually: %PYTHON_CMD% -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Dependencies installed successfully!
echo.

:DEPS_OK

REM Launch KAEDRA
echo [*] Launching KAEDRA v0.0.6...
echo [*] Location: us-east4
echo.
%PYTHON_CMD% run.py

REM Check exit status
if errorlevel 1 (
    echo.
    echo [!] KAEDRA exited with error code: %errorlevel%
    echo.
    pause
)

exit /b 0
