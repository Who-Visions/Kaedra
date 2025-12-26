@echo off
CALL .venv\Scripts\activate.bat

REM Load environment variables from .env file
FOR /F "tokens=*" %%i IN (.env) DO (
    SET %%i 2>nul
)

python listen_and_speak.py --tts flash --mic "Realtek"
PAUSE
