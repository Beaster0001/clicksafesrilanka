"""
QR Code Scanning API Routes
Modern FastAPI implementation for QR URL safety analysis
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
import asyncio
import os

# Local imports
from database import get_db
from auth_routes import get_current_user
from models import User, UserScan
from qr_service import QRURLSafetyService, convert_numpy_types
from production_cert_service import ProductionCERTService
from qr_cert_service import QRCERTService

qr_service = QRURLSafetyService()
production_cert_service = ProductionCERTService()
qr_cert_service = QRCERTService()

# Models for QR analysis, convert_numpy_types
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Initialize router
qr_router = APIRouter(prefix="/api/qr", tags=["QR Scanner"])

# Optional authentication dependency
security = HTTPBearer(auto_error=False)

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current authenticated user (optional)"""
    if not credentials:
        return None
    
    try:
        from auth import verify_token
        token = credentials.credentials
        payload = verify_token(token)
        
        if payload is None or payload.get("type") != "access":
            return None
        
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.is_active:
            return user
    except:
        pass
    
    return None

# Request/Response Models
class QRImageUploadResponse(BaseModel):
    """Response model for QR image upload and analysis"""
    success: bool
    message: str
    qr_detection: Optional[Dict[str, Any]] = None
    safety_analysis: Optional[Dict[str, Any]] = None
    combined_assessment: Optional[Dict[str, Any]] = None
    scan_id: Optional[str] = None
    processed_at: datetime

