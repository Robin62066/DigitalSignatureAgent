# agent/main.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from .pkcs11_utils import PKCS11Manager
import base64
import os
from .config import PKCS11_PATH, PORT
import traceback
import requests


app = Flask(__name__)

# Allow only your Django domain
# CORS(
#     app,
#     resources={r"/*": {"origins": ["http://127.0.0.1:8000", "http://localhost:8000"]}},
# )

# For testing, allow all origins (not recommended for production)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/")
def index():
    return """
    <html>
        <head><title>Digital Signature Agent</title></head>
        <body>
            <h1>Digital Signature Agent is Running</h1>
            <p>Service is active on port 5001</p>
            <p>Close this window to stop the service</p>
        </body>
    </html>
    """


@app.route("/status", methods=["POST", "GET"])
def status():
    return jsonify({"status": "running", "os": os.name})


@app.route("/cert-info", methods=["POST", "GET"])
def cert_info():
    try:
        print("[API] Certificate info request received")

        # -----------------------
        # Extract PIN
        # -----------------------
        if request.method == "GET":
            pin = request.args.get("pin")
        else:
            data = request.get_json() or {}
            pin = data.get("pin")

        if not pin:
            pin = "12345678"

        print(f"[API] Using PIN: {pin}")

        # -----------------------
        # Initialize PKCS11
        # -----------------------
        from agent.pkcs11_utils import PKCS11Manager
        from agent.config import PKCS11_PATH

        mgr = PKCS11Manager(PKCS11_PATH)

        try:
            key, cert_data, cert_info_data = mgr.get_token_credentials(
                pin, cert_info_only=True
            )

        except Exception as e:
            raw = repr(e)
            err = str(e).lower().strip()

            print(f"[CERT ERROR RAW]: {raw}")
            print(f"[CERT ERROR STR]: '{err}'")

            # ✅ Case 1: EMPTY ERROR → ALWAYS WRONG PIN
            if err == "" or err is None:
                return jsonify(
                    {"error": "Incorrect PIN", "error_type": "wrong_pin"}
                ), 400

            # ✅ Case 2: Wrong PIN
            wrong_pin_patterns = [
                "wrong pin",
                "incorrect pin",
                "ckr_pin_incorrect",
                "ckr_pin_invalid",
                "bad pin",
                "user pin",
                "invalid pin",
            ]
            if any(p in err for p in wrong_pin_patterns):
                return jsonify(
                    {"error": "Incorrect PIN", "error_type": "wrong_pin"}
                ), 400

            # ✅ Dongle missing
            if any(k in err for k in ["token", "dongle", "slot", "not present"]):
                return jsonify(
                    {
                        "error": "USB Token/Dongle not detected",
                        "error_type": "dongle_missing",
                    }
                ), 400

            # ✅ Token locked
            if "locked" in err or "too many" in err:
                return jsonify(
                    {
                        "error": "Token locked due to repeated wrong attempts",
                        "error_type": "token_locked",
                    }
                ), 400

            # ✅ PKCS11 library missing
            if "pkcs11" in err or "pkcs" in err:
                return jsonify(
                    {
                        "error": "PKCS#11 module failed to load",
                        "error_type": "pkcs11_load_error",
                    }
                ), 500

            # ✅ LAST FALLBACK
            return jsonify(
                {
                    "error": err or "Unknown certificate error",
                    "error_type": "unknown_error",
                }
            ), 500

        # -----------------------
        # SUCCESS RESPONSE
        # -----------------------
        return jsonify(
            {
                "status": "success",
                "certificates": {
                    "subject_cn": str(cert_info_data.get("subject_cn", "")),
                    "serial_number": str(cert_info_data.get("serial_number", "")),
                    "issuer_cn": str(cert_info_data.get("issuer_cn", "")),
                    "thumbprint": str(cert_info_data.get("thumbprint", "")),
                    "not_before": cert_info_data.get("not_before").isoformat()
                    if cert_info_data.get("not_before")
                    else "",
                    "not_after": cert_info_data.get("not_after").isoformat()
                    if cert_info_data.get("not_after")
                    else "",
                },
            }
        )

    except Exception as e:
        print(f"[API] CRITICAL FAILURE: {e}")
        return jsonify({"error": str(e), "error_type": "critical_failure"}), 500


