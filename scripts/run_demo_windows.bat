@echo off
setlocal
cd /d %~dp0\..
set PARKING_APP_DATA_DIR=%CD%\.demo_runtime
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python scripts\load_demo_data.py --reset-demo
python -m parking_app.main
endlocal