class URLAnalysisRequest(BaseModel):
    """Request model for direct URL analysis"""
    url: str
    save_to_history: bool = True
    
    @validator('url')
    def validate_url(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('URL cannot be empty')
        if len(v) > 2000:
            raise ValueError('URL too long (max 2000 characters)')
        return v.strip()

class URLAnalysisResponse(BaseModel):
    """Response model for URL analysis"""
    success: bool
    message: str
    analysis: Optional[Dict[str, Any]] = None
    combined_assessment: Optional[Dict[str, Any]] = None
    url_analysis: Optional[Dict[str, Any]] = None
    scan_id: Optional[str] = None
    processed_at: datetime

class ServiceStatusResponse(BaseModel):
    """Response model for service status"""
    service: str
    version: str
    status: str
    model_loaded: bool
    features: List[str]
    virustotal_enabled: bool

class ScanHistoryResponse(BaseModel):
    """Response model for scan history"""
    scans: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int

@qr_router.post("/scan/image", response_model=QRImageUploadResponse)
async def scan_qr_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Upload and analyze QR code from image
    
    This endpoint accepts image files containing QR codes, extracts the URL,
    and performs comprehensive safety analysis using ML models and external services.
    
    Supported formats: PNG, JPEG, JPG, GIF, BMP, WEBP
    Max file size: 10MB
    """
    try:
        # Validate file
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image (PNG, JPEG, JPG, GIF, BMP, WEBP)"
            )
        
        # Check file size (10MB limit)
        max_size = int(os.getenv('UPLOAD_MAX_SIZE', 10485760))  # 10MB
        file_content = await file.read()
        
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {max_size / 1024 / 1024:.1f}MB"
            )
        
        # Reset file pointer
        await file.seek(0)
        file_content = await file.read()
        
        user_identifier = current_user.email if current_user else "anonymous"
        logger.info(f"Processing QR image upload from user {user_identifier}")
        
        # Scan QR code and analyze URL
        result = await qr_service.scan_qr_from_image(file_content)
        
        # Generate scan ID for tracking
        if current_user:
            scan_id = f"qr-{datetime.now().strftime('%Y%m%d%H%M%S')}-{abs(hash(current_user.email)) % 10000:04d}"
        else:
            scan_id = f"qr-{datetime.now().strftime('%Y%m%d%H%M%S')}-anon"
        
        # Save scan to database for history (only for authenticated users)
        if current_user and result["success"]:
            try:
                decoded_url = result.get('qr_detection', {}).get('decoded_url', '')
                safety_analysis = result.get('safety_analysis', {})
                
                qr_scan = UserScan(
                    user_id=current_user.id,
                    scan_type='qr_code',
                    content=decoded_url,
                    original_content=decoded_url,
                    classification=safety_analysis.get('risk_level', 'unknown'),
                    risk_score=float(safety_analysis.get('risk_score', 0)),
                    language='url',  # URLs don't have language, use 'url' as identifier
                    suspicious_terms=safety_analysis.get('features', {}),
                    explanation=str(safety_analysis.get('recommendations', []))
                )
                db.add(qr_scan)
                db.commit()
                logger.info(f"QR scan saved to history for user {current_user.email}")
            except Exception as e:
                logger.error(f"Failed to save QR scan to history: {str(e)}")
                db.rollback()
        
        if result["success"]:
            logger.info(f"QR scan successful for user {user_identifier}: {result.get('qr_detection', {}).get('decoded_url', 'Unknown URL')}")
        else:
            logger.warning(f"QR scan failed for user {user_identifier}: {result.get('message')}")
        
        # Transform response to match frontend expectations
        response_data = {
            "success": result["success"],
            "message": result["message"],
            "qr_detection": result.get("qr_detection"),
            "safety_analysis": result.get("safety_analysis"),
            "scan_id": scan_id,
            "processed_at": datetime.now()
        }
        
        # Add combined_assessment for frontend compatibility
        if result.get("safety_analysis"):
            safety = result["safety_analysis"]
            risk_score = safety.get("risk_score", 30)  # Default to medium risk
            risk_level = safety.get("risk_level", "medium")  # Default to medium
            
            # Ensure we have valid recommendations based on risk score
            recommendations = safety.get("recommendations", [])
            if not recommendations:
                # Generate default recommendations based on risk score
                if risk_score >= 80:
                    recommendations = ["⚠️ HIGH RISK: Exercise extreme caution with this URL"]
                elif risk_score >= 60:
                    recommendations = ["⚠️ CAUTION: Verify this URL before proceeding"]
                elif risk_score >= 40:
                    recommendations = ["⚠️ BE CAREFUL: Check website authenticity"]
                else:
                    recommendations = ["✅ Appears relatively safe, but stay vigilant"]
            
            response_data["combined_assessment"] = {
                "final_risk_score": risk_score,
                "final_risk_level": risk_level,
                "confidence": safety.get("ml_prediction", {}).get("confidence", 0.5) if safety.get("ml_prediction") else 0.5,
                "reasoning": safety.get("ml_prediction", {}).get("prediction", "Analysis completed") if safety.get("ml_prediction") else "Analysis completed",
                "threat_indicators": safety.get("features", {}),
                "recommendation": recommendations[0] if recommendations else "Unknown recommendation",  # Frontend expects singular
                "recommendations": recommendations  # Full array for completeness
            }
        else:
            # Provide default assessment when safety analysis fails
            fallback_recommendations = ["⚠️ CAUTION: Could not analyze URL completely", "Verify URL manually before proceeding"]
            response_data["combined_assessment"] = {
                "final_risk_score": 50,
                "final_risk_level": "medium",
                "confidence": 0.5,
                "reasoning": "Unable to complete full analysis",
                "threat_indicators": {},
                "recommendation": fallback_recommendations[0],  # Frontend expects singular
                "recommendations": fallback_recommendations  # Full array for completeness
            }
        
        # Convert any remaining numpy types to native Python types
        response_data = convert_numpy_types(response_data)
        
        return QRImageUploadResponse(
            success=response_data["success"],
            message=response_data["message"],
            qr_detection=response_data.get("qr_detection"),
            safety_analysis=response_data.get("safety_analysis"),
            combined_assessment=response_data.get("combined_assessment"),
            scan_id=scan_id,
            processed_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"QR image processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during QR image processing"
        )

@qr_router.post("/scan/url", response_model=URLAnalysisResponse)
async def analyze_url_direct(
    request: URLAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Analyze URL safety directly without QR code
    
    This endpoint accepts a URL and performs comprehensive safety analysis,
    useful for manual URL verification or integration with other systems.
    """
    try:
        user_identifier = current_user.email if current_user else "anonymous"
        logger.info(f"Direct URL analysis requested by {user_identifier}: {request.url}")
        
        # Analyze URL safety
        analysis = await qr_service.analyze_url_safety(request.url)
        
        # Generate scan ID
        if current_user:
            scan_id = f"url-{datetime.now().strftime('%Y%m%d%H%M%S')}-{abs(hash(current_user.email)) % 10000:04d}"
        else:
            scan_id = f"url-{datetime.now().strftime('%Y%m%d%H%M%S')}-anon"
        
        # Save to database if requested (only for authenticated users)
        if current_user and request.save_to_history and analysis:
            try:
                url_scan = UserScan(
                    user_id=current_user.id,
                    scan_type='url',
                    content=request.url,
                    original_content=request.url,
                    classification=analysis.get('risk_level', 'unknown'),
                    risk_score=float(analysis.get('risk_score', 0)),
                    language='url',
                    suspicious_terms=analysis.get('features', {}),
                    explanation=str(analysis.get('recommendations', []))
                )
                db.add(url_scan)
                db.commit()
                logger.info(f"URL analysis saved to history for user {current_user.email}")
            except Exception as e:
                logger.error(f"Failed to save URL analysis to history: {str(e)}")
                db.rollback()
        
        logger.info(f"URL analysis completed for {user_identifier}: Risk score {analysis.get('risk_score', 'unknown')}")
        
        # Transform response for frontend compatibility
        recommendations = analysis.get("recommendations", [])
        combined_assessment = {
            "final_risk_score": analysis.get("risk_score", 0),
            "final_risk_level": analysis.get("risk_level", "unknown"),
            "confidence": analysis.get("ml_prediction", {}).get("confidence", 0.5) if analysis.get("ml_prediction") else 0.5,
            "reasoning": analysis.get("ml_prediction", {}).get("prediction", "Analysis completed") if analysis.get("ml_prediction") else "Analysis completed",
            "threat_indicators": analysis.get("features", {}),
            "recommendation": recommendations[0] if recommendations else "No specific recommendation available",  # Frontend expects singular
            "recommendations": recommendations  # Full array for completeness
        }
        
        url_analysis = {
            "url": analysis.get("url"),
            "risk_score": analysis.get("risk_score", 0),
            "risk_level": analysis.get("risk_level", "unknown"),
            "analyzed_at": analysis.get("analyzed_at")
        }
        
        # Convert numpy types to native Python types
        combined_assessment = convert_numpy_types(combined_assessment)
        url_analysis = convert_numpy_types(url_analysis)
        analysis = convert_numpy_types(analysis)
        
        return URLAnalysisResponse(
            success=True,
            message="URL analysis completed successfully",
            analysis=analysis,
            combined_assessment=combined_assessment,
            url_analysis=url_analysis,
            scan_id=scan_id,
            processed_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"URL analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during URL analysis"
        )

@qr_router.get("/scan/history", response_model=ScanHistoryResponse)
async def get_scan_history(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's QR scan history
    
    Returns paginated list of previous QR scans and URL analyses
    performed by the authenticated user.
    """
    try:
        # Query user's scan history
        offset = (page - 1) * page_size
        
        # Get total count
        total_count = db.query(UserScan).filter(
            UserScan.user_id == current_user.id,
            UserScan.scan_type.in_(['qr_code', 'url'])
        ).count()
        
        # Get paginated results
        scans = db.query(UserScan).filter(
            UserScan.user_id == current_user.id,
            UserScan.scan_type.in_(['qr_code', 'url'])
        ).order_by(UserScan.created_at.desc()).offset(offset).limit(page_size).all()
        
        # Convert to response format
        scan_list = []
        for scan in scans:
            scan_data = {
                "id": scan.id,
                "scan_type": scan.scan_type,
                "content": scan.content,
                "risk_score": scan.risk_score,
                "classification": scan.classification,
                "risk_level": scan.classification,  # For frontend compatibility
                "recommendations": eval(scan.explanation) if scan.explanation.startswith('[') else [scan.explanation],
                "scanned_at": scan.created_at.isoformat(),
                "features": scan.suspicious_terms or {}
            }
            scan_list.append(scan_data)
        
        return ScanHistoryResponse(
            scans=scan_list,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Scan history retrieval error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving scan history"
        )

@qr_router.get("/scan/{scan_id}")
async def get_scan_details(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific scan by ID
    
    Returns detailed information about a previous QR scan or URL analysis,
    including full analysis results and metadata.
    """
    try:
        # TODO: Implement database query for specific scan
        # This would fetch specific scan details from your database
        
        # For now, return not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan with ID {scan_id} not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scan details retrieval error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving scan details"
        )

@qr_router.get("/status", response_model=ServiceStatusResponse)
async def get_service_status():
    """
    Get QR service status and capabilities
    
    Public endpoint that returns information about the QR scanning service,
    including model status, available features, and service health.
    """
    try:
        status_info = qr_service.get_service_status()
        
        return ServiceStatusResponse(
            service=status_info["service"],
            version=status_info["version"],
            status=status_info["status"],
            model_loaded=status_info["model_loaded"],
            features=status_info["features"],
            virustotal_enabled=status_info["virustotal_enabled"]
        )
        
    except Exception as e:
        logger.error(f"Service status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while checking service status"
        )

@qr_router.get("/analytics")
async def get_qr_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get QR scanning analytics for admin users
    
    Returns analytics data about QR scanning usage, threat detection rates,
    and service performance metrics. Restricted to admin users.
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for analytics"
            )
        
        # TODO: Implement analytics queries
        # This would generate analytics from your database
        
        analytics = {
            "total_scans": 0,
            "threats_detected": 0,
            "detection_rate": 0.0,
            "top_threat_types": [],
            "scan_trends": [],
            "user_activity": [],
            "generated_at": datetime.now().isoformat()
        }
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while generating analytics"
        )

