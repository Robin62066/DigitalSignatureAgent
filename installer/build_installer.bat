@echo off
title Digital Signature Agent Installer Builder
echo ========================================
echo    Installer Builder
echo ========================================
echo.

:: Change to project root directory
cd /d "%~dp0.."
echo Current directory: %CD%

echo Step 1: Checking if executable exists...
if not exist "dist\DigitalSignatureAgent.exe" (
    echo ERROR: DigitalSignatureAgent.exe not found in dist folder!
    echo Please run the build process first.
    pause
    exit /b 1
)

echo Step 2: Checking for NSIS...
set "NSIS_PATH=C:\Program Files (x86)\NSIS\makensis.exe"
if not exist "%NSIS_PATH%" (
    set "NSIS_PATH=C:\Program Files\NSIS\makensis.exe"
    if not exist "%NSIS_PATH%" (
        echo ERROR: NSIS not found!
        pause
        exit /b 1
    )
)

echo Found NSIS at: %NSIS_PATH%

echo Step 3: Creating LICENSE file if missing...
if not exist "LICENSE.txt" (
    echo Creating LICENSE.txt...
    echo Digital Signature Agent>LICENSE.txt
    echo Copyright 2024 Your Company>>LICENSE.txt
    echo.>>LICENSE.txt
    echo License agreement>>LICENSE.txt
)

echo Step 4: Building installer with NSIS...
echo Using simple installer...
"%NSIS_PATH%" "installer\setup.nsi"

if errorlevel 1 (
    echo ERROR: NSIS build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo    SUCCESS! Installer created!
echo ========================================
echo Installer: DigitalSignatureAgent_Setup.exe
echo.
pause