@echo off
echo Starting Kaedra + Chatterbox Voice Engine...
cd /d "c:\Users\super\kaedra_proper"
"C:\Users\super\AppData\Local\Programs\Python\Python312\python.exe" chatterbox_speak.py --voice kaedra_voice_new.wav --device cuda
pause
