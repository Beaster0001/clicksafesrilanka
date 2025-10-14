#!/usr/bin/env python3
"""
Debug CERT Reporting System
Test all components to identify the issue
"""
import asyncio
import sys
import os
import logging

# Setup logging to see detailed output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all CERT-related modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from production_cert_service import ProductionCERTService
        print("✅ production_cert_service imported successfully")
    except Exception as e:
        print(f"❌ Failed to import production_cert_service: {e}")
        return False
    
    try:
        from cert_routes import router
        print("✅ cert_routes imported successfully")
    except Exception as e:
        print(f"❌ Failed to import cert_routes: {e}")
        return False
    
    return True

async def test_cert_service():
    """Test the CERT service functionality"""
    print("\n🧪 Testing CERT Service...")
    
    try:
        from production_cert_service import ProductionCERTService
        
        # Initialize service
        service = ProductionCERTService()
        print("✅ CERT service initialized")
        
        # Test data
        test_data = {
            'url': 'https://test-phishing-site.example.com',
            'content': 'This is a test phishing message',
            'risk_score': 85,
            'risk_level': 'high',
            'classification': 'phishing',
            'confidence': 0.85,
            'reasoning': 'Test debugging CERT system',
            'security_analysis': {
                'threat_indicators': {'test': True},
                'classification': 'phishing'
            },
            'comments': 'Debug test for CERT reporting',
            'user_email': 'test@example.com',
            'submitted_by': 'Debug Test',
            'submission_time': '2024-01-01T12:00:00'
        }
        
        print(f"📧 Attempting to send test report...")
        print(f"   Target email: {service.cert_email}")
        print(f"   Sender email: {service.current_config['sender_email']}")
        
        # Test email sending
        result = await service.send_cert_report(test_data)
        
        if result:
            print("✅ CERT email sent successfully!")
        else:
            print("❌ CERT email failed to send")
            
        return result
        
    except Exception as e:
        print(f"❌ Error in CERT service test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_routes():
    """Test if API routes are accessible"""
    print("\n🔗 Testing API Routes...")
    
    try:
        import requests
        
        # Test if server is running
        base_url = "http://localhost:8000"
        
        # Test CERT status endpoint
        try:
            response = requests.get(f"{base_url}/api/cert/status", timeout=5)
            if response.status_code == 200:
                print("✅ CERT status endpoint accessible")
                print(f"   Response: {response.json()}")
            else:
                print(f"⚠️ CERT status endpoint returned {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("❌ Server not running - cannot test API endpoints")
            return False
        except requests.exceptions.Timeout:
            print("❌ Server timeout - cannot test API endpoints")
            return False
            
    except ImportError:
        print("⚠️ requests library not available - skipping API tests")
        # This is not critical for CERT functionality
        
    return True

def check_email_config():
    """Check email configuration"""
    print("\n📧 Checking Email Configuration...")
    
    try:
        from production_cert_service import ProductionCERTService
        service = ProductionCERTService()
        
        print(f"Gmail Config:")
        print(f"  Server: {service.gmail_config['smtp_server']}:{service.gmail_config['smtp_port']}")
        print(f"  Sender: {service.gmail_config['sender_email']}")
        print(f"  Password: {'*' * len(service.gmail_config['sender_password'])}")
        
        print(f"Target CERT Email: {service.cert_email}")
        
        # Check if aiosmtplib is available
        try:
            import aiosmtplib
            print("✅ aiosmtplib library available")
        except ImportError:
            print("❌ aiosmtplib library missing - this is required!")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Email config check failed: {e}")
        return False

async def main():
    """Run all diagnostic tests"""
    print("🔧 CERT Reporting System Diagnostic")
    print("=" * 50)
    
    all_passed = True
    
    # Test 1: Imports
    if not test_imports():
        all_passed = False
    
    # Test 2: Email Configuration
    if not check_email_config():
        all_passed = False
    
    # Test 3: API Routes (if server is running)
    if not test_api_routes():
        print("⚠️ API tests failed - server may not be running")
    
    # Test 4: CERT Service
    if not await test_cert_service():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All CERT diagnostic tests passed!")
        print("🎯 CERT reporting should be working correctly")
    else:
        print("❌ Some CERT diagnostic tests failed")
        print("🔧 Please check the errors above and fix them")
    
    print("\n📋 Diagnostic Summary:")
    print("- Check if the FastAPI server is running")
    print("- Verify email credentials are correct")
    print("- Ensure aiosmtplib is installed")
    print("- Check network connectivity")

if __name__ == "__main__":
    asyncio.run(main())