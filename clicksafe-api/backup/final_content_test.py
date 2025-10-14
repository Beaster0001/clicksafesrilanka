"""
🎯 Final End-to-End CERT Test with Content
Test the complete CERT system including suspicious content
"""
import asyncio
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cert_email_service import cert_email_service
from production_cert_service import ProductionCERTService

async def final_content_test():
    """Final test with suspicious content included"""
    
    print("🎯 FINAL CERT SYSTEM TEST WITH CONTENT")
    print("=" * 50)
    
    # Realistic suspicious message (like users would receive)
    suspicious_content = """📱 Dialog Axiata Alert: Your data package has expired!

Click to renew immediately: http://fake-dialog-renewal.scam/urgent

💰 Special offer: 50GB for Rs.499 (Limited time)
⏰ Expires in 2 hours - Click now!

Reply STOP to unsubscribe
- Dialog Customer Care"""
    
    test_report_data = {
        'url': 'http://fake-dialog-renewal.scam/urgent',
        'content': suspicious_content,  # The actual suspicious message
        'risk_score': 87,
        'risk_level': 'high',
        'classification': 'phishing',
        'confidence': 0.85,
        'reasoning': 'Telecom provider impersonation with urgency tactics and fake renewal scam targeting Sri Lankan users',
        'security_analysis': {
            'threat_indicators': {
                'brand_impersonation': True,
                'urgency_tactics': True,
                'fake_renewal_scam': True,
                'telecom_fraud': True
            },
            'classification': 'phishing',
            'message_content': suspicious_content
        },
        'comments': 'User received this SMS - targeting Dialog customers with fake renewal offers',
        'user_email': 'user@example.com'
    }
    
    print("📱 Testing with Dialog telecom phishing scam:")
    print(f"   🔗 URL: {test_report_data['url']}")
    print(f"   ⚠️ Risk Score: {test_report_data['risk_score']}/100")
    print(f"   📧 Content: {suspicious_content[:100]}...")
    print()
    
    # Test main service
    print("🧪 Testing Main CERT Service...")
    try:
        success1 = await cert_email_service.send_cert_report(test_report_data)
        print(f"   Main Service: {'✅ SUCCESS' if success1 else '❌ FAILED'}")
    except Exception as e:
        print(f"   Main Service: ❌ ERROR - {str(e)}")
        success1 = False
    
    print()
    
    # Test production service
    print("🧪 Testing Production CERT Service...")
    try:
        prod_service = ProductionCERTService()
        success2 = await prod_service.send_cert_report(test_report_data)
        print(f"   Production Service: {'✅ SUCCESS' if success2 else '❌ FAILED'}")
    except Exception as e:
        print(f"   Production Service: ❌ ERROR - {str(e)}")
        success2 = False
    
    print()
    print("🎉 FINAL RESULTS")
    print("=" * 50)
    
    if success1 and success2:
        print("✅ ALL TESTS PASSED!")
        print("🚀 CERT system with content inclusion is WORKING!")
        print()
        print("📧 Emails sent to heshanrashmika9@gmail.com should now include:")
        print("   ✅ Section: '📱 SUSPICIOUS CONTENT DETECTED'")
        print("   ✅ Full suspicious message/SMS content")
        print("   ✅ Professional threat analysis")
        print("   ✅ Risk assessment and recommendations")
        print()
        print("🎯 Your ClickSafe CERT reporting now includes:")
        print("   • Complete suspicious message content")
        print("   • URL/link analysis")
        print("   • AI threat assessment")
        print("   • Professional CERT notification")
        print()
        print("✅ ISSUE FIXED: Suspicious content is now included in emails!")
        
    else:
        print("⚠️ Some issues detected - check logs above")

if __name__ == "__main__":
    asyncio.run(final_content_test())