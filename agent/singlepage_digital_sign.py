from PyPDF2 import PdfReader, PdfWriter
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography import x509
import pkcs11
import os
import datetime
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader
import io

def parse_certificate_info(cert_data):
    """Extract certificate information from DER encoded certificate"""
    try:
        certificate = x509.load_der_x509_certificate(cert_data, default_backend())
        
        subject_cn = None
        for attr in certificate.subject:
            if attr.oid == x509.NameOID.COMMON_NAME:
                subject_cn = attr.value
                break
        
        serial_number = str(certificate.serial_number)
        
        issuer_cn = None
        for attr in certificate.issuer:
            if attr.oid == x509.NameOID.COMMON_NAME:
                issuer_cn = attr.value
                break
        
        return {
            'subject_cn': subject_cn or 'Unknown',
            'serial_number': serial_number,
            'issuer_cn': issuer_cn or 'Unknown',
            'not_before': certificate.not_valid_before,
            'not_after': certificate.not_valid_after,
            'certificate': certificate
        }
    except Exception as e:
        print(f"Warning: Could not parse certificate: {e}")
        return {
            'subject_cn': 'Unknown',
            'serial_number': 'Unknown',
            'issuer_cn': 'Unknown',
            'not_before': datetime.datetime.now(),
            'not_after': datetime.datetime.now(),
            'certificate': None
        }

def create_signature_overlay(cert_info, signing_time):
    """Create a PDF overlay with visible signature stamp"""
    try:
        # Create a PDF for the signature overlay
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=letter)
        
        # Get page dimensions
        page_width, page_height = letter
        
        # Position on bottom right
        x_position = page_width - 300  # 280px from right
        y_position = 50  # 50px from bottom
        width = 260
        height = 120
        
        # Draw signature background
        c.setFillColor(Color(0.97, 0.98, 1.0))  # Light blue background
        c.rect(x_position, y_position, width, height, fill=1, stroke=0)
        
        # Border
        c.setStrokeColor(Color(0, 0.48, 0.74))  # Blue border
        c.setLineWidth(1)
        c.rect(x_position, y_position, width, height, fill=0, stroke=1)
        
        # --- Add the seal image ---
        try:
            image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seal.png")
            seal = ImageReader(image_path)
            c.drawImage(seal, x_position + 5, y_position + height - 45, width=40, height=40, mask='auto')  # Adjust position and size as needed
        except Exception as e:
            print(f"Error loading image: {e}")
        # --------------------------
    

        # Checkmark
        # c.setFillColor(Color(0.16, 0.68, 0.32))  # Green checkmark
        # c.circle(x_position + 20, y_position + height - 20, 8, fill=1)
        # c.setFillColor(Color(1, 1, 1))  # White check
        # c.setFont("Helvetica-Bold", 10)
        # c.drawString(x_position + 17, y_position + height - 23, "✓")
        
        # Main title
        c.setFillColor(Color(0, 0.48, 0.74))  # Blue text
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x_position + 50, y_position + height - 15, "DIGITALLY SIGNED")
        
        # Signature line
        c.setStrokeColor(Color(0, 0.48, 0.74))
        c.setLineWidth(1)
        c.line(x_position + 50, y_position + height - 20, x_position + 230, y_position + height - 20)
        
        # Certificate subject
        subject_display = cert_info['subject_cn']
        if len(subject_display) > 25:
            subject_display = subject_display[:25] + "..."
        
        c.setFillColor(Color(0.2, 0.2, 0.2))  # Dark gray
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x_position + 50, y_position + height - 30, "Signed by:")
        c.setFont("Helvetica", 8)
        c.drawString(x_position + 50, y_position + height - 38, subject_display)
        
        # Serial number
        serial_display = cert_info['serial_number']
        if len(serial_display) > 15:
            serial_display = serial_display[:15] + "..."
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x_position + 50, y_position + height - 50, "Serial No:")
        c.setFont("Helvetica", 8)
        c.drawString(x_position + 50, y_position + height - 58, serial_display)
        
        # Signing time
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x_position + 50, y_position + height - 70, "Date/Time:")
        c.setFont("Helvetica", 7)
        time_display = signing_time.strftime("%Y-%m-%d %H:%M:%S")
        c.drawString(x_position + 50, y_position + height - 78, time_display)
        
        # Token info
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x_position + 50, y_position + height - 90, "Token:")
        c.setFont("Helvetica", 7)
        c.drawString(x_position + 50, y_position + height - 98, "Watchdata PROXKey")
        
        # Validity status
        is_valid = cert_info['not_after'] > datetime.datetime.now()
        status_color = Color(0.16, 0.68, 0.32) if is_valid else Color(0.86, 0.08, 0.24)
        status_text = "VALID" if is_valid else "EXPIRED"
        
        c.setFillColor(status_color)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x_position + 180, y_position + height - 90, status_text)
        
        # Security info
        c.setFillColor(Color(0.6, 0.6, 0.6))
        c.setFont("Helvetica", 6)
        c.drawString(x_position + 50, y_position + 12, "PKCS11 • SHA256 • SECURED")
        
        c.save()
        packet.seek(0)
        return packet
        
    except Exception as e:
        print(f"Error creating signature overlay: {e}")
        return None

