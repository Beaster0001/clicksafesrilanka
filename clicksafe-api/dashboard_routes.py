"""
Dashboard and scan history routes
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_

from database import get_db
from models import User, UserScan, UserActivity, RecentScam
from schemas import (
    ScanCreate, ScanResponse, ScanFilter, UserStats, DashboardData,
    RecentScamResponse
)
from auth_routes import get_current_user, log_user_activity
from auth import anonymize_content

# Create routers
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
scans_router = APIRouter(prefix="/scans", tags=["Scans"])

@dashboard_router.get("/", response_model=DashboardData)
async def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user dashboard data"""
    
    # Get user scan statistics
    total_scans = db.query(UserScan).filter(UserScan.user_id == current_user.id).count()
    
    safe_scans = db.query(UserScan).filter(
        and_(UserScan.user_id == current_user.id, UserScan.classification == 'safe')
    ).count()
    
    suspicious_scans = db.query(UserScan).filter(
        and_(UserScan.user_id == current_user.id, UserScan.classification == 'suspicious')
    ).count()
    
    dangerous_scans = db.query(UserScan).filter(
        and_(UserScan.user_id == current_user.id, UserScan.classification == 'dangerous')
    ).count()
    
    # Get recent scans (last 10)
    recent_scans = db.query(UserScan).filter(
        UserScan.user_id == current_user.id
    ).order_by(desc(UserScan.created_at)).limit(10).all()
    
    # Get recent activities (last 10)
    recent_activities = db.query(UserActivity).filter(
        UserActivity.user_id == current_user.id
    ).order_by(desc(UserActivity.created_at)).limit(10).all()
    
    # Convert activities to dict format
    activities_data = []
    for activity in recent_activities:
        activities_data.append({
            "id": activity.id,
            "activity_type": activity.activity_type,
            "description": activity.description,
            "created_at": activity.created_at,
            "details": activity.details
        })
    
    user_stats = UserStats(
        total_scans=total_scans,
        safe_scans=safe_scans,
        suspicious_scans=suspicious_scans,
        dangerous_scans=dangerous_scans,
        recent_scans=recent_scans
    )
    
    return DashboardData(
        user=current_user,
        stats=user_stats,
        recent_activities=activities_data
    )

