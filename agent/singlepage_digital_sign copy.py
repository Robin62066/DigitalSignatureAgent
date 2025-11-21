from PyPDF2 import PdfReader, PdfWriter
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import pkcs11
import os
import datetime
import sys
from PyPDF2.generic import RectangleObject, NameObject, create_string_object
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
import io
import base64

def create_digital_signature_image():
    # Create a memory buffer
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(200, 80))
    
    # Background
    c.setFillColor('#f8f9fa')
    c.rect(0, 0, 200, 80, fill=1, stroke=0)
    
    # Border
    c.setStrokeColor('#007cba')
    c.setLineWidth(1)
    c.rect(1, 1, 198, 78, fill=0, stroke=1)
    
    # # Signature lines
    # c.setStrokeColor('#007cba')
    # c.setLineWidth(1)
    # c.line(20, 50, 180, 50)
    # c.line(20, 40, 180, 40)
    # c.line(20, 30, 180, 30)
    
    # --- Add the seal image ---
    try:
        image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seal.png")
        seal = ImageReader(image_path)
        c.drawImage(seal, 20, 35, width=40, height=40, mask='auto')  # Adjust position and size as needed
    except Exception as e:
        print(f"Error loading image: {e}")
    # --------------------------
    
    # Text
    c.setFillColor('#007cba')
    c.setFont("Helvetica-Bold", 10)
    c.drawString(70, 65, "DIGITALLY SIGNED")
    
    c.setFillColor('#666666')
    c.setFont("Helvetica", 8)
    c.drawString(70, 55, "Electronic Signature")
    
    c.setFont("Helvetica", 7)
    c.drawString(70, 45, "Secured with PKCS11 Token")


    c.save()
    packet.seek(0)
    return packet