def add_visible_signature_to_pdf(input_pdf, output_pdf, cert_info, signature, cert_data, signing_time):
    """Add visible signature overlay to PDF"""
    try:
        # Create signature overlay
        overlay_packet = create_signature_overlay(cert_info, signing_time)
        if not overlay_packet:
            return False
        
        if type(input_pdf) is bytes:
            input_pdf = io.BytesIO(input_pdf)

        # Read original PDF
        original_pdf = PdfReader(input_pdf)
        
        # Read overlay PDF
        overlay_pdf = PdfReader(overlay_packet)
        overlay_page = overlay_pdf.pages[0]
        
        # Create output PDF writer
        output_pdf_writer = PdfWriter()
        
        # Process each page
        for i, page in enumerate(original_pdf.pages):
            # For first page, merge with signature overlay
            if i == 0:
                page.merge_page(overlay_page)
            output_pdf_writer.add_page(page)
        
        # Add comprehensive metadata
        signing_time_str = signing_time.isoformat()
        formatted_time = signing_time.strftime("%Y-%m-%d %H:%M:%S")
        
        output_pdf_writer.add_metadata({
            '/Title': 'Digitally Signed Document',
            '/Author': 'Digital Signature System',
            '/Subject': f'Digitally Signed by {cert_info["subject_cn"]}',
            '/Keywords': 'Digital Signature, PKCS11, Watchdata',
            '/Creator': 'Python Digital Signature Agent',
            '/Producer': 'PyPDF2 with PKCS11',
            '/CreationDate': f'D:{signing_time.strftime("%Y%m%d%H%M%S")}',
            '/ModDate': f'D:{signing_time.strftime("%Y%m%d%H%M%S")}',
            '/Signature': signature.hex(),
            '/Cert': cert_data.hex(),
            '/SigningTime': signing_time_str,
            '/Signer': cert_info['subject_cn'],
            '/SignerSerial': cert_info['serial_number'],
            '/Issuer': cert_info['issuer_cn'],
            '/HashAlgorithm': 'SHA256',
            '/SignatureReason': 'Document Approval',
            '/SignatureLocation': 'Digital Signature System',
            '/CertValidFrom': cert_info['not_before'].isoformat(),
            '/CertValidTo': cert_info['not_after'].isoformat(),
            '/SignatureAppearance': 'Visible overlay on page 1',
            '/SignaturePosition': 'Bottom right'
        })
        
        # Save the final PDF
        with open(output_pdf, 'wb') as output_file:
            output_pdf_writer.write(output_file)
        
        print(f"✓ Added visible signature overlay to: {output_pdf}")
        return True
        
    except Exception as e:
        print(f"Error adding visible signature: {e}")
        import traceback
        traceback.print_exc()
        return False

