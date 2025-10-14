"""
QR CERT Email Sending Diagnostic
Compare working phishing vs failing QR CERT email sending
"""
import asyncio
import logging
from production_cert_service import ProductionCERTService
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def diagnostic_email_comparison():
    """Compare working phishing email vs QR CERT email"""
    print("🔍 QR CERT EMAIL SENDING DIAGNOSTIC")
    print("=" * 60)
    
    # Initialize the same service used by both phishing and QR
    service = ProductionCERTService()
    print(f"📧 Using ProductionCERTService")
    print(f"   Sender: {service.current_config['sender_email']}")
    print(f"   Recipient: {service.cert_email}")
    print(f"   SMTP: {service.current_config['smtp_server']}:{service.current_config['smtp_port']}")
    
    # Test 1: Working phishing detection data format
    print(f"\n1️⃣ Testing WORKING Phishing Detection Format...")
    phishing_data = {
        'url': 'http://test-phishing-site.malicious.com',
        'content': 'Test phishing content detected',
        'risk_score': 85,
        'risk_level': 'high',
        'classification': 'phishing',
        'confidence': 0.9,
        'reasoning': 'Test phishing detection reasoning',
        'security_analysis': {
            'threat_type': 'phishing',
            'classification': 'phishing'
        },
        'comments': 'Test phishing CERT report',
        'user_email': 'test@clicksafe.lk',
        'submitted_by': 'Test User',
        'submission_time': datetime.now()  # Same as phishing
    }
    
    try:
        print(f"📤 Sending phishing format email...")
        result1 = await service.send_cert_report(phishing_data)
        print(f"📬 Phishing email result: {result1}")
        if result1:
            print("✅ PHISHING EMAIL: SUCCESS")
        else:
            print("❌ PHISHING EMAIL: FAILED")
    except Exception as e:
        print(f"💥 PHISHING EMAIL: EXCEPTION - {e}")
    
    # Test 2: QR CERT data format (current implementation)
    print(f"\n2️⃣ Testing QR CERT Format...")
    qr_data = {
        'url': 'http://malicious-qr-site.fake-bank.com/login',
        'content': 'QR Code detected leading to: http://malicious-qr-site.fake-bank.com/login',
        'risk_score': 88,
        'risk_level': 'high',
        'classification': 'Malicious QR Code - High Risk',
        'confidence': 0.85,
        'reasoning': 'QR code analysis detected high risk level with score 88/100',
        'security_analysis': {
            'message_content': 'Suspicious QR code directing to URL: http://malicious-qr-site.fake-bank.com/login',
            'threat_indicators': {
                'suspicious_qr_code': True,
                'malicious_url': True,
                'phishing_attempt': True
            },
            'scan_method': 'QR Code Analysis',
            'detection_type': 'QR Code URL'
        },
        'comments': 'QR code CERT report submitted via ClickSafe',
        'user_email': 'test@clicksafe.lk',
        'submitted_by': 'QR Test User',
        'submission_time': datetime.now()  # Same as phishing
    }
    
    try:
        print(f"📤 Sending QR format email...")
        result2 = await service.send_cert_report(qr_data)
        print(f"📬 QR email result: {result2}")
        if result2:
            print("✅ QR EMAIL: SUCCESS")
        else:
            print("❌ QR EMAIL: FAILED")
    except Exception as e:
        print(f"💥 QR EMAIL: EXCEPTION - {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Compare data structures
    print(f"\n3️⃣ Data Structure Comparison...")
    print(f"Phishing data keys: {list(phishing_data.keys())}")
    print(f"QR data keys: {list(qr_data.keys())}")
    
    phishing_keys = set(phishing_data.keys())
    qr_keys = set(qr_data.keys())
    
    print(f"\nUnique to phishing: {phishing_keys - qr_keys}")
    print(f"Unique to QR: {qr_keys - phishing_keys}")
    print(f"Common keys: {phishing_keys & qr_keys}")
    
    # Test 4: Check specific field differences
    print(f"\n4️⃣ Field Value Comparison...")
    for key in phishing_keys & qr_keys:
        phishing_val = phishing_data[key]
        qr_val = qr_data[key]
        phishing_type = type(phishing_val).__name__
        qr_type = type(qr_val).__name__
        
        if phishing_type != qr_type:
            print(f"⚠️  {key}: phishing={phishing_type}, qr={qr_type}")
        elif str(phishing_val) != str(qr_val):
            print(f"🔍 {key}: different values (types match)")
        else:
            print(f"✅ {key}: identical")
    
    print(f"\n" + "=" * 60)
    print("🎯 DIAGNOSIS RESULTS:")
    print("   If phishing works but QR fails, check the logs above for:")
    print("   1. Exception details in QR email sending")
    print("   2. Type mismatches between data formats")
    print("   3. SMTP connection issues specific to QR data")

if __name__ == "__main__":
    asyncio.run(diagnostic_email_comparison())