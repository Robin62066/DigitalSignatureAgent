@echo off
title Building Digital Signature Agent
echo ========================================
echo    Digital Signature Agent Builder
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher
    pause
    exit /b 1
)

echo Step 1: Setting up virtual environment...
if not exist "venv-eSign" (
    echo Creating virtual environment...
    python -m venv venv-eSign
)

echo Activating virtual environment...
call venv-eSign\Scripts\activate.bat

echo Step 2: Installing/upgrading dependencies...
pip install --upgrade pip
echo Installing from requirements.txt...
pip install -r requirements.txt
echo Installing PyInstaller...
pip install pyinstaller

echo Step 3: Creating necessary directories...
if not exist "dist" mkdir dist
if not exist "build" mkdir build
if not exist "installer\output" mkdir installer\output

echo Step 4: Building executable with PyInstaller...
echo This may take a few minutes...
:: Run PyInstaller
python -m PyInstaller --clean --noconfirm --onefile ^
    --windowed ^
    --name "DigitalSignatureAgent" ^
    --icon "common/images/logo_icon.ico" ^
    --add-data "agent;agent" ^
    --add-data "common;common" ^
    --add-data ".env;." ^
    --hidden-import=pkcs11 ^
    --hidden-import=flask ^
    --hidden-import=PIL ^
    --hidden-import=pystray ^
    main.py

if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Build completed successfully!
echo ========================================
echo Executable created: dist\DigitalSignatureAgent.exe
echo.
echo You can now:
echo 1. Test the executable with: test_installation.bat
echo 2. Build installer with: installer\build_installer.bat
echo 3. Or run build_all.bat to do everything
echo.
pause