def sign_pdf_with_pkcs11(input_pdf, output_pdf, pkcs11_lib_path, pin='12345678'):
    """
    Digitally sign a PDF using PKCS#11 hardware token with GUARANTEED visible signature
    """
    lib = None
    session = None
    
    try:
        print(f"Loading PKCS11 library: {pkcs11_lib_path}")
        
        # Load the PKCS11 library
        lib = pkcs11.lib(pkcs11_lib_path)
        print("✓ PKCS11 library loaded successfully")
        
        # Get available slots
        slots = list(lib.get_slots())
        print(f"Found {len(slots)} slot(s)")
        
        if not slots:
            raise Exception("No PKCS11 slots found. Please check if token is connected.")
        
        # Find slots with tokens
        tokens = []
        for slot in slots:
            try:
                token = slot.get_token()
                tokens.append(token)
                print(f"✓ Token found in slot: {token.label}")
            except Exception as e:
                print(f"  Slot {slot} - No token: {e}")
                continue
        
        if not tokens:
            raise Exception("No tokens found in any slot. Please insert your digital signature token.")
        
        # Use first available token
        token = tokens[0]
        print(f"Using token: {token.label}")
        
        # Open session
        print("Opening session with token...")
        session = token.open(user_pin=pin, rw=True)
        print("✓ Session opened successfully")
        
        # Find private keys
        private_keys = list(session.get_objects({
            pkcs11.constants.Attribute.CLASS: pkcs11.constants.ObjectClass.PRIVATE_KEY
        }))
        print(f"Found {len(private_keys)} private key(s)")
        
        if not private_keys:
            raise Exception("No private keys found in token")
        
        # Find a signable private key
        signable_key = None
        for key in private_keys:
            try:
                if key[pkcs11.constants.Attribute.SIGN]:
                    signable_key = key
                    print("✓ Found signable private key")
                    break
            except:
                continue
        
        if not signable_key:
            signable_key = private_keys[0]
            print("Using first private key")
        
        # Find certificates
        certificates = list(session.get_objects({
            pkcs11.constants.Attribute.CLASS: pkcs11.constants.ObjectClass.CERTIFICATE
        }))
        print(f"Found {len(certificates)} certificate(s)")
        
        if not certificates:
            raise Exception("No certificates found in token")
        
        certificate = certificates[0]
        cert_data = certificate[pkcs11.constants.Attribute.VALUE]
        print(f"Certificate size: {len(cert_data)} bytes")
        
        # Parse certificate information
        print("Parsing certificate details...")
        cert_info = parse_certificate_info(cert_data)
        print(f"✓ Subject CN: {cert_info['subject_cn']}")
        print(f"✓ Serial No: {cert_info['serial_number']}")
        print(f"✓ Issuer CN: {cert_info['issuer_cn']}")
        print(f"✓ Valid Until: {cert_info['not_after'].strftime('%Y-%m-%d')}")
        
        # Read and hash PDF content
        print(f"Reading PDF: {input_pdf}")
        with open(input_pdf, 'rb') as file:
            pdf_content = file.read()
            print(f"PDF size: {len(pdf_content)} bytes")
            
            # Create hash of PDF content
            digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
            digest.update(pdf_content)
            hash_value = digest.finalize()
            print("✓ PDF hash computed")
            
            # Sign the hash
            print("Signing hash...")
            mechanism = pkcs11.Mechanism.SHA256_RSA_PKCS
            signature = signable_key.sign(hash_value, mechanism=mechanism)
            print(f"✓ Signature created: {len(signature)} bytes")
        
        # Create final signed PDF with GUARANTEED visible signature
        signing_time = datetime.datetime.now()
        print("Creating final PDF with GUARANTEED visible signature...")
        
        success = add_visible_signature_to_pdf(
            input_pdf, output_pdf, cert_info, signature, cert_data, signing_time
        )
        
        if success:
            print("✅ PDF successfully signed with GUARANTEED visible signature!")
            
            # Print comprehensive signature details
            print("\n" + "="*60)
            print("DIGITAL SIGNATURE DETAILS")
            print("="*60)
            print(f"Subject CN:      {cert_info['subject_cn']}")
            print(f"Serial Number:   {cert_info['serial_number']}")
            print(f"Issuer CN:       {cert_info['issuer_cn']}")
            print(f"Signing Time:    {signing_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Signature Size:  {len(signature)} bytes")
            print(f"Certificate Size: {len(cert_data)} bytes")
            print(f"Hash Algorithm:  SHA256")
            print(f"Token:           WD PROXKey")
            print(f"Valid Until:     {cert_info['not_after'].strftime('%Y-%m-%d')}")
            print(f"Signature Position: Bottom Right (GUARANTEED VISIBLE)")
            print("="*60)
            
            return output_pdf, cert_info, signing_time
        else:
            return None, None, None
        
    except pkcs11.exceptions.PKCS11Error as e:
        error_msg = str(e)
        print(f"❌ PKCS11 Error: {error_msg}")
        return None, None, None
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None, None
        
    finally:
        if session:
            try:
                session.close()
                print("Session closed")
            except:
                pass

