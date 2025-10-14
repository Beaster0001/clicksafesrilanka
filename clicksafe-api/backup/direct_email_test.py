"""
Direct test of ProductionCERTService to isolate email sending issues
This test runs completely independently of the FastAPI server
"""
import asyncio
import os
import sys
from datetime import datetime

# Make sure we can import the service
try:
    from production_cert_service import ProductionCERTService
    print("✅ Successfully imported ProductionCERTService")
except ImportError as e:
    print(f"❌ Failed to import ProductionCERTService: {e}")
    sys.exit(1)

async def test_email_service_directly():
    """Test the email service directly with both phishing and QR data structures"""
    
    print("\n" + "="*60)
    print("DIRECT EMAIL SERVICE TEST")
    print("="*60)
    
    # Initialize the service
    try:
        cert_service = ProductionCERTService()
        print("✅ ProductionCERTService initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize ProductionCERTService: {e}")
        return
    
    # Test 1: Phishing detection data structure (KNOWN TO WORK)
    print("\n" + "-"*40)
    print("TEST 1: PHISHING DATA STRUCTURE (Known Working)")
    print("-"*40)
    
    phishing_data = {
        'content': 'This is a phishing message with suspicious content',
        'classification': 'phishing',
        'risk_score': 0.85,
        'confidence': 0.92,
        'reasoning': 'Contains multiple phishing indicators',
        'security_analysis': {
            'classification': 'phishing'
        },
        'comments': 'User reported this as suspicious',
        'user_email': 'testuser@example.com',
        'submitted_by': 'Test User',
        'submission_time': datetime.now()
    }
    
    try:
        print("🚀 Sending phishing CERT email...")
        phishing_result = await cert_service.send_cert_report(phishing_data)
        if phishing_result:
            print("✅ PHISHING EMAIL SENT SUCCESSFULLY!")
        else:
            print("❌ PHISHING EMAIL FAILED")
    except Exception as e:
        print(f"💥 PHISHING EMAIL ERROR: {e}")
    
    # Test 2: QR data structure (PROBLEMATIC)
    print("\n" + "-"*40)
    print("TEST 2: QR DATA STRUCTURE (Problematic)")
    print("-"*40)
    
    qr_data = {
        'url': 'https://suspicious-qr-site.com/phishing',
        'content': 'QR Code detected leading to: https://suspicious-qr-site.com/phishing. User comments: This QR code looked suspicious',
        'risk_score': 85,
        'risk_level': 'high',
        'classification': 'Malicious QR Code - High Risk',
        'confidence': 0.85,
        'reasoning': 'QR code analysis detected high risk level with score 85/100',
        'security_analysis': {
            'classification': 'Malicious QR Code - High Risk'
        },
        'comments': 'This QR code looked suspicious',
        'user_email': 'testuser@example.com',
        'submitted_by': 'Test User',
        'submission_time': datetime.now()
    }
    
    try:
        print("🚀 Sending QR CERT email...")
        qr_result = await cert_service.send_cert_report(qr_data)
        if qr_result:
            print("✅ QR EMAIL SENT SUCCESSFULLY!")
        else:
            print("❌ QR EMAIL FAILED")
    except Exception as e:
        print(f"💥 QR EMAIL ERROR: {e}")
    
    # Test 3: Minimal QR data structure (Ultra-simplified)
    print("\n" + "-"*40)
    print("TEST 3: MINIMAL QR DATA STRUCTURE")
    print("-"*40)
    
    minimal_qr_data = {
        'content': 'QR Code detected leading to suspicious URL',
        'classification': 'malicious',
        'risk_score': 0.85,
        'confidence': 0.85,
        'reasoning': 'QR code analysis detected high risk',
        'security_analysis': {
            'classification': 'malicious'
        },
        'comments': 'QR CERT report',
        'user_email': 'testuser@example.com',
        'submitted_by': 'Test User',
        'submission_time': datetime.now()
    }
    
    try:
        print("🚀 Sending minimal QR CERT email...")
        minimal_result = await cert_service.send_cert_report(minimal_qr_data)
        if minimal_result:
            print("✅ MINIMAL QR EMAIL SENT SUCCESSFULLY!")
        else:
            print("❌ MINIMAL QR EMAIL FAILED")
    except Exception as e:
        print(f"💥 MINIMAL QR EMAIL ERROR: {e}")
    
    print("\n" + "="*60)
    print("TEST COMPLETED")
    print("="*60)

if __name__ == "__main__":
    print("Starting direct email service test...")
    asyncio.run(test_email_service_directly())
    print("\nDirect test completed.")