def fetch_pdf_from_url(pdf_filename):
    """Fetch specific PDF from the configured URL"""
    try:
        from .config import PDF_SOURCE_BASE_URL

        if not pdf_filename:
            raise Exception("PDF filename is required")

        # Ensure the filename has .pdf extension
        if not pdf_filename.lower().endswith(".pdf"):
            pdf_filename += ".pdf"

        pdf_url = f"{PDF_SOURCE_BASE_URL}{pdf_filename}"

        print(f"[PDF-FETCH] Fetching PDF from: {pdf_url}")

        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()

        # Validate PDF content
        if not response.content.startswith(b"%PDF"):
            raise Exception("Downloaded content is not a valid PDF file")

        print(
            f"[PDF-FETCH] Successfully fetched {pdf_filename}, size: {len(response.content)} bytes"
        )
        return response.content

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise Exception(f"PDF file not found on server: {pdf_filename}")
        else:
            raise Exception(f"Server error: {e}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {e}")
    except Exception as e:
        raise Exception(f"Error fetching PDF: {e}")


@app.route("/sign-pdf", methods=["POST"])
def sign_pdf():
    try:
        data = request.get_json() or {}
        pin = data.get("pin")
        pdf_filename = data.get("pdf_filename")  # Required: specific filename

        if not pin:
            return jsonify(
                {"error": "PIN is required", "error_type": "missing_pin"}
            ), 400

        if not pdf_filename:
            return jsonify(
                {"error": "PDF filename missing", "error_type": "missing_pdf_file"}
            ), 400

        print(f"[SIGN-PDF] Starting signing process for: {pdf_filename}")

        # AUTO-FETCH PDF from URL with provided filename
        from .config import AUTO_FETCH_PDF

        if AUTO_FETCH_PDF:
            print(f"[SIGN-PDF] Auto-fetch enabled for: {pdf_filename}")
            pdf_bytes = fetch_pdf_from_url(pdf_filename)
        else:
            # Fallback to original base64 method
            pdf_b64 = data.get("pdf_base64")
            if not pdf_b64:
                return jsonify({"error": "Missing PDF data"}), 400
            pdf_bytes = base64.b64decode(pdf_b64.encode("utf-8"))
            print(f"[SIGN-PDF] Using base64 PDF data, size: {len(pdf_bytes)} bytes")

        # Generate output filename based on original
        from .config import SIGNED_DOCS_PATH

        # Clean filename for output
        original_name = os.path.splitext(pdf_filename)[0]
        if original_name:
            # remove prefix "unsingedDoc_"
            cleaned_name = original_name.replace("unsingedDoc_", "")

        output_filename = f"signedDoc_{cleaned_name}.pdf"
        signed_pdf_path = os.path.join(SIGNED_DOCS_PATH, output_filename)

        # Initialize PKCS#11 manager and sign PDF
        print(f"[SIGN-PDF] Initializing PKCS11 manager...")
        manager = PKCS11Manager(PKCS11_PATH)

        print(f"[SIGN-PDF] Starting PDF signing...")
        isSuccess = manager.sign_pdf(pdf_bytes, signed_pdf_path, pin)

        if isSuccess:
            print(f"[SIGN-PDF] SUCCESS: Signed document saved as: {signed_pdf_path}")

            # Read the signed PDF and return as base64
            with open(signed_pdf_path, "rb") as f:
                signed_pdf_bytes = f.read()

            signed_b64 = base64.b64encode(signed_pdf_bytes).decode("utf-8")

            return jsonify(
                {
                    "status": "success",
                    "message": "PDF signed successfully",
                    "signed_pdf": signed_b64,
                    "original_filename": pdf_filename,
                    "output_filename": output_filename,
                    "saved_path": signed_pdf_path,
                }
            )
        else:
            print(f"[SIGN-PDF] FAILED: Could not sign PDF")
            return jsonify({"error": "PDF signing failed"}), 500

    except Exception as e:
        err = str(e).lower()
        print(f"[SIGN-PDF] ERROR: {err}")

        if "not found" in err or "no such file" in err:
            return jsonify(
                {
                    "error": f"PDF not found on server: {pdf_filename}",
                    "error_type": "pdf_not_found",
                }
            ), 404

        if "pin" in err and ("wrong" in err or "incorrect" in err):
            return jsonify({"error": "Incorrect PIN", "error_type": "wrong_pin"}), 400

        if "token" in err or "dongle" in err:
            return jsonify(
                {"error": "USB Token/Dongle missing", "error_type": "dongle_missing"}
            ), 400

        # fallback
        return jsonify({"error": str(e), "error_type": "signing_failed"}), 500


def run():
    app.run(host="127.0.0.1", port=PORT)


if __name__ == "__main__":
    run()