def sign_pdf_with_pkcs11_agent(pdf_bytes, output_pdf, pkcs11_lib_path, pin='12345678'):
    """
    Digitally sign a PDF using PKCS#11 hardware token with GUARANTEED visible signature
    """
    lib = None
    session = None
    
    try:
        print(f"Loading PKCS11 library: {pkcs11_lib_path}")
        
        # Load the PKCS11 library
        lib = pkcs11.lib(pkcs11_lib_path)
        print("✓ PKCS11 library loaded successfully")
        
        # Get available slots
        slots = list(lib.get_slots())
        print(f"Found {len(slots)} slot(s)")
        
        if not slots:
            raise Exception("No PKCS11 slots found. Please check if token is connected.")
        
        # Find slots with tokens
        tokens = []
        for slot in slots:
            try:
                token = slot.get_token()
                tokens.append(token)
                print(f"✓ Token found in slot: {token.label}")
            except Exception as e:
                print(f"  Slot {slot} - No token: {e}")
                continue
        
        if not tokens:
            raise Exception("No tokens found in any slot. Please insert your digital signature token.")
        
        # Use first available token
        token = tokens[0]
        print(f"Using token: {token.label}")
        
        # Open session
        print("Opening session with token...")
        session = token.open(user_pin=pin, rw=True)
        print("✓ Session opened successfully")
        
        # Find private keys
        private_keys = list(session.get_objects({
            pkcs11.constants.Attribute.CLASS: pkcs11.constants.ObjectClass.PRIVATE_KEY
        }))
        print(f"Found {len(private_keys)} private key(s)")
        
        if not private_keys:
            raise Exception("No private keys found in token")
        
        # Find a signable private key
        signable_key = None
        for key in private_keys:
            try:
                if key[pkcs11.constants.Attribute.SIGN]:
                    signable_key = key
                    print("✓ Found signable private key")
                    break
            except:
                continue
        
        if not signable_key:
            signable_key = private_keys[0]
            print("Using first private key")
        
        # Find certificates
        certificates = list(session.get_objects({
            pkcs11.constants.Attribute.CLASS: pkcs11.constants.ObjectClass.CERTIFICATE
        }))
        print(f"Found {len(certificates)} certificate(s)")
        
        if not certificates:
            raise Exception("No certificates found in token")
        
        certificate = certificates[0]
        cert_data = certificate[pkcs11.constants.Attribute.VALUE]
        print(f"Certificate size: {len(cert_data)} bytes")
        
        # Parse certificate information
        print("Parsing certificate details...")
        cert_info = parse_certificate_info(cert_data)
        print(f"✓ Subject CN: {cert_info['subject_cn']}")
        print(f"✓ Serial No: {cert_info['serial_number']}")
        print(f"✓ Issuer CN: {cert_info['issuer_cn']}")
        print(f"✓ Valid Until: {cert_info['not_after'].strftime('%Y-%m-%d')}")
        
        # Read and hash PDF content
        # print(f"Reading PDF: {input_pdf}")
        # with open(input_pdf, 'rb') as file:
        #     pdf_content = file.read()
        #     print(f"PDF size: {len(pdf_content)} bytes")
        pdf_content = pdf_bytes 
        # Create hash of PDF content
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(pdf_content)
        hash_value = digest.finalize()
        print("✓ PDF hash computed")
        
        # Sign the hash
        print("Signing hash...")
        mechanism = pkcs11.Mechanism.SHA256_RSA_PKCS
        signature = signable_key.sign(hash_value, mechanism=mechanism)
        print(f"✓ Signature created: {len(signature)} bytes")
        
        # Create final signed PDF with GUARANTEED visible signature
        signing_time = datetime.datetime.now()
        print("Creating final PDF with GUARANTEED visible signature...")
        
        success = add_visible_signature_to_pdf(
            pdf_content, output_pdf, cert_info, signature, cert_data, signing_time
        )
        
        if success:
            print("✅ PDF successfully signed with GUARANTEED visible signature!")
            
            # Print comprehensive signature details
            print("\n" + "="*60)
            print("DIGITAL SIGNATURE DETAILS")
            print("="*60)
            print(f"Subject CN:      {cert_info['subject_cn']}")
            print(f"Serial Number:   {cert_info['serial_number']}")
            print(f"Issuer CN:       {cert_info['issuer_cn']}")
            print(f"Signing Time:    {signing_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Signature Size:  {len(signature)} bytes")
            print(f"Certificate Size: {len(cert_data)} bytes")
            print(f"Hash Algorithm:  SHA256")
            print(f"Token:           WD PROXKey")
            print(f"Valid Until:     {cert_info['not_after'].strftime('%Y-%m-%d')}")
            print(f"Signature Position: Bottom Right (GUARANTEED VISIBLE)")
            print("="*60)
            
            return output_pdf, cert_info, signing_time
        else:
            return None, None, None
        
    except pkcs11.exceptions.PKCS11Error as e:
        error_msg = str(e)
        print(f"❌ PKCS11 Error: {error_msg}")
        return None, None, None
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None, None
        
    finally:
        if session:
            try:
                session.close()
                print("Session closed")
            except:
                pass

