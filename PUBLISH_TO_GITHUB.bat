@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\publish_to_github.ps1"
if errorlevel 1 (
  echo.
  echo Publish failed. Send a screenshot of this window to ChatGPT.
  pause
  exit /b 1
)
echo.
echo Published successfully.
pause
