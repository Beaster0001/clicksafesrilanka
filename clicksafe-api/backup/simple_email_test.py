"""
📧 Simple Test Email - Check Basic Delivery
Send a very simple email to test delivery without complex HTML
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_simple_test():
    """Send a very simple test email"""
    
    print("📧 SIMPLE EMAIL DELIVERY TEST")
    print("=" * 40)
    
    # Gmail configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "clicksafesrilanka@gmail.com"
    sender_password = "onyp ayly plyf sevt"
    recipient_email = "heshanrashmika9@gmail.com"
    
    try:
        print(f"📧 From: {sender_email}")
        print(f"📧 To: {recipient_email}")
        print()
        
        # Create simple message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "TEST: ClickSafe Email Delivery Check"
        
        # Simple text body
        body = f"""
Hello,

This is a simple test email from ClickSafe to verify email delivery.

Time sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
From: {sender_email}
To: {recipient_email}

If you receive this email, the delivery system is working correctly.

Best regards,
ClickSafe Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        print("🔄 Sending simple test email...")
        
        # Connect and send
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        print("✅ Simple test email sent successfully!")
        print()
        print("📧 Please check heshanrashmika9@gmail.com:")
        print("   1. Check inbox")
        print("   2. Check spam/junk folder") 
        print("   3. Check all mail/promotions tabs")
        print()
        print("🔍 If you don't see this simple email, there may be:")
        print("   • Email filtering rules")
        print("   • Delivery delays")
        print("   • Account storage issues")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    send_simple_test()