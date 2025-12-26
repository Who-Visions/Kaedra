@echo off
CALL .venv\Scripts\activate.bat

REM Load environment variables from .env file (skip comments)
FOR /F "eol=# tokens=*" %%i IN (.env) DO (
    SET "%%i"
)

python listen_and_speak.py --tts flash-lite --mic "Realtek"
PAUSE
