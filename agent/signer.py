# agent/signer.py
from endesive.pdf.cms import sign
from datetime import datetime

def sign_pdf(pdf_bytes, cert_file, key_file, password):
    dct = {
        "sigflags": 3,
        "contact": "user@domain.com",
        "location": "Local Signing Agent",
        "signingdate": datetime.now().strftime("%Y%m%d%H%M%S+00'00'"),
        "reason": "Document signed digitally",
    }
    signed_pdf = sign(pdf_bytes, dct, key_file, cert_file, password)
    return signed_pdf
