"""
CERT Reporting API Routes
Handles submission of phishing reports to Sri Lanka CERT
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import logging
from datetime import datetime

from database import get_db
from auth_routes import get_current_user
from models import User
from production_cert_service import ProductionCERTService

# Initialize production CERT service
production_cert_service = ProductionCERTService()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cert", tags=["CERT Reporting"])

class CERTReportRequest(BaseModel):
    """Request model for CERT phishing reports"""
    url: str
    content: Optional[str] = ""  # The actual suspicious message/content
    risk_score: int
    risk_level: str
    classification: str
    confidence: float
    reasoning: Optional[str] = ""
    security_analysis: dict
    comments: Optional[str] = ""
    
    @validator('risk_score')
    def validate_risk_score(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Risk score must be between 0 and 100')
        return v
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Confidence must be between 0 and 1')
        return v

class CERTReportResponse(BaseModel):
    """Response model for CERT report submission"""
    success: bool
    message: str
    report_id: Optional[str] = None
    submitted_at: datetime

@router.post("/report", response_model=CERTReportResponse)
async def submit_cert_report(
    report: CERTReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a phishing report to Sri Lanka CERT
    
    This endpoint accepts medium-risk and above phishing detections and automatically
    sends detailed reports to the Sri Lanka National Centre for Cyber Security.
    
    Requirements:
    - User must be authenticated
    - Risk score must be >= 50% (medium risk and above)
    - Valid URL and security analysis data required
    """
    
    try:
        # Validate risk threshold - accept medium, high, and critical risk reports
        if report.risk_score < 50:  # Accept medium risk (50+) and above
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CERT reports are only accepted for medium-risk threats and above (score >= 50%)"
            )
        
        # Prepare report data
        report_data = {
            'url': report.url,
            'content': report.content or report.security_analysis.get('message_content', ''),  # Get content from either field
            'risk_score': report.risk_score,
            'risk_level': report.risk_level,
            'classification': report.classification,
            'confidence': report.confidence,
            'reasoning': report.reasoning,
            'security_analysis': report.security_analysis,
            'comments': report.comments,
            'user_email': current_user.email,
            'submitted_by': current_user.full_name or current_user.username,
            'submission_time': datetime.now()
        }
        
        # Log the report attempt
        logger.info(f"CERT report submission attempt by {current_user.email} for URL: {report.url}")
        
        # Send email to CERT using production service
        email_sent = await production_cert_service.send_cert_report(report_data)
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send report to CERT. Please try again later."
            )
        
        # Generate report ID for tracking
        report_id = f"CS-{datetime.now().strftime('%Y%m%d')}-{abs(hash(report.url)) % 10000:04d}"
        
        # Log successful submission
        logger.info(f"CERT report {report_id} successfully submitted for URL: {report.url}")
        
        # TODO: Store report in database for tracking
        # This could be implemented later for report history and analytics
        
        return CERTReportResponse(
            success=True,
            message="Report successfully submitted to Sri Lanka CERT. You will receive a confirmation email shortly.",
            report_id=report_id,
            submitted_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting CERT report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing CERT report"
        )

@router.get("/test-template")
async def test_email_template(
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint to preview the CERT email template
    Only available for admin users for testing purposes
    """
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access this endpoint"
        )
    
    # Sample test data
    sample_data = {
        'url': 'https://fake-netflix-login.github.io/cloneNetflix',
        'risk_score': 95,
        'risk_level': 'critical',
        'classification': 'phishing',
        'confidence': 0.92,
        'reasoning': 'Brand impersonation detected: Netflix clone site with credential harvesting potential',
        'security_analysis': {
            'threat_indicators': {
                'brand_impersonation': True,
                'clone_site': True,
                'credential_harvesting': True,
                'github_pages_abuse': True
            },
            'classification': 'phishing'
        },
        'comments': 'Detected through QR code scanning - potential widespread distribution',
        'user_email': current_user.email
    }
    
    try:
        # Generate test email HTML using production service
        html_content = production_cert_service._create_professional_report(sample_data)
        
        return {
            "success": True,
            "message": "Test email template generated successfully",
            "html_preview": html_content
        }
        
    except Exception as e:
        logger.error(f"Error generating test template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate test email template"
        )

@router.get("/status")
async def get_cert_service_status():
    """
    Get the status of the CERT reporting service
    Public endpoint for service health checks
    """
    
    return {
        "service": "Sri Lanka CERT Reporting",
        "status": "operational",
        "email_service": "configured",
        "recipient": "heshanrashmika9@gmail.com",
        "sender": "ClickSafe_Srilanka@outlook.com",
        "minimum_risk_threshold": 75,
        "last_updated": datetime.now().isoformat()
    }