@scans_router.post("/", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    scan_data: ScanCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new scan record and analyze content"""
    
    try:
        # Use simple detector directly
        from simple_detector import simple_predict
        
        # Analyze the content
        analysis_result = simple_predict(scan_data.content)
        
        # Create scan record
        new_scan = UserScan(
            user_id=current_user.id,
            scan_type=scan_data.scan_type,
            content=scan_data.content,
            original_content=scan_data.content,
            classification=analysis_result.get('classification', 'unknown'),
            risk_score=analysis_result.get('risk_score', 0.0),
            language=analysis_result.get('language', 'unknown'),
            suspicious_terms=analysis_result.get('suspicious_terms', []),
            explanation=analysis_result.get('explanation', ''),
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        db.add(new_scan)
        db.commit()
        db.refresh(new_scan)
        
        # Log scan activity
        await log_user_activity(
            user_id=current_user.id,
            activity_type="scan",
            description=f"Scanned {scan_data.scan_type}: {analysis_result.get('classification', 'unknown')}",
            details={
                "scan_id": new_scan.id,
                "scan_type": scan_data.scan_type,
                "classification": analysis_result.get('classification'),
                "risk_score": analysis_result.get('risk_score')
            },
            request=request,
            db=db
        )
        
        # If it's a high-risk scam, add to recent scams feed
        if (analysis_result.get('classification') == 'dangerous' or 
            analysis_result.get('risk_score', 0) > 0.7):
            await add_to_recent_scams(new_scan, db)
        
        return new_scan
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze content: {str(e)}"
        )

@scans_router.get("/", response_model=List[ScanResponse])
async def get_user_scans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    scan_type: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Get user's scan history with filters"""
    
    query = db.query(UserScan).filter(UserScan.user_id == current_user.id)
    
    # Apply filters
    if scan_type:
        query = query.filter(UserScan.scan_type == scan_type)
    
    if classification:
        query = query.filter(UserScan.classification == classification)
    
    if language:
        query = query.filter(UserScan.language == language)
    
    if date_from:
        query = query.filter(UserScan.created_at >= date_from)
    
    if date_to:
        # Add one day to include the entire end date
        date_to_end = date_to + timedelta(days=1)
        query = query.filter(UserScan.created_at < date_to_end)
    
    # Order by most recent and apply pagination
    scans = query.order_by(desc(UserScan.created_at)).offset(offset).limit(limit).all()
    
    return scans

@scans_router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan_details(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed scan information"""
    
    scan = db.query(UserScan).filter(
        and_(UserScan.id == scan_id, UserScan.user_id == current_user.id)
    ).first()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    return scan

@scans_router.delete("/{scan_id}")
async def delete_scan(
    scan_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a scan record"""
    
    scan = db.query(UserScan).filter(
        and_(UserScan.id == scan_id, UserScan.user_id == current_user.id)
    ).first()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    db.delete(scan)
    db.commit()
    
    # Log deletion activity
    await log_user_activity(
        user_id=current_user.id,
        activity_type="scan_deletion",
        description=f"Deleted {scan.scan_type} scan",
        details={"deleted_scan_id": scan_id},
        request=request,
        db=db
    )
    
    return {"message": "Scan deleted successfully"}

@scans_router.get("/stats/summary")
async def get_scan_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """Get scan statistics for the user"""
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get scans within date range
    scans_query = db.query(UserScan).filter(
        and_(
            UserScan.user_id == current_user.id,
            UserScan.created_at >= start_date,
            UserScan.created_at <= end_date
        )
    )
    
    # Count by classification
    stats = {
        "total_scans": scans_query.count(),
        "safe_scans": scans_query.filter(UserScan.classification == 'safe').count(),
        "suspicious_scans": scans_query.filter(UserScan.classification == 'suspicious').count(),
        "dangerous_scans": scans_query.filter(UserScan.classification == 'dangerous').count()
    }
    
    # Count by scan type
    scan_types = db.query(
        UserScan.scan_type,
        func.count(UserScan.id).label('count')
    ).filter(
        and_(
            UserScan.user_id == current_user.id,
            UserScan.created_at >= start_date,
            UserScan.created_at <= end_date
        )
    ).group_by(UserScan.scan_type).all()
    
    stats["scan_types"] = {scan_type: count for scan_type, count in scan_types}
    
    # Count by language
    languages = db.query(
        UserScan.language,
        func.count(UserScan.id).label('count')
    ).filter(
        and_(
            UserScan.user_id == current_user.id,
            UserScan.created_at >= start_date,
            UserScan.created_at <= end_date
        )
    ).group_by(UserScan.language).all()
    
    stats["languages"] = {language: count for language, count in languages}
    
    return stats

# Recent scams public feed
@scans_router.get("/recent-scams/public", response_model=List[RecentScamResponse])
async def get_recent_scams(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    language: Optional[str] = Query(None)
):
    """Get recent high-risk scam messages (public, anonymized)"""
    
    query = db.query(RecentScam).filter(RecentScam.is_public == True)
    
    if language:
        query = query.filter(RecentScam.original_language == language)
    
    recent_scams = query.order_by(desc(RecentScam.created_at)).limit(limit).all()
    
    return recent_scams

# Helper function to add high-risk scams to public feed
async def add_to_recent_scams(scan: UserScan, db: Session):
    """Add high-risk scan to recent scams feed with anonymization"""
    
    try:
        # Anonymize the content
        anonymized = anonymize_content(scan.content)
        
        # Normalize content for better duplicate detection
        def normalize_content(content):
            import re
            # Remove extra whitespace, normalize line breaks, convert to lowercase
            normalized = re.sub(r'\s+', ' ', content.lower().strip())
            # Remove common variations in punctuation
            normalized = re.sub(r'[!.]{2,}', '!', normalized)
            return normalized
        
        normalized_content = normalize_content(anonymized)
        
        # Check if similar scam already exists with fuzzy matching
        existing_scams = db.query(RecentScam).filter(
            RecentScam.original_language == scan.language
        ).all()
        
        existing_scam = None
        for scam in existing_scams:
            existing_normalized = normalize_content(scam.anonymized_content)
            # Check if content is very similar (simple similarity check)
            if (len(existing_normalized) > 0 and len(normalized_content) > 0 and
                (existing_normalized in normalized_content or 
                 normalized_content in existing_normalized or
                 abs(len(existing_normalized) - len(normalized_content)) / max(len(existing_normalized), len(normalized_content)) < 0.1)):
                existing_scam = scam
                break
        
        if existing_scam:
            # Update scan count and risk score (use higher risk score)
            existing_scam.scan_count += 1
            existing_scam.risk_score = max(existing_scam.risk_score, scan.risk_score)
            existing_scam.updated_at = datetime.utcnow()
            # Update classification if new one is more severe
            severity_order = {'safe': 0, 'suspicious': 1, 'dangerous': 2, 'high': 3, 'critical': 4}
            if severity_order.get(scan.classification, 0) > severity_order.get(existing_scam.classification, 0):
                existing_scam.classification = scan.classification
            # Merge suspicious terms
            if scan.suspicious_terms:
                existing_terms = set(existing_scam.suspicious_terms or [])
                new_terms = set(scan.suspicious_terms)
                existing_scam.suspicious_terms = list(existing_terms.union(new_terms))
        else:
            # Create new recent scam entry
            recent_scam = RecentScam(
                anonymized_content=anonymized,
                original_language=scan.language,
                risk_score=scan.risk_score,
                classification=scan.classification,
                suspicious_terms=scan.suspicious_terms,
                scan_count=1
            )
            db.add(recent_scam)
        
        db.commit()
        
    except Exception as e:
        # Don't fail the main scan if this fails
        print(f"Failed to add to recent scams: {e}")
        db.rollback()