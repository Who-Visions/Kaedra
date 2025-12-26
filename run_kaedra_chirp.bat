@echo off
echo [*] Starting Kaedra Voice Engine (Chirp 3 HD + Smart Turn VAD)...
echo [*] TTS Model: Chirp 3 HD (Kore)
echo [*] VAD: Smart Turn V3 (Local)
cd /d "%~dp0"
call .venv\Scripts\activate
python listen_and_speak.py --tts chirp-kore --mic "Chat Mix"
pause
