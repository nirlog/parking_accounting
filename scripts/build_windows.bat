@echo off
setlocal
cd /d %~dp0\..

if not exist .venv (
  python -m venv .venv
)

call .venv\Scripts\activate
pip install -r parking_app\requirements.txt
python -m PyInstaller --clean --noconfirm parking_accounting.spec
