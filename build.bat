@echo off
echo Building Digital Signature Agent...
pyinstaller --onefile --noconsole --name "DigitalSignatureAgent" --icon=common/images/logo_icon.ico --add-data "common/images/logo.png;common/images" --add-data ".env;." main.py
echo Build complete!
pause