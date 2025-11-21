@echo off
Title Building Digital Signature Agent - Windows
echo ===============================================
echo Building Digital Signature Agent Executable
echo ===============================================

REM Create necessary directories
if not exist "dist" mkdir "dist"
if not exist "build" mkdir "build"
if not exist "signed_docs" mkdir "signed_docs"
if not exist "unsigned_docs" mkdir "unsigned_docs"

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Build executable using PyInstaller
echo Building executable...
pyinstaller --onefile --windowed --icon=installer\icons\logo_icon.ico --name "Digitalsignature" main.py

if %errorlevel% equ 0 (
    echo.
    echo ===============================================
    echo Build successful!
    echo Executable: dist\Digitalsignature.exe
    echo ===============================================
    
    REM Ask to build installer
    set /p build_installer="Do you want to build the installer now? (y/n): "
    if /i "%build_installer%"=="y" (
        call installer\build_installer.bat
    )
) else (
    echo.
    echo ===============================================
    echo Build failed!
    echo ===============================================
)

pause