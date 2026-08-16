@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo  Enable GitHub updates for CoD2 Chat Translator
echo ==============================================
echo.
echo This should be used AFTER this repository exists:
echo   https://github.com/kriskarter/cod2-chat-translator
echo.
set /p OK=Type YES to configure it now: 
if /I not "%OK%"=="YES" exit /b 0

python -c "import json,pathlib; p=pathlib.Path('release_config.json'); d=json.loads(p.read_text(encoding='utf-8')); d['repository']='kriskarter/cod2-chat-translator'; d['channel']='stable'; d['check_on_start']=True; p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')"
if errorlevel 1 (
  echo Failed to update release_config.json
  pause
  exit /b 1
)

echo.
echo GitHub update channel configured.
echo Now run BUILD_RELEASE.bat to rebuild the installer.
pause