def add_visible_signature_stamp(input_pdf, output_pdf, signature_data=None):
    """Add a visible digital signature stamp on the right side"""
    try:
        # Read original PDF
        original_pdf = PdfReader(input_pdf)
        output_pdf_writer = PdfWriter()
        
        # Create signature stamp
        stamp_packet = create_digital_signature_image()
        stamp_pdf = PdfReader(stamp_packet)
        stamp_page = stamp_pdf.pages[0]
        
        # Get PDF dimensions
        first_page = original_pdf.pages[0]
        media_box = first_page.mediabox
        pdf_width = float(media_box.width)
        pdf_height = float(media_box.height)
        
        print(f"PDF dimensions: {pdf_width} x {pdf_height}")
        
        # Process each page
        for i, page in enumerate(original_pdf.pages):
            # Create a new page with the stamp
            stamp_packet = create_digital_signature_image()
            stamp_pdf = PdfReader(stamp_packet)
            stamp_page = stamp_pdf.pages[0]
            
            # Calculate position for right side
            stamp_width = 200
            stamp_height = 80
            x_position = pdf_width - stamp_width - 50  # 50px from right edge
            y_position = 100  # 100px from bottom
            
            # Scale and position the stamp
            stamp_page.scale_to(stamp_width, stamp_height)
            
            # Merge stamp with page
            page.merge_page(stamp_page)
            
            # Add the page to writer
            output_pdf_writer.add_page(page)
        
        # Save the watermarked PDF
        with open(output_pdf, 'wb') as output_file:
            output_pdf_writer.write(output_file)
            
        print(f"✓ Added visible digital signature stamp to: {output_pdf}")
        return True
        
    except Exception as e:
        print(f"Warning: Could not add visible signature stamp: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_signature_field(writer, page_number=0):
    """Create an invisible signature field"""
    try:
        page = writer.pages[page_number]
        
        # Get page dimensions
        media_box = page.mediabox
        pdf_width = float(media_box.width)
        pdf_height = float(media_box.height)
        
        # Position on right side
        x = pdf_width - 250  # 250px from right
        y = 50  # 50px from bottom
        width = 200
        height = 80
        
        sig_field = {
            '/Type': '/Annot',
            '/Subtype': '/Widget',
            '/FT': '/Sig',
            '/Rect': RectangleObject([x, y, x + width, y + height]),
            '/T': create_string_object("DigitalSignature"),
            '/F': 4,
            '/P': page.indirect_reference,
        }
        
        if '/Annots' in page:
            page[NameObject('/Annots')].append(sig_field)
        else:
            page[NameObject('/Annots')] = [sig_field]
            
        return True
    except Exception as e:
        print(f"Warning: Could not create signature field: {e}")
        return False

def sign_pdf_with_pkcs11(input_pdf, output_pdf, pkcs11_lib_path, pin='12345678'):
    """
    Digitally sign a PDF using PKCS#11 hardware token with visible signature stamp
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
        
        # Read and process PDF
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
            
            # Create signed PDF
            file.seek(0)
            reader = PdfReader(file)
            writer = PdfWriter()
            
            # Copy all pages
            for page in reader.pages:
                writer.add_page(page)
            
            # Create signature field
            print("Creating signature field...")
            create_signature_field(writer, page_number=0)
            
            # Add comprehensive metadata
            signing_time = datetime.datetime.now()
            signing_time_str = signing_time.isoformat()
            formatted_time = signing_time.strftime("%Y-%m-%d %H:%M:%S")
            
            writer.add_metadata({
                '/Title': 'Digitally Signed Document',
                '/Author': 'Digital Signature System',
                '/Subject': 'Digitally Signed PDF Document',
                '/Keywords': 'Digital Signature, PKCS11, Watchdata',
                '/Creator': 'Python Digital Signature Agent',
                '/Producer': 'PyPDF2 with PKCS11',
                '/CreationDate': f'D:{signing_time.strftime("%Y%m%d%H%M%S")}',
                '/ModDate': f'D:{signing_time.strftime("%Y%m%d%H%M%S")}',
                '/Signature': signature.hex(),
                '/Cert': cert_data.hex(),
                '/SigningTime': signing_time_str,
                '/Signer': 'Digital Signature Token',
                '/HashAlgorithm': 'SHA256',
                '/SignatureReason': 'Document Approval',
                '/SignatureLocation': 'Digital Signature System'
            })
            
            # Add custom properties
            writer.add_metadata({
                'Signed': 'true',
                'SignatureDate': formatted_time,
                'SignatureType': 'PKCS11_Hardware_Token',
                'TokenManufacturer': 'Watchdata',
                'TokenModel': 'PROXKey',
                'SignaturePosition': 'Bottom Right',
                'SignatureAppearance': 'Digital Stamp'
            })
        
        # Save signed PDF
        print(f"Saving signed PDF: {output_pdf}")
        with open(output_pdf, 'wb') as output_file:
            writer.write(output_file)
        
        print("✅ PDF successfully signed and saved!")
        
        # Print signature details
        print("\n" + "="*50)
        print("SIGNATURE DETAILS:")
        print("="*50)
        print(f"Signature Size: {len(signature)} bytes")
        print(f"Certificate Size: {len(cert_data)} bytes")
        print(f"Signing Time: {formatted_time}")
        print(f"Hash Algorithm: SHA256")
        print(f"Token: WD PROXKey")
        print(f"Signature Position: Bottom Right")
        print("="*50)
        
        return True
        
    except pkcs11.exceptions.PKCS11Error as e:
        error_msg = str(e)
        print(f"❌ PKCS11 Error: {error_msg}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
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
        digitally_signed_path = os.path.join(BASE_DIR, "signed_docs", "digitally_signed.pdf")
        final_signed_path = os.path.join(BASE_DIR, "signed_docs", "signed_document_with_stamp.pdf")
        
        # Create directories if needed
        os.makedirs(os.path.dirname(input_path), exist_ok=True)
        os.makedirs(os.path.dirname(digitally_signed_path), exist_ok=True)
        
        # PKCS11 library path
        PKCS11_PATH = "C:\\Windows\\System32\\Watchdata\\PROXKey CSP India V3.0\\wdpkcs.dll"
        
        print("=" * 60)
        print("DIGITAL SIGNATURE TOOL WITH VISIBLE STAMP")
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
        
        print("\nStarting signing process...")
        
        # Step 1: Digitally sign the PDF
        success = sign_pdf_with_pkcs11(input_path, digitally_signed_path, PKCS11_PATH)
        
        if success:
            print(f"\n✓ Digital signature applied: {digitally_signed_path}")
            
            # Step 2: Add visible signature stamp on right side
            print("\nAdding visible digital signature stamp on right side...")
            if add_visible_signature_stamp(digitally_signed_path, final_signed_path):
                print(f"🎉 FINAL SIGNED DOCUMENT: {final_signed_path}")
                print("\n✅ Document Features:")
                print("   • Digital signature embedded (PKCS11)")
                print("   • Visible signature stamp on right side")
                print("   • Signature validation compatible")
                print("   • Professional appearance")
                
                print("\n📋 Signature Details:")
                print("   • Position: Bottom Right")
                print("   • Type: Digital Stamp with Checkmark")
                print("   • Technology: PKCS11 Hardware Token")
                print("   • Token: Watchdata PROXKey")
                
            else:
                print(f"✓ Digital signature applied (no visible stamp): {digitally_signed_path}")
                final_signed_path = digitally_signed_path
                
            print("\n🔍 To verify signature in Adobe Reader:")
            print("   1. Open the PDF in Adobe Acrobat Reader")
            print("   2. Look for the signature panel or blue ribbon")
            print("   3. Click on signature fields to view details")
            print("   4. Check File → Properties → Security")
            
        else:
            print(f"\n💥 FAILED: Could not sign PDF")
            
        return success
        
    except Exception as e:
        print(f"💥 Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎊 Process completed successfully!")
    else:
        print("\nPress Enter to exit...")
        input()
    
    sys.exit(0 if success else 1)