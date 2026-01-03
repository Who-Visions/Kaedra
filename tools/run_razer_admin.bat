@echo off
echo ═══════════════════════════════════════════════════════
echo   KAEDRA RAZER CHROMA VALIDATOR (ADMIN MODE)
echo ═══════════════════════════════════════════════════════
echo.
echo Requesting administrator privileges...
echo.

:: Request admin elevation
powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0..\" && .\.venv\Scripts\python.exe tools\validate_chromalink.py && pause' -Verb RunAs"
