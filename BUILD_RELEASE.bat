@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo  CoD2 Chat Translator - Release Build
echo ==============================================

where py >nul 2>nul
if errorlevel 1 (
  echo Python was not found.
  pause
  exit /b 1
)

if not exist ".buildvenv\Scripts\python.exe" py -3 -m venv .buildvenv
call ".buildvenv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
if errorlevel 1 goto :fail

python tools\build_assets.py
if errorlevel 1 goto :fail

python -m unittest discover -s tests -v
if errorlevel 1 goto :fail

pyinstaller --noconfirm --clean --onefile --windowed --name CoD2ChatTranslator --icon assets\app.ico --add-data "assets;assets" --add-data "release_config.json;." app.py
if errorlevel 1 goto :fail
pyinstaller --noconfirm --clean --onefile --windowed --name CoD2ChatTranslatorUpdater --icon assets\app.ico updater.py
if errorlevel 1 goto :fail

python tools\prepare_release.py
if errorlevel 1 goto :fail

set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" (
  echo.
  echo Inno Setup 6 was not found. EXEs and update package are ready in dist/release.
  echo Install Inno Setup 6, then run this file again to produce Setup.exe.
  pause
  exit /b 0
)

for /f %%V in ('python app.py --version') do set APPVER=%%V
"%ISCC%" /DMyAppVersion=%APPVER% installer\CoD2ChatTranslator.iss
if errorlevel 1 goto :fail

echo.
echo DONE. Release files are in: release\
pause
exit /b 0

:fail
echo.
echo Release build failed.
pause
exit /b 1
