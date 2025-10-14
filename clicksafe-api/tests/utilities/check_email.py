"""
Quick email address change script
"""
from production_cert_service import ProductionCERTService

# Show current email
service = ProductionCERTService()
print(f"Current CERT recipient email: {service.cert_email}")
print("If you need to change this email, update the cert_email in production_cert_service.py")
print("Line 33: self.cert_email = \"your-correct-email@gmail.com\"")