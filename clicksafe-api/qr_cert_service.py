"""
QR CERT Reporting Service
Dedicated service for handling QR code CERT reports with enhanced email functionality
"""
import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class QRCERTService:
    """Dedicated QR CERT reporting service with robust email functionality"""
    
    def __init__(self):
        # Gmail configuration (Primary) - Same as working phishing detection
        self.gmail_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "clicksafesrilanka@gmail.com",
            "sender_password": "onyp ayly plyf sevt",  # Gmail app password
            "use_tls": True
        }
        
        # ⚠️ IMPORTANT: Update this email address to where you want CERT reports sent
        self.cert_email = "heshanrashmika9@gmail.com"  # CERT recipient - CHANGE THIS TO YOUR PREFERRED EMAIL
        
        print(f"[QR CERT] Service initialized")
        print(f"   Sender: {self.gmail_config['sender_email']}")
        print(f"   CERT Recipient: {self.cert_email}")
        print(f"   NOTE: CERT reports will be sent to {self.cert_email}")
    
    async def _test_email_connection(self) -> bool:
        """Test basic SMTP connection"""
        try:
            logger.info("🔗 Testing SMTP connection...")
            
            smtp_client = aiosmtplib.SMTP(
                hostname="smtp.gmail.com",
                port=587,
                start_tls=True
            )
            
            await smtp_client.connect()
            await smtp_client.login(self.gmail_config["sender_email"], self.gmail_config["sender_password"])
            await smtp_client.quit()
            
            logger.info("✅ SMTP connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ SMTP connection test failed: {str(e)}")
            return False

    async def submit_qr_cert_report(self, qr_data: dict) -> dict:
        """
        Submit a QR CERT report with comprehensive error handling and logging
        
        Args:
            qr_data: Dictionary containing QR threat information
            
        Returns:
            Dictionary with submission status and details
        """
        try:
            print(f"\n{'='*60}")
            print(f"🚨 QR CERT REPORT SUBMISSION STARTING")
            print(f"{'='*60}")
            
            # Log the incoming data
            print(f"📊 QR Report Data:")
            for key, value in qr_data.items():
                if key == 'security_analysis':
                    print(f"  {key}: {type(value).__name__} - {value}")
                else:
                    print(f"  {key}: {value}")
            
            # Validate required fields (removed user_email for privacy)
            required_fields = ['url', 'risk_score']
            missing_fields = [field for field in required_fields if not qr_data.get(field)]
            
            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                print(f"❌ Validation Error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'email_sent': False
                }
            
            # Normalize and enhance the data
            normalized_data = self._normalize_qr_data(qr_data)
            print(f"\n📋 Normalized QR Data:")
            for key, value in normalized_data.items():
                print(f"  {key}: {value}")
            
            # Generate report ID
            report_id = f"QR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{abs(hash(normalized_data['url'])) % 10000:04d}"
            normalized_data['report_id'] = report_id
            
            print(f"\n🔖 Generated Report ID: {report_id}")
            
            # Create and send email
            print(f"\n📧 ATTEMPTING EMAIL SENDING...")
            email_result = await self._send_qr_cert_email(normalized_data)
            
            if email_result['success']:
                print(f"✅ QR CERT EMAIL SENT SUCCESSFULLY!")
                print(f"   Email ID: {email_result.get('email_id', 'N/A')}")
                print(f"   Sent to: {self.cert_email}")
                print(f"   Sent from: {self.gmail_config['sender_email']}")
                
                return {
                    'success': True,
                    'message': 'QR CERT report submitted successfully',
                    'report_id': report_id,
                    'email_sent': True,
                    'email_details': email_result,
                    'submitted_at': datetime.now().isoformat(),
                    'recipient': self.cert_email
                }
            else:
                print(f"❌ QR CERT EMAIL FAILED!")
                print(f"   Error: {email_result.get('error', 'Unknown error')}")
                
                return {
                    'success': False,
                    'message': 'QR CERT report processed but email delivery failed',
                    'report_id': report_id,
                    'email_sent': False,
                    'email_error': email_result.get('error', 'Unknown error'),
                    'submitted_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            error_msg = f"QR CERT Service error: {str(e)}"
            print(f"💥 CRITICAL ERROR: {error_msg}")
            logger.exception("QR CERT Service exception:")
            
            return {
                'success': False,
                'error': error_msg,
                'email_sent': False,
                'submitted_at': datetime.now().isoformat()
            }
    
    def _normalize_qr_data(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize QR report data to consistent format"""
        
        # Extract URL (handle both old and new formats)
        url = report_data.get('url') or report_data.get('qr_url', '')
        
        # Extract comments (handle both formats)
        comments = report_data.get('comments') or report_data.get('user_comments', '')
        
        # Extract risk information
        risk_score = report_data.get('risk_score', 0)
        risk_level = report_data.get('risk_level', '')
        
        # Derive risk level if not provided
        if not risk_level:
            if risk_score >= 80:
                risk_level = 'critical'
            elif risk_score >= 60:
                risk_level = 'high'
            else:
                risk_level = 'medium'
        
        # Extract classification
        classification = report_data.get('classification', f'Malicious QR Code - {risk_level.title()} Risk')
        
        # Extract confidence
        confidence = report_data.get('confidence')
        if confidence is None:
            confidence = min(risk_score / 100.0, 1.0)
        
        # Create content description
        content = report_data.get('content', f"QR code detected leading to: {url}")
        if comments and comments not in content:
            content += f". User comments: {comments}"
        
        # Create reasoning
        reasoning = report_data.get('reasoning', f"QR code analysis detected {risk_level} risk level with score {risk_score}/100")
        
        # Handle security analysis
        security_analysis = report_data.get('security_analysis', {})
        if not security_analysis:
            security_analysis = {
                'classification': classification,
                'threat_indicators': {
                    'suspicious_qr_code': True,
                    'risk_level': risk_level,
                    'malicious_url': risk_score >= 70
                }
            }
        
        return {
            'url': url,
            'content': content,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'classification': classification,
            'confidence': confidence,
            'reasoning': reasoning,
            'security_analysis': security_analysis,
            'comments': comments,
            'submission_time': datetime.now()
            # User details removed for privacy protection
        }
    
    async def _send_qr_cert_email(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send QR CERT email with detailed logging and error handling"""
        
        try:
            print(f"📧 Creating QR CERT email...")
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.gmail_config["sender_email"]
            msg['To'] = self.cert_email
            msg['Subject'] = f"🚨 URGENT: QR Code Threat Report - Risk Level {report_data['risk_score']}%"
            msg['Date'] = formatdate(localtime=True)
            
            # Create HTML content
            html_content = self._create_qr_cert_html_report(report_data)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            print(f"📧 Email created successfully")
            print(f"   Subject: {msg['Subject']}")
            print(f"   From: {msg['From']}")
            print(f"   To: {msg['To']}")
            
            # Send email using aiosmtplib
            print(f"📧 Connecting to Gmail SMTP...")
            
            smtp_client = aiosmtplib.SMTP(
                hostname=self.gmail_config["smtp_server"],
                port=self.gmail_config["smtp_port"],
                start_tls=True,
                username=self.gmail_config["sender_email"],
                password=self.gmail_config["sender_password"]
            )
            
            print(f"📧 SMTP client configured")
            print(f"   Server: {self.gmail_config['smtp_server']}:{self.gmail_config['smtp_port']}")
            print(f"   Username: {self.gmail_config['sender_email']}")
            
            # Send the message
            async with smtp_client:
                print(f"📧 Sending email...")
                await smtp_client.send_message(msg)
            
            print(f"✅ QR CERT EMAIL SENT SUCCESSFULLY!")
            
            return {
                'success': True,
                'email_id': f"qr-cert-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'sent_to': self.cert_email,
                'sent_from': self.gmail_config["sender_email"],
                'subject': msg['Subject'],
                'sent_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Email sending failed: {str(e)}"
            print(f"❌ EMAIL ERROR: {error_msg}")
            logger.exception("QR CERT email sending exception:")
            
            return {
                'success': False,
                'error': error_msg,
                'attempted_at': datetime.now().isoformat()
            }
    
    def _create_qr_cert_html_report(self, report_data: Dict[str, Any]) -> str:
        """Create professional HTML report for QR CERT submission"""
        
        risk_score = report_data.get('risk_score', 0)
        risk_color = '#dc3545' if risk_score >= 80 else '#fd7e14' if risk_score >= 60 else '#ffc107'
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>QR Code Threat Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: {risk_color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .section {{ margin-bottom: 20px; padding: 15px; border-left: 4px solid {risk_color}; background: #f8f9fa; }}
                .label {{ font-weight: bold; color: #495057; }}
                .value {{ margin-left: 10px; }}
                .risk-badge {{ background: {risk_color}; color: white; padding: 5px 10px; border-radius: 4px; font-weight: bold; }}
                .footer {{ background: #6c757d; color: white; padding: 15px; text-align: center; font-size: 12px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f9fa; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 QR Code Security Threat Report</h1>
                <p>Submitted via ClickSafe Threat Detection System</p>
            </div>
            
            <div class="content">
                <div class="section">
                    <h2>🎯 Threat Summary</h2>
                    <table>
                        <tr><td class="label">Malicious URL:</td><td><strong>{report_data.get('url', 'N/A')}</strong></td></tr>
                        <tr><td class="label">Risk Level:</td><td><span class="risk-badge">{report_data.get('risk_level', 'Unknown').upper()}</span></td></tr>
                        <tr><td class="label">Risk Score:</td><td><strong>{risk_score}%</strong></td></tr>
                        <tr><td class="label">Classification:</td><td>{report_data.get('classification', 'N/A')}</td></tr>
                        <tr><td class="label">Confidence:</td><td>{report_data.get('confidence', 0):.2%}</td></tr>
                    </table>
                </div>
                
                <div class="section">
                    <h2>📋 Threat Description</h2>
                    <p><strong>Content:</strong> {report_data.get('content', 'N/A')}</p>
                    <p><strong>Analysis Reasoning:</strong> {report_data.get('reasoning', 'N/A')}</p>
                    {f"<p><strong>User Comments:</strong> {report_data.get('comments', 'None provided')}</p>" if report_data.get('comments') else ''}
                </div>
                
                <div class="section">
                    <h2>🔍 Security Analysis</h2>
                    <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto;">{json.dumps(report_data.get('security_analysis', {}), indent=2)}</pre>
                </div>
                
                <div class="section">
                    <h2>� Submission Details</h2>
                    <table>
                        <tr><td class="label">Report ID:</td><td>{report_data.get('report_id', 'N/A')}</td></tr>
                        <tr><td class="label">Submitted Via:</td><td>ClickSafe Security Platform</td></tr>
                        <tr><td class="label">Submission Time:</td><td>{report_data.get('submission_time', datetime.now()).strftime('%Y-%m-%d %H:%M:%S UTC') if hasattr(report_data.get('submission_time', datetime.now()), 'strftime') else str(report_data.get('submission_time', datetime.now()))}</td></tr>
                    </table>
                    <p style="font-size: 12px; color: #666; margin-top: 10px;">
                        <em>Note: User identity protected for privacy. Contact ClickSafe for additional details if required for investigation.</em>
                    </p>
                </div>
                
                <div class="section">
                    <h2>⚡ Recommended Actions</h2>
                    {"<ul>" + "".join([f"<li>🔴 <strong>CRITICAL:</strong> Immediate investigation and blocking recommended</li><li>📊 Add URL to threat intelligence databases</li><li>🚫 Consider domain blocking at infrastructure level</li>" if risk_score >= 80 else 
                    "<li>🟠 <strong>HIGH RISK:</strong> Investigation recommended within 24 hours</li><li>📊 Monitor for similar patterns</li><li>⚠️ Consider user awareness alerts</li>" if risk_score >= 60 else
                    "<li>🟡 <strong>MEDIUM RISK:</strong> Standard investigation procedures</li><li>📊 Add to monitoring systems</li><li>📝 Document for trend analysis</li>"]) + "</ul>"}
                </div>
            </div>
            
            <div class="footer">
                <p>This report was automatically generated by ClickSafe QR Code Security System</p>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} | Report ID: {report_data.get('report_id', 'N/A')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    async def test_email_connection(self) -> Dict[str, Any]:
        """Test email connection and configuration"""
        try:
            print(f"\n🔧 TESTING QR CERT EMAIL CONNECTION...")
            print(f"   Server: {self.gmail_config['smtp_server']}:{self.gmail_config['smtp_port']}")
            print(f"   Username: {self.gmail_config['sender_email']}")
            
            smtp_client = aiosmtplib.SMTP(
                hostname=self.gmail_config["smtp_server"],
                port=self.gmail_config["smtp_port"],
                start_tls=True,
                username=self.gmail_config["sender_email"],
                password=self.gmail_config["sender_password"]
            )
            
            async with smtp_client:
                print("✅ SMTP connection successful!")
                return {'success': True, 'message': 'Email connection test passed'}
                
        except Exception as e:
            error_msg = f"Email connection test failed: {str(e)}"
            print(f"❌ SMTP connection failed: {error_msg}")
            return {'success': False, 'error': error_msg}

# Test function
async def test_qr_cert_service():
    """Test the QR CERT service with sample data"""
    print("🧪 TESTING QR CERT SERVICE...")
    
    service = QRCERTService()
    
    # Test connection first
    connection_result = await service.test_email_connection()
    if not connection_result['success']:
        print(f"❌ Connection test failed: {connection_result['error']}")
        return
    
    # Test QR CERT submission
    sample_data = {
        'url': 'https://malicious-qr-test.com/steal-credentials',
        'risk_score': 87,
        'risk_level': 'high',
        'user_email': 'testuser@clicksafe.com',
        'submitted_by': 'Test User',
        'comments': 'Found this QR code on a suspicious poster in a public area'
    }
    
    result = await service.submit_qr_cert_report(sample_data)
    
    if result['success']:
        print(f"\n🎉 QR CERT SERVICE TEST SUCCESSFUL!")
        print(f"   Report ID: {result['report_id']}")
        print(f"   Email Sent: {result['email_sent']}")
    else:
        print(f"\n❌ QR CERT SERVICE TEST FAILED!")
        print(f"   Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(test_qr_cert_service())
