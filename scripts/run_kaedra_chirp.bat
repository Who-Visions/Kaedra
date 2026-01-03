@echo off
echo [*] Starting Kaedra Voice Engine (Chirp 3 HD + Smart Turn VAD)...
echo [*] TTS Model: Journey Expressive (Flash)
echo [*] VAD: Smart Turn V3 (Local)
cd /d "%~dp0"
call .venv\Scripts\activate
python listen_and_speak.py --tts flash --mic "Chat Mix"
pause
