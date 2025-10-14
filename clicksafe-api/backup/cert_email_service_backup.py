"""
Email service for automated CERT reporting
Handles sending phishing reports to Sri Lanka CERT with professional formatting
"""
import aiosmtplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json
from jinja2 import Template
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class CERTEmailService:
    """Professional email service for Sri Lanka CERT phishing reports"""
    
    def __init__(self):
        # Gmail SMTP configuration - WORKING!
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "clicksafesrilanka@gmail.com"
        self.sender_password = "onyp ayly plyf sevt"  # Gmail app password
        self.cert_email = "heshanrashmika9@gmail.com"  # Sri Lanka CERT representative
        
        # Email templates
        self.report_template = self._get_report_template()
    
    def _get_report_template(self) -> Template:
        """Professional email template for CERT reports"""
        template_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background: #d32f2f; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .section { margin: 20px 0; padding: 15px; border-left: 4px solid #d32f2f; background: #f5f5f5; }
        .details-table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        .details-table th, .details-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .details-table th { background-color: #f2f2f2; }
        .risk-high { color: #d32f2f; font-weight: bold; }
        .risk-critical { color: #b71c1c; font-weight: bold; background: #ffebee; padding: 2px 5px; }
        .footer { background: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #666; }
        .evidence { background: #fff3e0; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h2>🚨 PHISHING THREAT REPORT - SRI LANKA CERT</h2>
        <p>Automated Security Alert from ClickSafe Detection System</p>
    </div>

    <div class="content">
        <div class="section">
            <h3>🛡️ THREAT SUMMARY</h3>
            <table class="details-table">
                <tr>
                    <th>Detection Time</th>
                    <td>{{ detection_time }}</td>
                </tr>
                <tr>
                    <th>Risk Level</th>
                    <td class="{{ risk_class }}">{{ risk_level }} ({{ risk_score }}/100)</td>
                </tr>
                <tr>
                    <th>Threat Type</th>
                    <td>{{ threat_type }}</td>
                </tr>
                <tr>
                    <th>Detection Method</th>
                    <td>QR Code Scanning + AI Security Analysis</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <h3>🔗 MALICIOUS URL DETAILS</h3>
            <div class="evidence">
                <strong>URL:</strong> <code>{{ url }}</code><br>
                <strong>Domain:</strong> {{ domain }}<br>
                <strong>Protocol:</strong> {{ protocol }}<br>
                {% if is_github_pages %}
                <strong>⚠️ GitHub Pages Abuse Detected</strong><br>
                {% endif %}
            </div>
        </div>

        <div class="section">
            <h3>🔍 THREAT ANALYSIS</h3>
            <table class="details-table">
                <tr>
                    <th>Classification</th>
                    <td>{{ classification }}</td>
                </tr>
                <tr>
                    <th>Confidence Level</th>
                    <td>{{ confidence }}%</td>
                </tr>
                <tr>
                    <th>Analysis Engine</th>
                    <td>{{ analysis_method }}</td>
                </tr>
            </table>
            
            {% if threat_indicators %}
            <h4>🚨 Detected Threat Indicators:</h4>
            <ul>
                {% for indicator in threat_indicators %}
                <li>{{ indicator }}</li>
                {% endfor %}
            </ul>
            {% endif %}

            {% if reasoning %}
            <div class="evidence">
                <strong>Analysis Reasoning:</strong><br>
                {{ reasoning }}
            </div>
            {% endif %}
        </div>

        <div class="section">
            <h3>👤 REPORTER INFORMATION</h3>
            <table class="details-table">
                <tr>
                    <th>Reporting System</th>
                    <td>ClickSafe Security Platform</td>
                </tr>
                <tr>
                    <th>User Email</th>
                    <td>{{ user_email }}</td>
                </tr>
                <tr>
                    <th>Report ID</th>
                    <td>{{ report_id }}</td>
                </tr>
                <tr>
                    <th>Additional Comments</th>
                    <td>{{ comments }}</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <h3>📋 RECOMMENDED ACTIONS</h3>
            <ul>
                <li><strong>Immediate:</strong> Block access to the reported URL</li>
                <li><strong>Investigation:</strong> Verify phishing content and target victims</li>
                <li><strong>Coordination:</strong> Notify relevant ISPs and hosting providers</li>
                <li><strong>Public Alert:</strong> Consider issuing public warning if widespread</li>
                {% if is_github_pages %}
                <li><strong>Platform Abuse:</strong> Report to GitHub for Terms of Service violation</li>
                {% endif %}
            </ul>
        </div>
    </div>

    <div class="footer">
        <p><strong>ClickSafe - National Cyber Security Initiative | Sri Lanka</strong></p>
        <p>This is an automated report generated by ClickSafe's AI-powered phishing detection system.</p>
        <p>For technical inquiries: support@clicksafe.lk | Emergency: +94-11-CERT-24x7</p>
        <p>Report generated on {{ generation_time }}</p>
    </div>
</body>
</html>
        """
        return Template(template_content)
    
    async def send_cert_report(self, report_data: Dict[str, Any]) -> bool:
        """
        Send phishing report to Sri Lanka CERT
        
        Args:
            report_data: Dictionary containing all report information
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Prepare email data
            email_data = self._prepare_email_data(report_data)
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = self.cert_email
            msg['Subject'] = f"🚨 PHISHING ALERT - Risk Level: {email_data['risk_level']} | ClickSafe Report #{email_data['report_id']}"
            msg['Date'] = formatdate(localtime=True)
            
            # Add headers for better delivery
            msg['X-Priority'] = '1'  # High priority
            msg['X-MSMail-Priority'] = 'High'
            msg['Importance'] = 'high'
            
            # Generate HTML content
            html_content = self.report_template.render(**email_data)
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Send email using aiosmtplib for async operation
            await self._send_async_email(msg)
            
            logger.info(f"CERT report sent successfully for URL: {report_data.get('url', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send CERT report: {str(e)}")
            return False
    
    def _prepare_email_data(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare and format data for email template"""
        
        # Extract key information
        url = report_data.get('url', 'Unknown')
        risk_score = report_data.get('risk_score', 0)
        risk_level = report_data.get('risk_level', 'unknown').upper()
        
        # Determine risk CSS class
        risk_class = 'risk-critical' if risk_score >= 90 else 'risk-high'
        
        # Extract domain information
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        protocol = parsed.scheme.upper()
        
        # Check for GitHub Pages
        is_github_pages = 'github.io' in domain.lower()
        
        # Extract threat indicators
        threat_indicators = []
        security_analysis = report_data.get('security_analysis', {})
        indicators = security_analysis.get('threat_indicators', {})
        
        for indicator, detected in indicators.items():
            if detected:
                threat_indicators.append(indicator.replace('_', ' ').title())
        
        # Generate unique report ID
        report_id = f"CS-{datetime.now().strftime('%Y%m%d')}-{abs(hash(url)) % 10000:04d}"
        
        return {
            'detection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_class': risk_class,
            'threat_type': 'Phishing Website',
            'url': url,
            'domain': domain,
            'protocol': protocol,
            'is_github_pages': is_github_pages,
            'classification': security_analysis.get('classification', 'Unknown').title(),
            'confidence': int(report_data.get('confidence', 0) * 100),
            'analysis_method': 'Enhanced AI Security Analysis',
            'threat_indicators': threat_indicators,
            'reasoning': report_data.get('reasoning', 'No additional details available'),
            'user_email': report_data.get('user_email', 'Anonymous'),
            'report_id': report_id,
            'comments': report_data.get('comments', 'No additional comments provided')
        }
    
    async def _send_async_email(self, msg: MIMEMultipart):
        """Send email using async SMTP"""
        
        # Production email sending using aiosmtplib with Gmail
        try:
            print(f"� Sending CERT report email...")
            print(f"   From: {self.sender_email}")
            print(f"   To: {self.cert_email}")
            print(f"   Subject: {msg['Subject']}")
            
            # Connect to Gmail SMTP server asynchronously
            smtp = aiosmtplib.SMTP(hostname=self.smtp_server, port=self.smtp_port, use_tls=False)
            await smtp.connect()
            await smtp.starttls()
            await smtp.login(self.sender_email, self.sender_password)
            
            # Send the email
            await smtp.send_message(msg)
            await smtp.quit()
            
            print("✅ CERT email sent successfully to Sri Lanka CERT!")
            logger.info(f"✅ Email sent successfully to {self.cert_email}")
            
        except Exception as e:
            print(f"❌ SMTP Error: {str(e)}")
            logger.error(f"❌ SMTP Error: {str(e)}")
            raise e
    
    def test_email_template(self, sample_data: Dict[str, Any]) -> str:
        """Generate test email HTML for verification"""
        email_data = self._prepare_email_data(sample_data)
        return self.report_template.render(**email_data)

# Global email service instance
cert_email_service = CERTEmailService()