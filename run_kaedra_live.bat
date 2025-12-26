@echo off
echo Starting Kaedra Live Mode (Pro TTS)...

REM Load environment variables from .env file
FOR /F "tokens=*" %%i IN (.env) DO (
    SET %%i 2>nul
)

call .venv\Scripts\python.exe listen_and_speak.py --tts pro --mic "Realtek"
pause
