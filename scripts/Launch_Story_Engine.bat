@echo off
setlocal
cd /d "%~dp0.."
echo [KAEDRA] Activating Virtual Environment...
call venv\Scripts\activate.bat
echo [KAEDRA] Launching StoryEngine v7.15...
python -m kaedra.story.engine
pause
