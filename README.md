# 🧾 DigitalSignatureAgent

**DigitalSignatureAgent** is a lightweight client-side signing utility designed to digitally sign PDF documents using a **USB dongle (token)** that contains a valid **digital certificate (PKCS#11)**.  
It runs locally on the user’s computer and exposes a secure REST API that your **Django web application** (or any other web client) can interact with — ensuring that **the private key never leaves the token or client machine**.

---

## 🚀 Features

- 🔐 **Client-side digital signing** – private key remains securely in the USB token.
- 🧾 **PDF signing** – digitally sign PDF files in PKCS#7/PAdES-compliant format.
- 🧠 **Plug-and-play architecture** – easily integrate with any Django or web application.
- ⚙️ **Local REST API** – simple HTTP interface (`http://localhost:5001`) for PDF signing and status checking.
- 🪪 **PKCS#11 compatible** – supports tokens from Watchdata, ePass, SafeNet, and other vendors.
- 💡 **Cross-platform** – works on both **Windows** and **Ubuntu Linux** servers or desktops.
- 🧰 **Installer-ready** – packaged via **PyInstaller** for one-click installation and background startup.

---

## Project Structure

- **DigitalSignatureAgent**

  - common\images
    -logo-icon.ico
    -logo.png
    -seal.png
  - agent

    - main.py
    - config.py
    - pkcs11_utils.py
    - tray_gui.py
    - signer.py
    - version.py

  -installer
  -icons
  -logo_icon.ico
  -output
  -build_installer.bat
  -DigitalSignatureAgent_setup.exe
  -setup.nsi
  -uninstall.bat
  -dist
  -DigitalSignatureAgent.exe # for testing

  -build
  DigitalSignatureAgent
  -localpycs
  -pyimod01_achive.pyc
  -pyimod02_importers.pyc
  -pyimod03_dtypes.pyc
  -pyimod04_pywin32.pyc
  -struct.pyc
  -Analysis-00.toc
  -base_libarary.zip
  -DigitalSignatyreAgent.pkg
  -EXE-00.toc
  -PKG-00.toc
  -PYZ-00.toc
  -PYZ-00.pyz
  -warn-DititalSignatureAgent.txt
  -xref-DigitalSignatureAgent.html
  -signed_docs
  -unsigned_docs

  - .env
  - README.md
  - requirements.txt
  - setup.py
    -build_exe.bat
    -build_linux.sh
    -build_windows.bat
    -DigitalSignatureAgent-setup.exe
    -DigitalSignatureAgent.spec
    -installer.nsi
    -License.txt
    -main.py
    -main.spec

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/DigitalSignatureAgent.git
cd DigitalSignatureAgent
```
"# DigitalSignatureAgent" 
