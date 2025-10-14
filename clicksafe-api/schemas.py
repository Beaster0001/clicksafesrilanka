"""
Pydantic schemas for request/response models
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        from auth import validate_password_strength
        validation = validate_password_strength(v)
        if not validation['is_valid']:
            raise ValueError('; '.join(validation['errors']))
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    is_active: bool
    is_admin: bool
    profile_picture: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    bio: Optional[str]
    website: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenRefresh(BaseModel):
    refresh_token: str

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        from auth import validate_password_strength
        validation = validate_password_strength(v)
        if not validation['is_valid']:
            raise ValueError('; '.join(validation['errors']))
        return v

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        from auth import validate_password_strength
        validation = validate_password_strength(v)
        if not validation['is_valid']:
            raise ValueError('; '.join(validation['errors']))
        return v

# OAuth Schemas
class OAuthUserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    profile_picture: Optional[str] = None
    google_id: Optional[str] = None
    facebook_id: Optional[str] = None
    oauth_provider: str

# Scan Schemas
class ScanCreate(BaseModel):
    scan_type: str  # 'message', 'url', 'qr_code'
    content: str

class ScanResponse(BaseModel):
    id: int
    scan_type: str
    content: str
    classification: str
    risk_score: float
    language: str
    suspicious_terms: Optional[Any]  # Can be Dict, List, or None - flexible for different formats
    explanation: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ScanFilter(BaseModel):
    scan_type: Optional[str] = None
    classification: Optional[str] = None
    language: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 50
    offset: int = 0

# Dashboard Schemas
class UserStats(BaseModel):
    total_scans: int
    safe_scans: int
    suspicious_scans: int
    dangerous_scans: int
    recent_scans: List[ScanResponse]

class DashboardData(BaseModel):
    user: UserResponse
    stats: UserStats
    recent_activities: List[Dict[str, Any]]

# Admin Schemas
class AdminUserList(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    is_active: bool
    scan_count: int
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class AdminUserActivity(BaseModel):
    id: int
    user_id: int
    activity_type: str
    description: Optional[str]
    created_at: datetime
    ip_address: Optional[str]
    
    class Config:
        from_attributes = True

class AdminStats(BaseModel):
    total_users: int
    active_users: int
    total_scans: int
    dangerous_scans_today: int
    recent_activities: List[AdminUserActivity]

# Recent Scams Schemas
class RecentScamResponse(BaseModel):
    id: int
    anonymized_content: str
    original_language: str
    risk_score: float
    classification: str
    scam_type: Optional[str]
    suspicious_terms: Optional[Any]
    scan_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Activity Schemas
class ActivityCreate(BaseModel):
    activity_type: str
    description: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class ActivityResponse(BaseModel):
    id: int
    activity_type: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Message Request (keeping existing)
class MessageRequest(BaseModel):
    message: str

# Prediction Response (keeping existing) 
class PredictionResponse(BaseModel):
    text: str
    language: str
    classification: str
    risk_score: float
    suspicious_terms: Any
    explanation: str
    is_safe: bool

# Recent Scam Response
class RecentScamResponse(BaseModel):
    id: int
    anonymized_content: str
    original_language: str
    risk_score: float
    classification: str
    scam_type: Optional[str]
    suspicious_terms: Optional[List[str]]
    scan_count: int
    is_verified: bool
    is_public: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True