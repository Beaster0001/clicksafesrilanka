"""
CERT Service Diagnostic
Check what's wrong with CERT reporting
"""
import sys
import traceback

def diagnose_cert_service():
    """Diagnose CERT service issues"""
    print("🔍 CERT Service Diagnostic")
    print("=" * 50)
    
    # Test 1: Check imports
    print("\n1. Testing imports...")
    try:
        from production_cert_service import ProductionCERTService
        print("   ✅ ProductionCERTService import: OK")
    except Exception as e:
        print(f"   ❌ ProductionCERTService import failed: {e}")
        traceback.print_exc()
    
    try:
        from cert_email_service import cert_email_service
        print("   ✅ cert_email_service import: OK")
    except Exception as e:
        print(f"   ❌ cert_email_service import failed: {e}")
        traceback.print_exc()
    
    # Test 2: Check service initialization
    print("\n2. Testing service initialization...")
    try:
        service = ProductionCERTService()
        print("   ✅ ProductionCERTService initialization: OK")
        print(f"   Current config: {service.current_config['sender_email']}")
        print(f"   CERT email: {service.cert_email}")
    except Exception as e:
        print(f"   ❌ ProductionCERTService initialization failed: {e}")
        traceback.print_exc()
    
    # Test 3: Check dependencies
    print("\n3. Testing dependencies...")
    dependencies = ['aiosmtplib', 'email', 'logging', 'datetime']
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"   ✅ {dep}: OK")
        except Exception as e:
            print(f"   ❌ {dep}: Failed - {e}")
    
    # Test 4: Check CERT routes import
    print("\n4. Testing CERT routes...")
    try:
        from cert_routes import router
        print("   ✅ CERT routes import: OK")
        print(f"   Router prefix: {router.prefix}")
        print(f"   Router tags: {router.tags}")
    except Exception as e:
        print(f"   ❌ CERT routes import failed: {e}")
        traceback.print_exc()
    
    # Test 5: Test email template generation
    print("\n5. Testing email template generation...")
    try:
        service = ProductionCERTService()
        test_data = {
            'url': 'http://test.com',
            'risk_score': 75,
            'risk_level': 'high',
            'classification': 'phishing',
            'user_email': 'test@example.com'
        }
        html_content = service._create_professional_report(test_data)
        print("   ✅ Email template generation: OK")
        print(f"   Template length: {len(html_content)} characters")
    except Exception as e:
        print(f"   ❌ Email template generation failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_cert_service()
    print("\n🎉 Diagnostic completed!")