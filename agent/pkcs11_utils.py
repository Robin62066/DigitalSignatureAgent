import os
import io
import sys
import datetime
import traceback
import pkcs11
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from .config import IMAGES_DIR


class PKCS11Manager:
    def __init__(self, pkcs11_lib_path: str):
        """
        Initialize PKCS#11 Manager with the path to the PKCS#11 library.
        Example: 'C:\\Windows\\System32\\Watchdata\\PROXKey CSP India V3.0\\wdpkcs.dll'
        """
        self.pkcs11_lib_path = pkcs11_lib_path
        self.lib = None
        self.session = None

        # --------------------------------------------------------------------------
        # CERTIFICATE HANDLING
        # --------------------------------------------------------------------------

    def get_token_credentials(self, pin, cert_info_only=False):
        """
        Opens a PKCS#11 session using the provided PIN and retrieves the
        private key, raw certificate data, and parsed certificate info.
        This method is called by the Flask API.
        """
        try:
            print(
                f"[DEBUG] get_token_credentials called with pin: {pin}, cert_info_only: {cert_info_only}"
            )

            # Initialize PKCS11 library
            print(f"[DEBUG] Initializing PKCS11 library: {self.pkcs11_lib_path}")
            self.lib = pkcs11.lib(self.pkcs11_lib_path)

            # Find slots with tokens
            slots = list(self.lib.get_slots())
            print(f"[DEBUG] Found {len(slots)} slots")

            tokens = []
            for i, slot in enumerate(slots):
                try:
                    token = slot.get_token()
                    tokens.append(token)
                    print(f"[DEBUG] ✓ Token found in slot {i}: {token.label}")
                except Exception as e:
                    print(f"[DEBUG]   Slot {i} - No token: {e}")
                    continue

            if not tokens:
                raise Exception(
                    "No tokens found in any slot. Please insert your digital signature token."
                )

            # Use the first token found
            token = tokens[0]
            print(f"[DEBUG] Using token: {token.label}")

            # Open session with the token
            print(f"[DEBUG] Opening session with PIN...")
            self.session = token.open(user_pin=pin, rw=True)
            print(f"[DEBUG] Session opened successfully")

            # Find certificates
            print(f"[DEBUG] Searching for certificates...")
            certificates = list(
                self.session.get_objects(
                    {
                        pkcs11.constants.Attribute.CLASS: pkcs11.constants.ObjectClass.CERTIFICATE
                    }
                )
            )
            print(f"[DEBUG] Found {len(certificates)} certificate(s)")

            if not certificates:
                raise Exception("No certificates found in token")

            # Use the first certificate
            certificate = certificates[0]
            print(f"[DEBUG] Getting certificate data...")
            cert_data = certificate[pkcs11.constants.Attribute.VALUE]
            print(f"[DEBUG] Certificate data retrieved, length: {len(cert_data)}")

            # Parse certificate info
            cert_info = self.parse_certificate_info(cert_data)
            print(f"[DEBUG] Certificate info parsed successfully")

            # Find private key (only if needed for signing)
            key = None
            if not cert_info_only:
                print(f"[DEBUG] Searching for private keys...")
                private_keys = list(
                    self.session.get_objects(
                        {
                            pkcs11.constants.Attribute.CLASS: pkcs11.constants.ObjectClass.PRIVATE_KEY
                        }
                    )
                )
                print(f"[DEBUG] Found {len(private_keys)} private key(s)")

                if private_keys:
                    key = private_keys[0]
                    print(f"[DEBUG] Using private key for signing")
                else:
                    print(f"[DEBUG] No private keys found")

            # Close session if only cert info is needed
            if cert_info_only and self.session:
                print(f"[DEBUG] Closing session (cert_info_only=True)")
                self.session.close()
                self.session = None
            else:
                print(f"[DEBUG] Keeping session open for signing")

            print(f"[DEBUG] get_token_credentials completed successfully")
            return key, cert_data, cert_info

        except Exception as e:
            print(f"[DEBUG] get_token_credentials error: {e}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            # Close session on error
            if self.session:
                try:
                    self.session.close()
                    self.session = None
                    print(f"[DEBUG] Session closed due to error")
                except Exception as close_error:
                    print(f"[DEBUG] Error closing session: {close_error}")
            raise

    def parse_certificate_info(self, cert_data):
        """Extract certificate information from DER encoded certificate - ULTRA SAFE VERSION"""
        try:
            print(
                f"[DEBUG] parse_certificate_info: Starting with cert_data type: {type(cert_data)}, length: {len(cert_data) if cert_data else 0}"
            )

            # Check if cert_data is valid
            if not cert_data:
                print(
                    f"[DEBUG] parse_certificate_info: ERROR - cert_data is None or empty!"
                )
                now = datetime.datetime.now()
                safe_result = {
                    "subject_cn": "No Certificate Data",
                    "serial_number": "N/A",
                    "issuer_cn": "N/A",
                    "not_before": now,
                    "not_after": now,
                    "thumbprint": "N/A",
                    "certificate": None,
                }
                print(
                    f"[DEBUG] parse_certificate_info: Returning safe fallback: {safe_result}"
                )
                return safe_result

            print(f"[DEBUG] parse_certificate_info: Attempting to load certificate...")
            certificate = x509.load_der_x509_certificate(cert_data, default_backend())
            print(f"[DEBUG] parse_certificate_info: Certificate loaded successfully")

            # SAFELY extract subject CN - with maximum error handling
            subject_cn = "Unknown Subject"
            try:
                print(f"[DEBUG] parse_certificate_info: Extracting subject...")
                subject_attrs = list(certificate.subject)
                print(
                    f"[DEBUG] parse_certificate_info: Subject attributes count: {len(subject_attrs)}"
                )

                for i, attr in enumerate(subject_attrs):
                    print(
                        f"[DEBUG] parse_certificate_info: Subject attr {i}: {attr.oid} = {attr.value}"
                    )
                    if attr.oid == x509.NameOID.COMMON_NAME:
                        cn_value = attr.value
                        print(
                            f"[DEBUG] parse_certificate_info: Found CN: {cn_value} (type: {type(cn_value)})"
                        )

                        # ULTRA SAFE conversion to string
                        if cn_value is None:
                            subject_cn = "No Common Name"
                            print(f"[DEBUG] parse_certificate_info: CN value is None")
                        else:
                            try:
                                subject_cn = str(cn_value)
                                print(
                                    f"[DEBUG] parse_certificate_info: CN converted to string: {subject_cn}"
                                )
                            except Exception as str_error:
                                print(
                                    f"[DEBUG] parse_certificate_info: Error converting CN to string: {str_error}"
                                )
                                subject_cn = "Error Converting CN"
                        break
                else:
                    subject_cn = "No Common Name Found"
                    print(
                        f"[DEBUG] parse_certificate_info: No CN found in subject attributes"
                    )

            except Exception as e:
                print(
                    f"[DEBUG] parse_certificate_info: CRITICAL ERROR extracting subject: {e}"
                )
                print(
                    f"[DEBUG] parse_certificate_info: Subject traceback: {traceback.format_exc()}"
                )
                subject_cn = "Error Reading Subject"

            # SAFELY extract issuer CN
            issuer_cn = "Unknown Issuer"
            try:
                print(f"[DEBUG] parse_certificate_info: Extracting issuer...")
                issuer_attrs = list(certificate.issuer)
                print(
                    f"[DEBUG] parse_certificate_info: Issuer attributes count: {len(issuer_attrs)}"
                )

                for i, attr in enumerate(issuer_attrs):
                    print(
                        f"[DEBUG] parse_certificate_info: Issuer attr {i}: {attr.oid} = {attr.value}"
                    )
                    if attr.oid == x509.NameOID.COMMON_NAME:
                        cn_value = attr.value
                        print(
                            f"[DEBUG] parse_certificate_info: Found issuer CN: {cn_value} (type: {type(cn_value)})"
                        )

                        # ULTRA SAFE conversion to string
                        if cn_value is None:
                            issuer_cn = "No Issuer CN"
                        else:
                            try:
                                issuer_cn = str(cn_value)
                            except Exception as str_error:
                                print(
                                    f"[DEBUG] parse_certificate_info: Error converting issuer CN: {str_error}"
                                )
                                issuer_cn = "Error Converting Issuer CN"
                        break
                else:
                    issuer_cn = "No Issuer CN Found"
                    print(
                        f"[DEBUG] parse_certificate_info: No CN found in issuer attributes"
                    )

            except Exception as e:
                print(
                    f"[DEBUG] parse_certificate_info: CRITICAL ERROR extracting issuer: {e}"
                )
                issuer_cn = "Error Reading Issuer"

            # SAFELY handle serial number - PREVENT None FORMATTING
            serial_number = "N/A"
            try:
                print(f"[DEBUG] parse_certificate_info: Extracting serial number...")
                serial_obj = certificate.serial_number
                print(
                    f"[DEBUG] parse_certificate_info: Serial object: {serial_obj} (type: {type(serial_obj)})"
                )

                if serial_obj is None:
                    serial_number = "No Serial Number"
                    print(f"[DEBUG] parse_certificate_info: Serial number is None")
                else:
                    try:
                        serial_number = str(serial_obj)
                        print(
                            f"[DEBUG] parse_certificate_info: Serial converted to string: {serial_number}"
                        )
                    except Exception as str_error:
                        print(
                            f"[DEBUG] parse_certificate_info: Error converting serial to string: {str_error}"
                        )
                        serial_number = "Error Converting Serial"

            except Exception as e:
                print(
                    f"[DEBUG] parse_certificate_info: CRITICAL ERROR with serial number: {e}"
                )
                serial_number = "Error Reading Serial"

            # SAFELY handle dates - PREVENT None FORMATTING
            now = datetime.datetime.now()
            not_before = now
            not_after = now
            try:
                print(f"[DEBUG] parse_certificate_info: Extracting dates...")
                if (
                    hasattr(certificate, "not_valid_before_utc")
                    and certificate.not_valid_before_utc
                ):
                    not_before = certificate.not_valid_before_utc.replace(tzinfo=None)
                    print(f"[DEBUG] parse_certificate_info: not_before: {not_before}")
                elif (
                    hasattr(certificate, "not_valid_before")
                    and certificate.not_valid_before
                ):
                    not_before = certificate.not_valid_before.replace(tzinfo=None)
                    print(
                        f"[DEBUG] parse_certificate_info: not_before (legacy): {not_before}"
                    )
                else:
                    print(f"[DEBUG] parse_certificate_info: No not_before date found")

                if (
                    hasattr(certificate, "not_valid_after_utc")
                    and certificate.not_valid_after_utc
                ):
                    not_after = certificate.not_valid_after_utc.replace(tzinfo=None)
                    print(f"[DEBUG] parse_certificate_info: not_after: {not_after}")
                elif (
                    hasattr(certificate, "not_valid_after")
                    and certificate.not_valid_after
                ):
                    not_after = certificate.not_valid_after.replace(tzinfo=None)
                    print(
                        f"[DEBUG] parse_certificate_info: not_after (legacy): {not_after}"
                    )
                else:
                    print(f"[DEBUG] parse_certificate_info: No not_after date found")

            except Exception as e:
                print(f"[DEBUG] parse_certificate_info: CRITICAL ERROR with dates: {e}")
                # Keep default dates

            # SAFELY handle thumbprint - PREVENT None FORMATTING
            thumbprint = "N/A"
            try:
                print(f"[DEBUG] parse_certificate_info: Calculating thumbprint...")
                if certificate:
                    thumbprint_bytes = certificate.fingerprint(hashes.SHA256())
                    thumbprint = thumbprint_bytes.hex()
                    print(
                        f"[DEBUG] parse_certificate_info: Thumbprint calculated: {thumbprint}"
                    )
                else:
                    print(
                        f"[DEBUG] parse_certificate_info: Certificate object is None, cannot calculate thumbprint"
                    )
            except Exception as e:
                print(
                    f"[DEBUG] parse_certificate_info: CRITICAL ERROR with thumbprint: {e}"
                )
                thumbprint = "Error Calculating Thumbprint"

            # Build result with ALL values converted to safe strings
            result = {
                "subject_cn": str(subject_cn)
                if subject_cn is not None
                else "Unknown Subject",
                "serial_number": str(serial_number)
                if serial_number is not None
                else "Unknown Serial",
                "issuer_cn": str(issuer_cn)
                if issuer_cn is not None
                else "Unknown Issuer",
                "not_before": not_before,
                "not_after": not_after,
                "thumbprint": str(thumbprint)
                if thumbprint is not None
                else "Unknown Thumbprint",
                "certificate": certificate,
            }

            print(f"[DEBUG] parse_certificate_info: Final result:")
            for key, value in result.items():
                if key != "certificate":  # Skip the certificate object
                    print(f"[DEBUG]   {key}: {value} (type: {type(value)})")

            print(f"[DEBUG] parse_certificate_info: Completed successfully")
            return result

        except Exception as e:
            print(
                f"[DEBUG] parse_certificate_info: CRITICAL ERROR in entire function: {e}"
            )
            print(
                f"[DEBUG] parse_certificate_info: Full traceback: {traceback.format_exc()}"
            )
            now = datetime.datetime.now()
            safe_result = {
                "subject_cn": "Certificate Parse Error",
                "serial_number": "N/A",
                "issuer_cn": "N/A",
                "not_before": now,
                "not_after": now,
                "thumbprint": "N/A",
                "certificate": None,
            }
            return safe_result

    # --------------------------------------------------------------------------
    # PDF SIGNATURE OVERLAY CREATION
    # --------------------------------------------------------------------------

    def create_signature_overlay(self, cert_info, signing_time):
        """Create visible signature overlay"""
        try:
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=letter)
            page_width, page_height = letter

            # Position bottom-right
            x, y, w, h = page_width - 300, 315, 240, 120

            # Seal image - FIXED PATH
            try:
                # Try multiple locations for seal.png
                seal_paths = [
                    os.path.join(IMAGES_DIR, "seal.png"),  # common/images/seal.png
                    "seal.png",  # root directory
                ]

                image_path = None
                for path in seal_paths:
                    if os.path.exists(path):
                        image_path = path
                        print(f"[DEBUG] ✓ Found seal image at: {path}")
                        break

                # For PyInstaller bundled executable
                if not image_path:
                    base_path = getattr(sys, "_MEIPASS", "")
                    if base_path:
                        bundled_paths = [
                            os.path.join(base_path, "agent", "seal.png"),
                            os.path.join(base_path, "common", "images", "seal.png"),
                            os.path.join(base_path, "seal.png"),
                        ]
                        for path in bundled_paths:
                            if os.path.exists(path):
                                image_path = path
                                print(f"[DEBUG] ✓ Found seal image at bundled: {path}")
                                break

                if image_path and os.path.exists(image_path):
                    c.drawImage(
                        ImageReader(image_path),
                        x + 180,
                        y + h - 60,
                        width=40,
                        height=40,
                        mask="auto",
                    )
                    print(f"[DEBUG] ✓ Seal image added to signature overlay")
                else:
                    print(f"[DEBUG] ✗ Seal image not found in any location")
            except Exception as e:
                print(f"[DEBUG] Seal image error: {e}")

            # Signer info - safely handle None values
            subject = (
                str(cert_info.get("subject_cn", "Unknown"))[:25] + "..."
                if len(str(cert_info.get("subject_cn", "Unknown"))) > 25
                else str(cert_info.get("subject_cn", "Unknown"))
            )
            serial = (
                str(cert_info.get("serial_number", "Unknown"))[:15] + "..."
                if len(str(cert_info.get("serial_number", "Unknown"))) > 15
                else str(cert_info.get("serial_number", "Unknown"))
            )

            # All fields in horizontal layout with reduced vertical spacing
            c.setFillColor(Color(0.2, 0.2, 0.2))

            # Signed by - on one line with reduced vertical gap
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x + 50, y + h - 35, "Signed by:  ")
            c.setFont("Helvetica", 8)
            c.drawString(x + 50 + 50, y + h - 35, subject)

            # Serial No - on one line with reduced vertical gap
            c.setFont("Helvetica-Bold", 9)
            c.drawString(
                x + 50, y + h - 47, "Serial No:  "
            )  # Reduced from -50 to -47 (3px less)
            c.setFont("Helvetica", 8)
            c.drawString(x + 50 + 50, y + h - 47, serial)  # Reduced from -50 to -47

            # Date/Time - on one line with reduced vertical gap
            c.setFont("Helvetica-Bold", 9)
            c.drawString(
                x + 50, y + h - 59, "Date/Time:  "
            )  # Reduced from -65 to -59 (6px less)
            c.setFont("Helvetica", 7)
            c.drawString(
                x + 50 + 50, y + h - 59, signing_time.strftime("%Y-%m-%d %H:%M:%S")
            )  # Reduced from -65 to -59

            # Token - on one line with reduced vertical gap
            c.setFont("Helvetica-Bold", 9)
            c.drawString(
                x + 50, y + h - 71, "Token:  "
            )  # Reduced from -80 to -71 (9px less)
            c.setFont("Helvetica", 7)
            c.drawString(
                x + 50 + 50, y + h - 71, "Watchdata PROXKey"
            )  # Reduced from -80 to -71

            # Validity status - positioned to the right
            valid = (
                cert_info.get("not_after", datetime.datetime.now())
                > datetime.datetime.now()
            )
            c.setFillColor(
                Color(0.16, 0.68, 0.32) if valid else Color(0.86, 0.08, 0.24)
            )
            c.setFont("Helvetica-Bold", 8)
            c.drawString(
                x + 180, y + h - 71, "VALID" if valid else "EXPIRED"
            )  # Reduced from -80 to -71

            # Footer - moved up significantly to reduce space
            c.setFillColor(Color(0.6, 0.6, 0.6))
            c.setFont("Helvetica", 6)
            c.drawString(
                x + 50, y + h - 83, "PKCS11 • SHA256 • SECURED"
            )  # Changed from y + 8 to y + 5 (3px less)

            c.save()
            packet.seek(0)
            return packet

        except Exception as e:
            print(f"[DEBUG] Error creating overlay: {e}")
            return None

    # --------------------------------------------------------------------------
    # PDF SIGNING LOGIC
    # --------------------------------------------------------------------------
    def add_visible_signature(
        self, input_pdf, output_pdf, cert_info, signature, cert_data, signing_time
    ):
        """Add visible signature box to PDF"""
        try:
            overlay = self.create_signature_overlay(cert_info, signing_time)
            if not overlay:
                raise Exception("Overlay creation failed")

            if isinstance(input_pdf, bytes):
                input_pdf = io.BytesIO(input_pdf)

            original = PdfReader(input_pdf)
            overlay_pdf = PdfReader(overlay)
            overlay_page = overlay_pdf.pages[0]

            writer = PdfWriter()
            for i, page in enumerate(original.pages):
                if i == 0:
                    page.merge_page(overlay_page)
                writer.add_page(page)

            writer.add_metadata(
                {
                    "/Title": "Digitally Signed Document",
                    "/Author": cert_info.get("subject_cn", "Unknown"),
                    "/Signer": cert_info.get("subject_cn", "Unknown"),
                    "/SigningTime": signing_time.isoformat(),
                    "/Signature": signature.hex(),
                }
            )

            with open(output_pdf, "wb") as out_file:
                writer.write(out_file)

            print(f"[DEBUG] ✓ Signature applied to {output_pdf}")
            return True

        except Exception as e:
            print(f"[DEBUG] Error adding signature: {e}")
            return False

    # --------------------------------------------------------------------------
    # MAIN SIGNING METHOD
    # --------------------------------------------------------------------------
    def sign_pdf(self, input_pdf: str | bytes, output_pdf: str, pin: str):
        """
        Digitally signs a PDF file using the private key and certificate
        stored in the connected PKCS#11 token.

        Args:
            input_pdf (str | bytes): Path to the input PDF file or raw PDF bytes.
            output_pdf (str): Path to save the signed PDF file.
            pin (str): User PIN for token authentication.

        Returns:
            bool: True if the PDF was signed successfully, False otherwise.
        """
        try:
            print(f"[DEBUG] Starting PDF signing process")
            key, cert_data, cert_info = self.get_token_credentials(pin)

            if isinstance(input_pdf, bytes):
                pdf_data = input_pdf
            else:
                with open(input_pdf, "rb") as f:
                    pdf_data = f.read()

            digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
            digest.update(pdf_data)
            pdf_hash = digest.finalize()

            signature = key.sign(pdf_hash, mechanism=pkcs11.Mechanism.SHA256_RSA_PKCS)

            signing_time = datetime.datetime.now()
            success = self.add_visible_signature(
                input_pdf, output_pdf, cert_info, signature, cert_data, signing_time
            )

            return success

        except Exception as e:
            print(f"[DEBUG] Error during signing: {e}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return False
        finally:
            if self.session:
                try:
                    self.session.close()
                except:
                    pass

    def get_token_credentials(self, pin, cert_info_only=False):
        """
        Opens a PKCS#11 session using the provided PIN and retrieves the
        private key, raw certificate data, and parsed certificate info
        from the connected token.
        """
        try:
            print(f"[DEBUG] Starting get_token_credentials with PIN: {pin}")
            print(f"[DEBUG] PKCS11 library path: {self.pkcs11_lib_path}")

            # Initialize PKCS11 library
            print(f"[DEBUG] Initializing PKCS11 library...")
            self.lib = pkcs11.lib(self.pkcs11_lib_path)
            print(f"[DEBUG] PKCS11 library initialized successfully")

            # Find slots with tokens
            print(f"[DEBUG] Getting slots...")
            slots = list(self.lib.get_slots())
            print(f"[DEBUG] Found {len(slots)} slots")

            tokens = []
            for i, slot in enumerate(slots):
                try:
                    print(f"[DEBUG] Checking slot {i}...")
                    token = slot.get_token()
                    token_label = getattr(token, "label", "Unknown")
                    print(f"[DEBUG] ✓ Token found in slot {i}: {token_label}")
                    tokens.append(token)
                except Exception as e:
                    print(f"[DEBUG]   Slot {i} - No token: {e}")
                    continue

            if not tokens:
                raise Exception(
                    "No tokens found in any slot. Please insert your digital signature token."
                )

            token = tokens[0]  # Use first token found
            print(f"[DEBUG] Using token: {getattr(token, 'label', 'Unknown')}")

            # Open session
            print(f"[DEBUG] Opening session with PIN...")
            self.session = token.open(user_pin=pin, rw=True)
            print(f"[DEBUG] Session opened successfully")

            # Find private keys
            print(f"[DEBUG] Searching for private keys...")
            private_keys = list(
                self.session.get_objects(
                    {
                        pkcs11.constants.Attribute.CLASS: pkcs11.constants.ObjectClass.PRIVATE_KEY
                    }
                )
            )
            print(f"[DEBUG] Found {len(private_keys)} private key(s)")

            if not private_keys:
                raise Exception("No private keys found in token")

            # Find a signable private key
            print(f"[DEBUG] Finding signable private key...")
            signable_key = None
            for i, key in enumerate(private_keys):
                try:
                    print(f"[DEBUG] Checking key {i} for signing capability...")
                    can_sign = key[pkcs11.constants.Attribute.SIGN]
                    print(f"[DEBUG] Key {i} - SIGN attribute: {can_sign}")
                    if can_sign:
                        signable_key = key
                        print(f"[DEBUG] Using signable key {i}")
                        break
                except Exception as e:
                    print(f"[DEBUG] Key {i} - Error checking SIGN: {e}")
                    continue

            if not signable_key:
                signable_key = private_keys[0]
                print(f"[DEBUG] Using first key as fallback")

            # Find certificates
            print(f"[DEBUG] Searching for certificates...")
            certificates = list(
                self.session.get_objects(
                    {
                        pkcs11.constants.Attribute.CLASS: pkcs11.constants.ObjectClass.CERTIFICATE
                    }
                )
            )
            print(f"[DEBUG] Found {len(certificates)} certificate(s)")

            if not certificates:
                raise Exception("No certificates found in token")

            certificate = certificates[0]
            print(f"[DEBUG] Using first certificate")

            # Get certificate data with safe attribute access
            print(f"[DEBUG] Getting certificate VALUE attribute...")
            try:
                cert_data = certificate[pkcs11.constants.Attribute.VALUE]
                print(
                    f"[DEBUG] Certificate data retrieved, length: {len(cert_data) if cert_data else 0}"
                )
            except Exception as e:
                print(f"[DEBUG] Error getting certificate VALUE: {e}")
                raise Exception(f"Failed to read certificate data: {e}")

            # Parse certificate info
            print(f"[DEBUG] Parsing certificate info...")
            cert_info = self.parse_certificate_info(cert_data)
            print(f"[DEBUG] Certificate info parsed successfully")

            # Debug print all certificate info values
            print(f"[DEBUG] Certificate info values:")
            for key, value in cert_info.items():
                if key != "certificate":  # Skip the actual certificate object
                    print(f"[DEBUG]   {key}: {value} (type: {type(value)})")

            if cert_info_only:
                print(f"[DEBUG] cert_info_only=True, closing session...")
                # close session if only cert info is needed
                if self.session:
                    try:
                        self.session.close()
                        self.session = None
                        print(f"[DEBUG] Session closed")
                    except Exception as e:
                        print(f"[DEBUG] Error closing session: {e}")
                return None, cert_data, cert_info
            else:
                print(f"[DEBUG] Returning key and certificate info for signing")
                return signable_key, cert_data, cert_info

        except Exception as e:
            print(f"[DEBUG] Error in get_token_credentials: {e}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            # Ensure session is closed on error
            if self.session:
                try:
                    self.session.close()
                    self.session = None
                except:
                    pass
            raise
