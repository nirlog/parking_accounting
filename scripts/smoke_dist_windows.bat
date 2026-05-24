@echo off
setlocal
cd /d %~dp0\..

if not exist dist\ParkingAccounting\ParkingAccounting.exe (
  echo dist executable not found
  exit /b 1
)

dist\ParkingAccounting\ParkingAccounting.exe --bootstrap-only
if errorlevel 1 exit /b 1
