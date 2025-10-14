"""
Admin and user management routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_

from database import get_db
from models import User, UserActivity, UserScan, AdminLog
from schemas import (
    AdminUserList, AdminUserActivity, AdminStats,
    UserResponse, ActivityResponse, PasswordChange
)
from auth_routes import get_current_admin_user, get_current_user, log_user_activity

# Create router
admin_router = APIRouter(prefix="/admin", tags=["Admin"])
user_router = APIRouter(prefix="/users", tags=["User Management"])

# Helper function to log admin activity
async def log_admin_activity(
    admin_user_id: int,
    action: str,
    target_user_id: int = None,
    description: str = None,
    details: dict = None,
    request: Request = None,
    db: Session = None
):
    """Log admin activity"""
    if db is None:
        return
    
    admin_log = AdminLog(
        admin_user_id=admin_user_id,
        action=action,
        target_user_id=target_user_id,
        description=description,
        details=details,
        ip_address=request.client.host if request else None
    )
    
    db.add(admin_log)
    db.commit()

@admin_router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    
    # Count total users
    total_users = db.query(User).count()
    
    # Count active users (logged in within last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users = db.query(User).filter(User.last_login >= thirty_days_ago).count()
    
    # Count total scans
    total_scans = db.query(UserScan).count()
    
    # Count dangerous scans today
    today = datetime.utcnow().date()
    dangerous_scans_today = db.query(UserScan).filter(
        and_(
            func.date(UserScan.created_at) == today,
            UserScan.classification == 'dangerous'
        )
    ).count()
    
    # Get recent activities
    recent_activities = db.query(UserActivity).order_by(
        desc(UserActivity.created_at)
    ).limit(10).all()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_scans": total_scans,
        "dangerous_scans_today": dangerous_scans_today,
        "recent_activities": recent_activities
    }

@admin_router.get("/users", response_model=List[AdminUserList])
async def get_all_users(
    request: Request,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Get list of all users"""
    
    query = db.query(
        User.id,
        User.email,
        User.username,
        User.full_name,
        User.is_active,
        User.last_login,
        User.created_at,
        func.count(UserScan.id).label('scan_count')
    ).outerjoin(UserScan)
    
    # Apply filters
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_filter)) |
            (User.username.ilike(search_filter)) |
            (User.full_name.ilike(search_filter))
        )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Group by user and apply pagination
    users = query.group_by(User.id).offset(skip).limit(limit).all()
    
    # Log admin activity
    await log_admin_activity(
        admin_user_id=admin_user.id,
        action="view_users",
        description=f"Viewed user list (search: {search}, active: {is_active})",
        request=request,
        db=db
    )
    
    return users

@admin_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_details(
    user_id: int,
    request: Request,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get detailed user information"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log admin activity
    await log_admin_activity(
        admin_user_id=admin_user.id,
        action="view_user_details",
        target_user_id=user_id,
        description=f"Viewed details for user {user.email}",
        request=request,
        db=db
    )
    
    return user

@admin_router.get("/users/{user_id}/activities", response_model=List[AdminUserActivity])
async def get_user_activities(
    user_id: int,
    request: Request,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=500)
):
    """Get user activity history"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    activities = db.query(UserActivity).filter(
        UserActivity.user_id == user_id
    ).order_by(desc(UserActivity.created_at)).limit(limit).all()
    
    # Log admin activity
    await log_admin_activity(
        admin_user_id=admin_user.id,
        action="view_user_activities",
        target_user_id=user_id,
        description=f"Viewed activities for user {user.email}",
        request=request,
        db=db
    )
    
    return activities

@admin_router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete admin users"
        )
    
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete yourself"
        )
    
    user_email = user.email
    
    # Delete user (cascade will handle related records)
    db.delete(user)
    db.commit()
    
    # Log admin activity
    await log_admin_activity(
        admin_user_id=admin_user.id,
        action="delete_user",
        target_user_id=user_id,
        description=f"Deleted user {user_email}",
        request=request,
        db=db
    )
    
    return {"message": f"User {user_email} deleted successfully"}

@admin_router.patch("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    request: Request,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Activate a user account"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    db.commit()
    
    # Log admin activity
    await log_admin_activity(
        admin_user_id=admin_user.id,
        action="activate_user",
        target_user_id=user_id,
        description=f"Activated user {user.email}",
        request=request,
        db=db
    )
    
    return {"message": f"User {user.email} activated successfully"}

@admin_router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    request: Request,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Deactivate a user account"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot deactivate admin users"
        )
    
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot deactivate yourself"
        )
    
    user.is_active = False
    db.commit()
    
    # Log admin activity
    await log_admin_activity(
        admin_user_id=admin_user.id,
        action="deactivate_user",
        target_user_id=user_id,
        description=f"Deactivated user {user.email}",
        request=request,
        db=db
    )
    
    return {"message": f"User {user.email} deactivated successfully"}

# User profile management routes
@user_router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

@user_router.patch("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_data: dict,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    
    # Update allowed fields
    allowed_fields = ['full_name', 'profile_picture', 'phone', 'location', 'bio', 'website', 'username']
    for field in allowed_fields:
        if field in profile_data:
            setattr(current_user, field, profile_data[field])
    
    db.commit()
    db.refresh(current_user)
    
    # Log activity
    await log_user_activity(
        user_id=current_user.id,
        activity_type="profile_update",
        description="Profile updated",
        details=profile_data,
        request=request,
        db=db
    )
    
    return current_user

@user_router.get("/activities", response_model=List[ActivityResponse])
async def get_user_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200)
):
    """Get current user's activity history"""
    
    activities = db.query(UserActivity).filter(
        UserActivity.user_id == current_user.id
    ).order_by(desc(UserActivity.created_at)).limit(limit).all()
    
    return activities

