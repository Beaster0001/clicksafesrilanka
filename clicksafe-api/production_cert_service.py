"""
🔧 CERT Email Service - Production Ready
Handles real email sending with multiple provider support
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ProductionCERTService:
    """Production-ready CERT email service with provider fallbacks"""
    
    def __init__(self):
        # Gmail configuration (Primary)
        self.gmail_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "clicksafesrilanka@gmail.com",
            "sender_password": "onyp ayly plyf sevt",  # Gmail app password
            "use_tls": True
        }
        
        # Backup: Outlook configuration (if needed)
        self.outlook_config = {
            "smtp_server": "smtp-mail.outlook.com",
            "smtp_port": 587,
            "sender_email": "ClickSafe_Srilanka@outlook.com",
            "sender_password": "hcnbqheivfsdsijr",
            "use_tls": True
        }
        
        self.cert_email = "heshanrashmika9@gmail.com"  # Verify this email address
        self.current_config = self.gmail_config  # Default to Gmail
    
    async def send_cert_report(self, threat_data: Dict[str, Any]) -> bool:
        """Send professional CERT phishing report"""
        try:
            # Create professional email
            msg = MIMEMultipart('alternative')
            msg['From'] = self.current_config["sender_email"]
            msg['To'] = self.cert_email
            msg['Subject'] = f"🚨 URGENT: Phishing Threat Report - Risk Level {threat_data.get('risk_score', 0)}%"
            msg['Date'] = formatdate(localtime=True)
            
            # Professional HTML content
            html_content = self._create_professional_report(threat_data)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Attempt to send
            success = await self._send_email_async(msg)
            
            if success:
                logger.info(f"✅ CERT report sent successfully to {self.cert_email}")
                return True
            else:
                logger.error("❌ Failed to send CERT report")
                return False
                
        except Exception as e:
            logger.error(f"❌ CERT email service error: {str(e)}")
            return False
    
    async def _send_email_async(self, message: MIMEMultipart) -> bool:
        """Send email using async SMTP with working Gmail configuration"""
        try:
            print("📧 Sending CERT report via Gmail...")
            print(f"   From: {self.current_config['sender_email']}")
            print(f"   To: {self.cert_email}")
            print(f"   Subject: {message['Subject']}")
            
            # Use working Gmail configuration with aiosmtplib
            smtp_client = aiosmtplib.SMTP(
                hostname=self.current_config["smtp_server"],
                port=self.current_config["smtp_port"],
                start_tls=True,
                username=self.current_config["sender_email"],
                password=self.current_config["sender_password"]
            )
            
            # Send the message using context manager
            async with smtp_client:
                await smtp_client.send_message(message)
            
            print("✅ CERT email sent successfully!")
            return True
            
        except Exception as e:
            print(f"❌ SMTP Error: {str(e)}")
            return False
    
    def _create_professional_report(self, threat_data: Dict[str, Any]) -> str:
        """Create professional HTML report for CERT"""
        risk_score = threat_data.get('risk_score', 0)
        
        # Extract URL and content properly
        url = threat_data.get('url', 'Unknown URL')
        detected_content = threat_data.get('content', '') or threat_data.get('security_analysis', {}).get('message_content', '')
        
        # If no content, use the URL as the main content
        if not detected_content or detected_content.strip() == '':
            detected_content = f"Malicious URL detected: {url}"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine threat level
        if risk_score >= 90:
            threat_level = "🔴 CRITICAL"
            threat_color = "#d32f2f"
        elif risk_score >= 75:
            threat_level = "🟠 HIGH"
            threat_color = "#f57c00"
        else:
            threat_level = "🟡 MEDIUM"
            threat_color = "#fbc02d"
        
        # Extract additional threat data
        risk_level = threat_data.get('risk_level', 'Medium').title()
        classification = threat_data.get('classification', 'Phishing/Social Engineering')
        user_email = threat_data.get('user_email', 'Anonymous')
        comments = threat_data.get('comments', 'No additional comments')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: {threat_color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .threat-box {{ background: #ffebee; border: 2px solid {threat_color}; padding: 15px; margin: 10px 0; }}
                .data-section {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #2196f3; }}
                .footer {{ background: #263238; color: white; padding: 15px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🛡️ ClickSafe CERT Report</h1>
                <h2>Phishing Threat Detection Alert</h2>
            </div>
            
            <div class="content">
                <div class="threat-box">
                    <h2>{threat_level} THREAT DETECTED</h2>
                    <p><strong>Risk Score:</strong> {risk_score}%</p>
                    <p><strong>Detection Time:</strong> {timestamp}</p>
                    <p><strong>Source:</strong> ClickSafe Mobile Application</p>
                </div>
                
                <div class="data-section">
                    <h3>� Malicious URL Details</h3>
                    <p><strong>Detected URL:</strong></p>
                    <pre style="background: white; padding: 10px; border: 1px solid #ddd; color: #d32f2f; font-weight: bold;">{url}</pre>
                </div>
                
                <div class="data-section">
                    <h3>�📱 Detected Content</h3>
                    <p><strong>Suspicious Content/Message:</strong></p>
                    <pre style="background: white; padding: 10px; border: 1px solid #ddd;">{detected_content}</pre>
                </div>
                
                <div class="data-section">
                    <h3>🔍 Threat Analysis</h3>
                    <p><strong>Detection Method:</strong> AI-Powered Phishing Detection</p>
                    <p><strong>Risk Level:</strong> {risk_level}</p>
                    <p><strong>Confidence Level:</strong> {risk_score}%</p>
                    <p><strong>Classification:</strong> {classification}</p>
                    <p><strong>Reported by User:</strong> {user_email}</p>
                    <p><strong>Comments:</strong> {comments}</p>
                </div>
                
                <div class="data-section">
                    <h3>🎯 Recommended Actions</h3>
                    <ul>
                        <li>Investigate the source of this phishing attempt</li>
                        <li>Add to threat intelligence databases</li>
                        <li>Consider issuing public warning if widespread</li>
                        <li>Monitor for similar attack patterns</li>
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p><strong>ClickSafe - Protecting Sri Lankan Citizens from Cyber Threats</strong></p>
                <p>This report was automatically generated by the ClickSafe security system</p>
                <p>For questions contact: ClickSafe_Srilanka@outlook.com</p>
            </div>
        </body>
        </html>
        """
        
        return html_content

    async def test_connection(self) -> bool:
        """Test email service connection"""
        test_data = {
            "risk_score": 95,
            "content": "🧪 This is a test message to verify CERT reporting system",
            "timestamp": datetime.now().isoformat()
        }
        
        print("🔄 Testing CERT email service...")
        result = await self.send_cert_report(test_data)
        
        if result:
            print("✅ CERT email service is ready!")
            print("🎯 System will send real emails when threats are detected")
        else:
            print("❌ CERT email service needs configuration")
            
        return result

# Test the service
if __name__ == "__main__":
    import datetime
    async def main():
        service = ProductionCERTService()
        await service.test_connection()
    
    asyncio.run(main())