# Health check endpoint
@qr_router.get("/health")
async def health_check():
    """Quick health check for QR service"""
    return {
        "status": "healthy",
        "service": "QR URL Safety Analysis",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": qr_service.model_loaded
    }

# QR CERT Reporting Models (Following exact pattern from working phishing detection)
class QRCERTReportRequest(BaseModel):
    """Request model for QR CERT reports - flexible to handle frontend data"""
    # Primary fields (new format)
    url: Optional[str] = None  # QR URL that was detected as malicious
    content: Optional[str] = ""  # Description of the QR code threat
    risk_score: Optional[int] = None  # Risk score from QR analysis
    risk_level: Optional[str] = None  # Risk level (medium, high, critical)
    classification: Optional[str] = None  # Classification of the threat
    confidence: Optional[float] = None  # Confidence level (0.0 to 1.0)
    reasoning: Optional[str] = ""  # Reasoning for the classification
    security_analysis: Optional[dict] = None  # Security analysis data
    comments: Optional[str] = ""  # User comments
    
    # Legacy fields (old format compatibility)
    qr_url: Optional[str] = None  # Old format QR URL
    user_comments: Optional[str] = None  # Old format comments
    scan_id: Optional[str] = None  # Old format scan ID
    
    @validator('risk_score')
    def validate_risk_score(cls, v):
        if v is not None and not (0 <= v <= 100):
            raise ValueError('Risk score must be between 0 and 100')
        return v
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if v is not None and not (0 <= v <= 1):
            raise ValueError('Confidence must be between 0 and 1')
        return v

