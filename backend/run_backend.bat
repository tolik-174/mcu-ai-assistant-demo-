@echo off
echo Starting MCU AI Assistant backend...
cd /d %~dp0
uvicorn app:app --reload --port 8000
pause