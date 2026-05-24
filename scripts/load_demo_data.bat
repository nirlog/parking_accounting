@echo off
setlocal
cd /d %~dp0\..
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python scripts\load_demo_data.py --reset-demo
endlocal