@user_router.post("/change-password")
async def change_user_password(
    password_data: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    from auth import verify_password, get_password_hash
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    # Log activity
    await log_user_activity(
        user_id=current_user.id,
        activity_type="password_change",
        description="Password changed",
        request=request,
        db=db
    )
    
    return {"message": "Password changed successfully"}

@user_router.delete("/account")
async def delete_user_account(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user account"""
    
    # Log activity before deletion
    await log_user_activity(
        user_id=current_user.id,
        activity_type="account_deletion",
        description="Account deleted",
        request=request,
        db=db
    )
    
    # Delete user
    db.delete(current_user)
    db.commit()
    
    return {"message": "Account deleted successfully"}

@user_router.get("/export-data")
async def export_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    format: str = Query("json", regex="^(json|csv|xml)$")
):
    """Export user data"""
    
    # Get user's activities
    activities = db.query(UserActivity).filter(
        UserActivity.user_id == current_user.id
    ).all()
    
    # Get user's scans
    from models import UserScan
    scans = db.query(UserScan).filter(
        UserScan.user_id == current_user.id
    ).all()
    
    data = {
        "user_profile": {
            "email": current_user.email,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
        },
        "activities": [
            {
                "activity_type": activity.activity_type,
                "description": activity.description,
                "created_at": activity.created_at.isoformat() if activity.created_at else None,
            }
            for activity in activities
        ],
        "scans": [
            {
                "content": scan.content,
                "scan_type": scan.scan_type,
                "classification": scan.classification,
                "risk_score": scan.risk_score,
                "language": scan.language,
                "created_at": scan.created_at.isoformat() if scan.created_at else None,
            }
            for scan in scans
        ]
    }
    
    if format == "json":
        return data
    
    elif format == "csv":
        import io
        import csv
        from fastapi.responses import StreamingResponse
        
        output = io.StringIO()
        
        # Write user profile
        output.write("USER PROFILE\n")
        writer = csv.writer(output)
        writer.writerow(["Field", "Value"])
        for key, value in data["user_profile"].items():
            writer.writerow([key, value])
        output.write("\n")
        
        # Write activities
        output.write("ACTIVITIES\n")
        writer.writerow(["Activity Type", "Description", "Created At"])
        for activity in data["activities"]:
            writer.writerow([activity["activity_type"], activity["description"], activity["created_at"]])
        output.write("\n")
        
        # Write scans
        output.write("SCANS\n")
        writer.writerow(["Content", "Scan Type", "Classification", "Risk Score", "Language", "Created At"])
        for scan in data["scans"]:
            writer.writerow([scan["content"], scan["scan_type"], scan["classification"], scan["risk_score"], scan["language"], scan["created_at"]])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=user_data.csv"}
        )
    
    elif format == "xml":
        from fastapi.responses import Response
        
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += '<user_data>\n'
        
        # User profile
        xml_content += '  <user_profile>\n'
        for key, value in data["user_profile"].items():
            xml_content += f'    <{key}>{value if value is not None else ""}</{key}>\n'
        xml_content += '  </user_profile>\n'
        
        # Activities
        xml_content += '  <activities>\n'
        for activity in data["activities"]:
            xml_content += '    <activity>\n'
            xml_content += f'      <activity_type>{activity["activity_type"]}</activity_type>\n'
            xml_content += f'      <description>{activity["description"]}</description>\n'
            xml_content += f'      <created_at>{activity["created_at"]}</created_at>\n'
            xml_content += '    </activity>\n'
        xml_content += '  </activities>\n'
        
        # Scans
        xml_content += '  <scans>\n'
        for scan in data["scans"]:
            xml_content += '    <scan>\n'
            xml_content += f'      <content>{scan["content"]}</content>\n'
            xml_content += f'      <scan_type>{scan["scan_type"]}</scan_type>\n'
            xml_content += f'      <classification>{scan["classification"]}</classification>\n'
            xml_content += f'      <risk_score>{scan["risk_score"]}</risk_score>\n'
            xml_content += f'      <language>{scan["language"]}</language>\n'
            xml_content += f'      <created_at>{scan["created_at"]}</created_at>\n'
            xml_content += '    </scan>\n'
        xml_content += '  </scans>\n'
        xml_content += '</user_data>'
        
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={"Content-Disposition": "attachment; filename=user_data.xml"}
        )

@user_router.get("/settings")
async def get_user_settings(
    current_user: User = Depends(get_current_user)
):
    """Get user settings"""
    # Return default settings for now
    # In a real implementation, you'd have a UserSettings model
    return {
        "theme": "system",
        "language": "en",
        "notifications": {
            "email": True,
            "push": True,
            "security_alerts": True
        },
        "privacy": {
            "profile_visibility": "public",
            "show_activity": True,
            "show_stats": True
        }
    }

@user_router.patch("/settings")
async def update_user_settings(
    settings_data: dict,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user settings"""
    
    # In a real implementation, you'd save these to a UserSettings model
    # For now, just log the activity
    await log_user_activity(
        user_id=current_user.id,
        activity_type="settings_update",
        description="Settings updated",
        details=settings_data,
        request=request,
        db=db
    )
    
    return {"message": "Settings updated successfully", "settings": settings_data}