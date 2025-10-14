"""
Comprehensive QR CERT Reporting Fix
This script will diagnose and fix all issues with QR CERT reporting
"""
import asyncio
import sys
import logging
import traceback
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def comprehensive_diagnostic():
    """Run comprehensive diagnostic and fix"""
    print("🔍 COMPREHENSIVE QR CERT REPORTING DIAGNOSTIC")
    print("=" * 60)
    
    # Test 1: Check imports
    print("\n1️⃣ Testing all imports...")
    try:
        from production_cert_service import ProductionCERTService
        print("   ✅ ProductionCERTService imported successfully")
        
        from qr_service import QRURLSafetyService, convert_numpy_types
        print("   ✅ QR service imports successful")
        
        from qr_routes import qr_router
        print("   ✅ QR routes imported successfully")
        
        from cert_routes import router as cert_router
        print("   ✅ CERT routes imported successfully")
        
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        traceback.print_exc()
        return False
    
    # Test 2: Initialize services
    print("\n2️⃣ Testing service initialization...")
    try:
        cert_service = ProductionCERTService()
        print(f"   ✅ ProductionCERTService initialized")
        print(f"   📧 Sender: {cert_service.current_config['sender_email']}")
        print(f"   🎯 Recipient: {cert_service.cert_email}")
        
        qr_service = QRURLSafetyService()
        print(f"   ✅ QRURLSafetyService initialized")
        
    except Exception as e:
        print(f"   ❌ Service initialization error: {e}")
        traceback.print_exc()
        return False
    
    # Test 3: Test email service directly (regular report)
    print("\n3️⃣ Testing regular CERT email service...")
    try:
        regular_report_data = {
            'url': 'http://test-phishing.malicious.com',
            'content': 'TEST: Regular phishing content detected',
            'risk_score': 85,
            'risk_level': 'high',
            'classification': 'phishing',
            'confidence': 0.9,
            'reasoning': 'Test regular CERT report',
            'security_analysis': {'test': 'data'},
            'comments': 'TEST: Regular CERT reporting',
            'user_email': 'test@clicksafe.lk',
            'submitted_by': 'Test User'
        }
        
        result = await cert_service.send_cert_report(regular_report_data)
        if result:
            print("   ✅ Regular CERT email sent successfully")
        else:
            print("   ❌ Regular CERT email failed")
        
    except Exception as e:
        print(f"   ❌ Regular CERT email error: {e}")
        traceback.print_exc()
    
    # Test 4: Test QR-specific email service
    print("\n4️⃣ Testing QR CERT email service...")
    try:
        qr_report_data = {
            'url': 'http://test-malicious-qr.fake-bank.com/login',
            'content': 'QR Code detected leading to: http://test-malicious-qr.fake-bank.com/login',
            'risk_score': 88,
            'risk_level': 'high',
            'classification': 'Malicious QR Code - High Risk',
            'confidence': 0.85,
            'reasoning': 'QR code analysis detected high risk level with score 88/100',
            'security_analysis': {
                'message_content': 'Suspicious QR code directing to URL: http://test-malicious-qr.fake-bank.com/login',
                'threat_indicators': {
                    'suspicious_qr_code': True,
                    'malicious_url': True,
                    'phishing_attempt': True
                },
                'scan_method': 'QR Code Analysis',
                'detection_type': 'QR Code URL'
            },
            'comments': 'TEST: QR code CERT report submitted via ClickSafe',
            'user_email': 'test@clicksafe.lk',
            'submitted_by': 'QR Test User',
            'submission_time': '2025-09-27 15:30:00'
        }
        
        result = await cert_service.send_cert_report(qr_report_data)
        if result:
            print("   ✅ QR CERT email sent successfully")
            print("   📧 Check heshanrashmika9@gmail.com (including spam folder)")
        else:
            print("   ❌ QR CERT email failed")
        
    except Exception as e:
        print(f"   ❌ QR CERT email error: {e}")
        traceback.print_exc()
    
    # Test 5: Test data format comparison
    print("\n5️⃣ Comparing data formats...")
    print("   Regular CERT data keys:", list(regular_report_data.keys()))
    print("   QR CERT data keys:", list(qr_report_data.keys()))
    
    # Check for differences
    regular_keys = set(regular_report_data.keys())
    qr_keys = set(qr_report_data.keys())
    
    if regular_keys == qr_keys:
        print("   ✅ Data formats are identical")
    else:
        print("   ⚠️  Data format differences:")
        print(f"      Only in regular: {regular_keys - qr_keys}")
        print(f"      Only in QR: {qr_keys - regular_keys}")
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSTIC COMPLETE")
    print("📧 If both email tests show success but you're not receiving emails:")
    print("   1. Check spam/junk folder")
    print("   2. Check all Gmail tabs (Primary, Promotions, etc.)")
    print("   3. Search for 'ClickSafe' or 'CERT' in Gmail")
    print("   4. Add clicksafesrilanka@gmail.com to contacts")

if __name__ == "__main__":
    asyncio.run(comprehensive_diagnostic())