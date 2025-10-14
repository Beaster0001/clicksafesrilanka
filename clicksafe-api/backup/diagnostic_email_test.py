"""
Simple test to check if email is working
Had issues with email not sending, so created this to debug
"""
import asyncio
import sys
import os

# Add current directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cert_email_service import cert_email_service

async def test_email():
    """Basic test for email functionality"""
    
    print("Testing CERT email service...")
    print("=" * 40)
    
    # Check if config is set up
    print("Configuration:")
    print(f"SMTP: {cert_email_service.smtp_server}:{cert_email_service.smtp_port}")
    print(f"From: {cert_email_service.sender_email}")
    print(f"To: {cert_email_service.cert_email}")
    print(f"Password: {'SET' if cert_email_service.sender_password else 'NOT SET'}")
    print()
    
    # Test SMTP connection
    print("Testing SMTP connection...")
    try:
        import smtplib
        server = smtplib.SMTP(cert_email_service.smtp_server, cert_email_service.smtp_port)
        server.starttls()
        server.login(cert_email_service.sender_email, cert_email_service.sender_password)
        server.quit()
        print("SMTP connection OK")
    except Exception as e:
        print(f"SMTP failed: {e}")
        return
    
    # Test email sending with dummy data
    print("Testing email send...")
    test_data = {
        'url': 'https://test-site.com',
        'risk_score': 75,
        'risk_level': 'high',
        'classification': 'phishing',
        'confidence': 0.75,
        'reasoning': 'Test email',
        'security_analysis': {
            'threat_indicators': {'suspicious_domain': True},
            'classification': 'phishing'
        },
        'comments': 'Test email - ignore',
        'user_email': 'test@test.com'
    }
    
    try:
        result = await cert_email_service.send_cert_report(test_data)
        if result:
            print("Email sent successfully!")
            print("Check heshanrashmika9@gmail.com inbox")
        else:
            print("Email send failed")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    asyncio.run(test_email())