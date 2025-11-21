@echo off
echo Uninstalling Digital Signature Agent...

:: Stop running instances
taskkill /f /im DigitalSignatureAgent.exe >nul 2>&1

:: Remove installation directory
rmdir /s /q "%PROGRAMFILES%\DigitalSignatureAgent"

:: Remove shortcuts
del "%USERPROFILE%\Desktop\DigitalSignatureAgent.lnk" >nul 2>&1
rmdir /s /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\DigitalSignatureAgent" >nul 2>&1

echo Uninstallation completed!
pause