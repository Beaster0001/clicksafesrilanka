"""
🎯 Final CERT System Test
Test the complete CERT reporting system with Gmail
"""
import asyncio
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cert_email_service import cert_email_service
from production_cert_service import ProductionCERTService

async def final_cert_test():
    """Final test of the complete CERT system"""
    
    print("🎯 FINAL CERT SYSTEM TEST")
    print("=" * 50)
    print("Testing both cert_email_service and production_cert_service")
    print()
    
    # Sample high-risk phishing data (what the API would send)
    test_report_data = {
        'url': 'https://malicious-banking-site.github.io/fake-boc',
        'risk_score': 89,
        'risk_level': 'high',
        'classification': 'phishing',
        'confidence': 0.87,
        'reasoning': 'Bank of Ceylon clone detected with credential harvesting forms. Domain abuse on GitHub Pages platform.',
        'security_analysis': {
            'threat_indicators': {
                'brand_impersonation': True,
                'clone_site': True,
                'credential_harvesting': True,
                'github_pages_abuse': True
            },
            'classification': 'phishing'
        },
        'comments': 'Detected via ClickSafe QR scanner - targeting Sri Lankan banking customers',
        'user_email': 'concerned.citizen@example.com',
        'submitted_by': 'ClickSafe User',
        'submission_time': '2024-01-15 16:45:30'
    }
    
    print("📊 Test Report Data:")
    print(f"   🔗 URL: {test_report_data['url']}")
    print(f"   ⚠️ Risk Score: {test_report_data['risk_score']}/100")
    print(f"   🎯 Classification: {test_report_data['classification']}")
    print(f"   💬 Comments: {test_report_data['comments']}")
    print()
    
    # Test 1: Main CERT Email Service
    print("🧪 TEST 1: Main CERT Email Service")
    print("-" * 40)
    try:
        success1 = await cert_email_service.send_cert_report(test_report_data)
        if success1:
            print("✅ Main service: SUCCESS")
        else:
            print("❌ Main service: FAILED")
    except Exception as e:
        print(f"❌ Main service error: {str(e)}")
        success1 = False
    
    print()
    
    # Test 2: Production CERT Service
    print("🧪 TEST 2: Production CERT Service")
    print("-" * 40)
    try:
        production_service = ProductionCERTService()
        success2 = await production_service.send_cert_report(test_report_data)
        if success2:
            print("✅ Production service: SUCCESS")
        else:
            print("❌ Production service: FAILED")
    except Exception as e:
        print(f"❌ Production service error: {str(e)}")
        success2 = False
    
    print()
    print("🎉 FINAL RESULTS")
    print("=" * 50)
    
    if success1 and success2:
        print("✅ ALL TESTS PASSED!")
        print("🚀 Your CERT reporting system is FULLY OPERATIONAL!")
        print()
        print("📧 System Configuration:")
        print("   • From: clicksafesrilanka@gmail.com")
        print("   • To: heshanrashmika9@gmail.com") 
        print("   • SMTP: Gmail (smtp.gmail.com:587)")
        print("   • Auth: App Password (✅ Working)")
        print()
        print("🎯 How it works in your app:")
        print("   1. User scans suspicious QR/text with ClickSafe")
        print("   2. AI detects risk score ≥75%")
        print("   3. CERT button appears in PhishingDetector")
        print("   4. User clicks 'Report to CERT'")
        print("   5. Professional email sent to Sri Lanka CERT")
        print("   6. CERT receives detailed threat analysis")
        print()
        print("📧 Check heshanrashmika9@gmail.com for test emails!")
        
    else:
        print("⚠️ SOME TESTS FAILED")
        print("📋 Results:")
        print(f"   Main Service: {'✅ PASS' if success1 else '❌ FAIL'}")
        print(f"   Production Service: {'✅ PASS' if success2 else '❌ FAIL'}")

if __name__ == "__main__":
    asyncio.run(final_cert_test())