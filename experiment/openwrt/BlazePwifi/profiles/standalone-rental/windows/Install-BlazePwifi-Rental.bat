@echo off
setlocal
title BlazePwifi Standalone Rental Server Installer
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-BlazePwifi-Rental.ps1"
set RC=%ERRORLEVEL%
if not "%RC%"=="0" (
  echo.
  echo Installer exited with code %RC%.
  pause
)
exit /b %RC%