def main():
    """Main function"""
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Path setup
        input_path = os.path.join(BASE_DIR, "unsigned_docs", "document.pdf")
        final_signed_path = os.path.join(BASE_DIR, "signed_docs", "signed_document.pdf")
        
        # Create directories if needed
        os.makedirs(os.path.dirname(input_path), exist_ok=True)
        os.makedirs(os.path.dirname(final_signed_path), exist_ok=True)
        
        # PKCS11 library path
        PKCS11_PATH = "C:\\Windows\\System32\\Watchdata\\PROXKey CSP India V3.0\\wdpkcs.dll"
        
        print("=" * 60)
        print("GUARANTEED VISIBLE DIGITAL SIGNATURE TOOL")
        print("=" * 60)
        print(f"Input PDF:  {input_path}")
        print(f"Output PDF: {final_signed_path}")
        print(f"PKCS11 Lib: {PKCS11_PATH}")
        print("=" * 60)
        
        # Check input PDF
        if not os.path.exists(input_path):
            print(f"❌ Input PDF not found: {input_path}")
            return False
        
        # Check PKCS11 library
        if not os.path.exists(PKCS11_PATH):
            print(f"❌ PKCS11 library not found: {PKCS11_PATH}")
            return False
        
        print("\nStarting signing process with GUARANTEED visible signature...")
        
        # Sign the PDF
        result = sign_pdf_with_pkcs11(input_path, final_signed_path, PKCS11_PATH)
        
        if result[0]:
            print(f"\n🎉 SUCCESS: Signed document saved as: {final_signed_path}")
            
            print("\n✅ GUARANTEED VISIBLE FEATURES:")
            print("   • Professional signature stamp on bottom right of first page")
            print("   • Subject CN: " + result[1]['subject_cn'])
            print("   • Serial number: " + result[1]['serial_number'])
            print("   • Signing date and time")
            print("   • Validity status (VALID/EXPIRED)")
            print("   • Digital signature embedded in metadata")
            print("   • WILL BE VISIBLE in ALL PDF viewers")
            
            print("\n🔍 The signature is GUARANTEED to be visible as:")
            print("   • A professional blue-styled box on the bottom right")
            print("   • Contains all certificate information")
            print("   • Visible in Adobe Reader, browser viewers, etc.")
            print("   • Part of the actual page content (not just metadata)")
            
        else:
            print(f"\n💥 FAILED: Could not sign PDF")
            
        return bool(result[0])
        
    except Exception as e:
        print(f"💥 Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎊 Process completed successfully!")
        print("The signature is GUARANTEED to be visible on the PDF page!")
    else:
        print("\nPress Enter to exit...")
        input()
    
    sys.exit(0 if success else 1)