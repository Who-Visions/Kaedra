@echo off
chcp 65001 >nul 2>&1
REM ===================================================================
REM   KAEDRA v0.0.6 Launcher - PYTHON 3.14 TEST VERSION
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
echo    [PYTHON 3.14 TEST VERSION]
echo.
echo ===============================================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Force Python 3.14
py -3.14 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=py -3.14
    goto :FOUND_PYTHON
)

python3.14 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python3.14
    goto :FOUND_PYTHON
)

echo [ERROR] Python 3.14 not found!
echo.
echo You have these versions installed:
py --list
echo.
pause
exit /b 1

:FOUND_PYTHON
REM Display Python version
for /f "tokens=*" %%i in ('%PYTHON_CMD% --version') do set PYTHON_VERSION=%%i
echo [*] Using: %PYTHON_VERSION%
echo [*] Testing Python 3.14 compatibility...
echo.

REM Check if run.py exists
if not exist "run.py" (
    echo [ERROR] run.py not found in current directory.
    echo Expected: %CD%\run.py
    echo.
    pause
    exit /b 1
)

REM Check for required packages
echo [*] Checking dependencies...
%PYTHON_CMD% -c "import vertexai" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [!] Missing required packages detected!
    echo.
    echo Installing dependencies with Python 3.14...
    echo.
    %PYTHON_CMD% -m pip install -r requirements.txt
    
    if errorlevel 1 (
        echo.
        echo [ERROR] Package installation failed with Python 3.14.
        echo This may indicate compatibility issues.
        echo.
        pause
        exit /b 1
    )
    echo.
)

REM Launch KAEDRA with 3.14
echo [*] Launching KAEDRA v0.0.6 with Python 3.14...
echo [*] Location: us-east4
echo.
echo [DEBUG] If you see errors, Python 3.14 may have compatibility issues.
echo [DEBUG] Use Launch_Kaedra_v006.bat for Python 3.12 instead.
echo.
%PYTHON_CMD% run.py

REM Check exit status
if errorlevel 1 (
    echo.
    echo [!] KAEDRA exited with error code: %errorlevel%
    echo [!] This suggests Python 3.14 has compatibility issues.
    echo [!] Try Launch_Kaedra_v006.bat (uses Python 3.12) instead.
    echo.
    pause
)

exit /b 0