class QRCERTReportResponse(BaseModel):
    """Response model for QR CERT report submission - mirrors phishing detection pattern"""
    success: bool
    message: str
    report_id: Optional[str] = None
    submitted_at: datetime

@qr_router.post("/report/cert", response_model=QRCERTReportResponse)
async def submit_qr_cert_report(
    report: QRCERTReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a malicious QR code report to Sri Lanka CERT
    
    This endpoint follows the EXACT same pattern as the working phishing detection
    CERT reporting to ensure consistency and reliability.
    
    Requirements:
    - User must be authenticated
    - Risk score must be >= 50% (medium risk and above)
    - Valid URL and security analysis data required
    """
    
    try:
        # DEBUG: Log the incoming request data to identify the issue
        logger.info(f"🔍 QR CERT DEBUG - Raw incoming request data:")
        logger.info(f"   All fields: {report.dict()}")
        
        # Normalize data from either old or new format
        qr_url = report.url or report.qr_url
        user_comments = report.comments or report.user_comments or ""
        risk_score = report.risk_score
        risk_level = report.risk_level
        classification = report.classification or f"malicious_qr_code"
        confidence = report.confidence
        security_analysis = report.security_analysis or {"classification": classification}
        
        # If we don't have the new format fields, try to derive them
        if not qr_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="QR URL is required"
            )
        
        if risk_score is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Risk score is required"
            )
        
        if not risk_level:
            # Derive risk level from score if not provided
            if risk_score >= 80:
                risk_level = "critical"
            elif risk_score >= 60:
                risk_level = "high"
            else:
                risk_level = "medium"
        
        if confidence is None:
            # Derive confidence from risk score if not provided
            confidence = min(risk_score / 100.0, 1.0)
        
        logger.info(f"🔍 QR CERT DEBUG - Normalized data:")
        logger.info(f"   QR URL: {qr_url}")
        logger.info(f"   Risk Score: {risk_score}")
        logger.info(f"   Risk Level: {risk_level}")
        logger.info(f"   Classification: {classification}")
        logger.info(f"   Confidence: {confidence}")
        logger.info(f"   Comments: {user_comments}")
        
        # Validate risk threshold - EXACTLY same as phishing detection
        if risk_score < 50:  # Accept medium risk (50+) and above
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CERT reports are only accepted for medium-risk threats and above (score >= 50%)"
            )
        
        # Prepare report data - EXACTLY same structure as phishing detection (using normalized data)
        content = report.content or f"QR code detected leading to: {qr_url}. User comments: {user_comments or 'None provided'}"
        reasoning = report.reasoning or f"QR code analysis detected {risk_level} risk level with score {risk_score}/100"
        
        report_data = {
            'url': qr_url,
            'content': content,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'classification': classification,
            'confidence': confidence,
            'reasoning': reasoning,
            'security_analysis': security_analysis,
            'comments': user_comments,
            'user_email': current_user.email,
            'submitted_by': current_user.full_name or current_user.username,
            'submission_time': datetime.now()
        }
        
        # Log the report attempt - EXACTLY same as phishing detection
        logger.info(f"QR CERT report submission attempt by {current_user.email} for URL: {qr_url}")
        
        # Send email to CERT using dedicated QR CERT service
        cert_result = await qr_cert_service.submit_qr_cert_report(report_data)
        
        if not cert_result.get('success') or not cert_result.get('email_sent'):
            logger.error(f"QR CERT submission failed: {cert_result.get('error', 'Email delivery failed')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send report to CERT: {cert_result.get('error', 'Email delivery failed')}"
            )
        
        # Generate report ID for tracking - same pattern with QR prefix
        report_id = f"QR-{datetime.now().strftime('%Y%m%d')}-{abs(hash(qr_url)) % 10000:04d}"
        
        # Log successful submission - EXACTLY same as phishing detection
        logger.info(f"QR CERT report {report_id} successfully submitted for URL: {qr_url}")
        
        # TODO: Store report in database for tracking
        # This could be implemented later for report history and analytics
        
        return QRCERTReportResponse(
            success=True,
            message="QR threat report successfully submitted to Sri Lanka CERT. You will receive a confirmation email shortly.",
            report_id=report_id,
            submitted_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting QR CERT report: {str(e)}")
        logger.exception("Full QR CERT error traceback:")
        
        # Provide more specific error messages for common issues
        error_detail = str(e)
        if "[object Object]" in error_detail:
            error_detail = "Data format error: Invalid object serialization in request data"
        elif "validation error" in error_detail.lower():
            error_detail = f"Validation error: {error_detail}"
        else:
            error_detail = "Internal server error while processing QR CERT report"
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


# NEW DEDICATED QR CERT ENDPOINT
@qr_router.post("/report/cert-v2", response_model=QRCERTReportResponse)
async def submit_qr_cert_report_v2(
    report: QRCERTReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a QR CERT report using the dedicated QR CERT service
    This is a new endpoint that uses a separate service for better reliability
    """
    
    try:
        logger.info(f"🔄 QR CERT V2: Starting submission by {current_user.email}")
        
        # Prepare data for the dedicated service
        service_data = {
            'url': report.url or report.qr_url,
            'content': report.content,
            'risk_score': report.risk_score,
            'risk_level': report.risk_level,
            'classification': report.classification,
            'confidence': report.confidence,
            'reasoning': report.reasoning,
            'security_analysis': report.security_analysis,
            'comments': report.comments or report.user_comments,
            'user_email': current_user.email,
            'submitted_by': current_user.full_name or current_user.username,
            'scan_id': report.scan_id
        }
        
        # Use the dedicated QR CERT service
        result = await qr_cert_service.submit_qr_cert_report(service_data)
        
        if result['success'] and result['email_sent']:
            logger.info(f"✅ QR CERT V2: Report {result['report_id']} submitted successfully")
            
            return QRCERTReportResponse(
                success=True,
                message="QR threat report successfully submitted to Sri Lanka CERT using dedicated service. Email confirmation sent.",
                report_id=result['report_id'],
                submitted_at=datetime.fromisoformat(result['submitted_at'])
            )
        else:
            logger.error(f"❌ QR CERT V2: Submission failed - {result.get('error', 'Unknown error')}")
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"QR CERT submission failed: {result.get('error', 'Email delivery failed')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 QR CERT V2: Exception - {str(e)}")
        logger.exception("QR CERT V2 exception details:")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"QR CERT V2 service error: {str(e)}"
        )