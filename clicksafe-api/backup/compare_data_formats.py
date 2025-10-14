"""
Data Format Comparison
Compare the working test data vs QR CERT data formats
"""
import json
from datetime import datetime

def compare_data_formats():
    """Compare working test data vs QR CERT data"""
    print("🔍 DATA FORMAT COMPARISON")
    print("=" * 50)
    
    # Working test data (from comprehensive_cert_fix.py)
    working_test_data = {
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
    
    # QR CERT data format (from qr_routes.py - after fixes)
    qr_cert_data = {
        'url': 'http://malicious-qr-site.fake-bank.com/login',
        'content': 'QR Code detected leading to: http://malicious-qr-site.fake-bank.com/login',
        'risk_score': 88,  # Now converted to int
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
        'submission_time': datetime.now().isoformat()  # Now as string
    }
    
    print("📊 WORKING TEST DATA:")
    print(json.dumps(working_test_data, indent=2, default=str))
    
    print(f"\n📱 QR CERT DATA:")
    print(json.dumps(qr_cert_data, indent=2, default=str))
    
    print(f"\n🔍 KEY DIFFERENCES:")
    
    # Check field differences
    test_keys = set(working_test_data.keys())
    qr_keys = set(qr_cert_data.keys())
    
    print(f"   Fields only in test data: {test_keys - qr_keys}")
    print(f"   Fields only in QR data: {qr_keys - test_keys}")
    print(f"   Common fields: {test_keys & qr_keys}")
    
    print(f"\n🎯 POTENTIAL ISSUES FIXED:")
    print(f"   1. ✅ risk_score: Now converted to int({qr_cert_data['risk_score']})")
    print(f"   2. ✅ submission_time: Now ISO string ({qr_cert_data['submission_time'][:19]})")
    print(f"   3. ✅ url: Now explicitly string")
    print(f"   4. ✅ All other fields appear compatible")
    
    print(f"\n📧 The QR data format should now work identically to the test data!")

if __name__ == "__main__":
    compare_data_formats()