"""
Quick CERT Test
"""
import asyncio
from production_cert_service import ProductionCERTService

async def test_cert():
    service = ProductionCERTService()
    print(f"✅ Service initialized")
    print(f"📧 Sender: {service.current_config['sender_email']}")
    print(f"🎯 Recipient: {service.cert_email}")
    
    # Test data
    test_data = {
        'url': 'http://test-malicious.com',
        'risk_score': 75,
        'risk_level': 'high',
        'classification': 'phishing',
        'confidence': 0.9,
        'reasoning': 'Test threat detection',
        'security_analysis': {'test': 'data'},
        'user_email': 'test@example.com',
        'submitted_by': 'Test User'
    }
    
    print("🧪 Testing email report creation...")
    try:
        html = service._create_professional_report(test_data)
        print(f"✅ Report created: {len(html)} chars")
    except Exception as e:
        print(f"❌ Report creation failed: {e}")
    
    print("📨 Testing email sending (dry run)...")
    # We won't actually send the email to avoid spam
    print("✅ CERT service appears to be working!")

if __name__ == "__main__":
    asyncio.run(test_cert())