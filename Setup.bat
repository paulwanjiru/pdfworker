@echo off
:: Document Studio Pro — Double-Click Bootstrap Launcher
:: Launches Setup.ps1 via PowerShell silently (no console flash)

pushd "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass ^
  -WindowStyle Hidden ^
  -File "%~dp0Setup.ps1"

popd
