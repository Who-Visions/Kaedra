@echo off
REM ============================================================
REM    DAILY CREDIT BURNER - Automated Task
REM    Burns $2/day to use $50 before December 22, 2025
REM ============================================================

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║  💰 DAV1D CREDIT BURNER - Automated Daily Run           ║
echo ║  Target: $2.08/day = $50 in 24 days                      ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

cd /d "c:\Users\super\Watchtower\Dav1d\dav1d brain"

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Run the credit burner
echo.
echo Starting credit burn routine...
python burn_credits.py

REM Log completion
echo.
echo ✅ Credit burn complete at %date% %time%
echo.

REM Keep window open for 10 seconds
timeout /t 10

exit
