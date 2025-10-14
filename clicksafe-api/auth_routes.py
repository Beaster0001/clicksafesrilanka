"""
Authentication routes and dependencies
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database import get_db
from models import User, UserActivity, PasswordResetToken
from schemas import (
    UserCreate, UserLogin, UserResponse, Token, TokenRefresh,
    PasswordReset, PasswordResetConfirm, PasswordChange,
    OAuthUserCreate, ActivityCreate
)
from auth import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, verify_token, generate_reset_token
)

# Create router
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security scheme
security = HTTPBearer()

# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

# Dependency to get current admin user
async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current authenticated admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Helper function to log user activity
async def log_user_activity(
    user_id: int,
    activity_type: str,
    description: str = None,
    details: dict = None,
    request: Request = None,
    db: Session = None
):
    """Log user activity"""
    if db is None:
        return
    
    activity = UserActivity(
        user_id=user_id,
        activity_type=activity_type,
        description=description,
        details=details,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    
    db.add(activity)
    db.commit()

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create new user
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log registration activity
    await log_user_activity(
        user_id=new_user.id,
        activity_type="registration",
        description="User registered successfully",
        request=request,
        db=db
    )
    
    return new_user

@auth_router.post("/login", response_model=Token)
async def login_user(
    user_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login user and return JWT tokens"""
    
    # Find user by email
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Log login activity
    await log_user_activity(
        user_id=user.id,
        activity_type="login",
        description="User logged in successfully",
        request=request,
        db=db
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@auth_router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    
    payload = verify_token(token_data.refresh_token)
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user
    }

@auth_router.post("/oauth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def oauth_register(
    user_data: OAuthUserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register user via OAuth (Google/Facebook)"""
    
    # Check if user already exists by email or OAuth ID
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | 
        (User.google_id == user_data.google_id) if user_data.google_id else False |
        (User.facebook_id == user_data.facebook_id) if user_data.facebook_id else False
    ).first()
    
    if existing_user:
        # Update OAuth info if user exists but doesn't have OAuth linked
        if user_data.google_id and not existing_user.google_id:
            existing_user.google_id = user_data.google_id
            existing_user.oauth_provider = user_data.oauth_provider
        elif user_data.facebook_id and not existing_user.facebook_id:
            existing_user.facebook_id = user_data.facebook_id
            existing_user.oauth_provider = user_data.oauth_provider
        
        db.commit()
        return existing_user
    
    # Create new OAuth user
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        profile_picture=user_data.profile_picture,
        google_id=user_data.google_id,
        facebook_id=user_data.facebook_id,
        oauth_provider=user_data.oauth_provider
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log OAuth registration
    await log_user_activity(
        user_id=new_user.id,
        activity_type="oauth_registration",
        description=f"User registered via {user_data.oauth_provider}",
        request=request,
        db=db
    )
    
    return new_user

@auth_router.post("/oauth/login", response_model=Token)
async def oauth_login(
    user_data: OAuthUserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login user via OAuth (Google/Facebook)"""
    
    # Check if user exists by email or OAuth ID
    user = db.query(User).filter(
        (User.email == user_data.email) | 
        (User.google_id == user_data.google_id) if user_data.google_id else False |
        (User.facebook_id == user_data.facebook_id) if user_data.facebook_id else False
    ).first()
    
    if not user:
        # Auto-register new OAuth user
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            profile_picture=user_data.profile_picture,
            google_id=user_data.google_id,
            facebook_id=user_data.facebook_id,
            oauth_provider=user_data.oauth_provider
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Log OAuth registration
        await log_user_activity(
            user_id=user.id,
            activity_type="oauth_registration",
            description=f"User auto-registered via {user_data.oauth_provider}",
            request=request,
            db=db
        )
    else:
        # Update OAuth info if needed
        updated = False
        if user_data.google_id and not user.google_id:
            user.google_id = user_data.google_id
            user.oauth_provider = user_data.oauth_provider
            updated = True
        elif user_data.facebook_id and not user.facebook_id:
            user.facebook_id = user_data.facebook_id
            user.oauth_provider = user_data.oauth_provider
            updated = True
        
        if updated:
            db.commit()
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Log OAuth login
    await log_user_activity(
        user_id=user.id,
        activity_type="oauth_login",
        description=f"User logged in via {user_data.oauth_provider}",
        request=request,
        db=db
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@auth_router.post("/password/reset")
async def request_password_reset(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    
    user = db.query(User).filter(User.email == reset_data.email).first()
    
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Generate reset token
    reset_token = generate_reset_token()
    expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
    
    # Save reset token
    token_record = PasswordResetToken(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at
    )
    
    db.add(token_record)
    db.commit()
    
    # TODO: Send email with reset link
    # For now, we'll just return the token (remove this in production)
    print(f"Password reset token for {user.email}: {reset_token}")
    
    return {"message": "If the email exists, a reset link has been sent"}

@auth_router.post("/password/reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token"""
    
    # Find valid token
    token_record = db.query(PasswordResetToken).filter(
        and_(
            PasswordResetToken.token == reset_data.token,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        )
    ).first()
    
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update user password
    user = db.query(User).filter(User.id == token_record.user_id).first()
    user.hashed_password = get_password_hash(reset_data.new_password)
    
    # Mark token as used
    token_record.is_used = True
    
    db.commit()
    
    # Log password reset
    await log_user_activity(
        user_id=user.id,
        activity_type="password_reset",
        description="Password reset via email token",
        db=db
    )
    
    return {"message": "Password reset successfully"}

@auth_router.post("/password/change")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    # Log password change
    await log_user_activity(
        user_id=current_user.id,
        activity_type="password_change",
        description="Password changed by user",
        db=db
    )
    
    return {"message": "Password changed successfully"}

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@auth_router.post("/logout")
async def logout_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user (mainly for logging purposes)"""
    
    # Log logout activity
    await log_user_activity(
        user_id=current_user.id,
        activity_type="logout",
        description="User logged out",
        request=request,
        db=db
    )
    
    return {"message": "Logged out successfully"}