"""
Database models for ClickSafe application
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    """User model for authentication and profile management"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    profile_picture = Column(String(500), nullable=True)
    
    # Additional profile fields
    phone = Column(String(20), nullable=True)
    location = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)
    
    # OAuth fields
    google_id = Column(String(100), unique=True, nullable=True)
    facebook_id = Column(String(100), unique=True, nullable=True)
    oauth_provider = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    scans = relationship("UserScan", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")

class UserScan(Base):
    """Store user's scan history (messages, URLs, QR codes)"""
    __tablename__ = "user_scans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Scan details
    scan_type = Column(String(50), nullable=False)  # 'message', 'url', 'qr_code'
    content = Column(Text, nullable=False)  # The scanned content
    original_content = Column(Text, nullable=True)  # Original unprocessed content
    
    # Analysis results
    classification = Column(String(50), nullable=False)  # 'safe', 'suspicious', 'dangerous'
    risk_score = Column(Float, nullable=False)
    language = Column(String(50), nullable=False)
    suspicious_terms = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=True)
    
    # Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="scans")

class UserActivity(Base):
    """Track user activities for admin monitoring"""
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    activity_type = Column(String(100), nullable=False)  # 'login', 'scan', 'password_change', etc.
    description = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)  # Additional activity details
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="activities")

class AdminLog(Base):
    """Log admin activities"""
    __tablename__ = "admin_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    action = Column(String(100), nullable=False)  # 'delete_user', 'view_activities', etc.
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    description = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    admin_user = relationship("User", foreign_keys=[admin_user_id])
    target_user = relationship("User", foreign_keys=[target_user_id])

class RecentScam(Base):
    """Store recent high-risk scam messages for public display"""
    __tablename__ = "recent_scams"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Anonymized content (remove personal info)
    anonymized_content = Column(Text, nullable=False)
    original_language = Column(String(50), nullable=False)
    risk_score = Column(Float, nullable=False)
    classification = Column(String(50), nullable=False)
    
    # Scam characteristics
    scam_type = Column(String(100), nullable=True)  # 'phishing', 'financial_fraud', etc.
    suspicious_terms = Column(JSON, nullable=True)
    
    # Metadata
    scan_count = Column(Integer, default=1)  # How many times this type was scanned
    is_verified = Column(Boolean, default=False)  # Admin verified as scam
    is_public = Column(Boolean, default=True)  # Show on public feed
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PasswordResetToken(Base):
    """Store password reset tokens"""
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")