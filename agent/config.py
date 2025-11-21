# agent/config.py - FIXED VERSION
import os
import sys


def get_base_path():
    """Get base path that works for both development and PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return base_path


BASE_DIR = get_base_path()
COMMON_DIR = os.path.join(BASE_DIR, "common")
IMAGES_DIR = os.path.join(COMMON_DIR, "images")

# For installed version - NO .ENV DEPENDENCIES
LOCAL_MODE = False
BASE_URL = "http://127.0.0.1:5001"

# Set default values for installed version
SECRET_KEY = "digital-signature-agent-secret-key"
SECRET_PASSWORD_KEY = "password-encryption-key"

PDF_SOURCE_BASE_URL = "http://10.10.1.13/uploads/unsigned_docs/"

AUTO_FETCH_PDF = True

PORT = 5001

# Create directories
os.makedirs(os.path.join(BASE_DIR, "unsigned_docs"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "signed_docs"), exist_ok=True)

UNSIGNED_DOCS_PATH = os.path.join(BASE_DIR, "unsigned_docs")
SIGNED_DOCS_PATH = os.path.join(BASE_DIR, "signed_docs")

# Set PKCS#11 library path - USE ABSOLUTE PATH
PKCS11_PATH = r"C:\Windows\System32\Watchdata\PROXKey CSP India V3.0\wdpkcs.dll"

# DB config - not needed for basic functionality
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "digital_signature",
    "user": "postgres",
    "password": "password",
}
