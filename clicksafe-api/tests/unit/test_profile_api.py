"""
Minimal FastAPI app for testing Profile and Settings pages
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json

app = FastAPI(title="ClickSafe API - Minimal Test", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock user data
mock_user = {
    "id": 1,
    "email": "user@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "phone": "+94 77 123 4567",
    "location": "Colombo, Sri Lanka",
    "bio": "Software developer passionate about cybersecurity",
    "website": "https://example.com",
    "is_admin": False,
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z"
}

mock_stats = {
    "total_scans": 125,
    "threats_detected": 15,
    "safe_scans": 110,
    "cert_reports": 3
}

mock_activities = [
    {
        "id": 1,
        "activity_type": "scan",
        "description": "Scanned suspicious email",
        "created_at": "2024-01-15T14:30:00Z"
    },
    {
        "id": 2,
        "activity_type": "login",
        "description": "User logged in",
        "created_at": "2024-01-15T10:30:00Z"
    },
    {
        "id": 3,
        "activity_type": "cert_report",
        "description": "Reported phishing attempt to CERT",
        "created_at": "2024-01-14T16:45:00Z"
    }
]

# Auth dependency (mock)
def get_current_user():
    return mock_user

@app.get("/")
def read_root():
    return {"message": "ClickSafe API - Profile & Settings Test"}

@app.get("/auth/me")
def get_current_user_info():
    return mock_user

@app.post("/auth/login")
def login(credentials: dict):
    return {
        "access_token": "mock_token_12345",
        "token_type": "bearer",
        "user": mock_user
    }

@app.post("/auth/register")  
def register(user_data: dict):
    return {
        "access_token": "mock_token_12345",
        "token_type": "bearer", 
        "user": mock_user
    }

@app.get("/users/profile")
def get_user_profile():
    return mock_user

@app.patch("/users/profile")
def update_user_profile(profile_data: dict):
    # Update mock user data
    for key, value in profile_data.items():
        if key in mock_user:
            mock_user[key] = value
    return mock_user

@app.get("/users/activities")
def get_user_activities(limit: int = 50):
    return mock_activities[:limit]

@app.post("/users/change-password")
def change_password(password_data: dict):
    return {"message": "Password changed successfully"}

@app.delete("/users/account")
def delete_account():
    return {"message": "Account deleted successfully"}

@app.get("/users/export-data")
def export_data():
    return {
        "user_profile": mock_user,
        "activities": mock_activities,
        "scans": []
    }

@app.get("/users/settings")
def get_settings():
    return {
        "theme": "system",
        "language": "en",
        "notifications": {
            "email": True,
            "push": True,
            "security_alerts": True
        }
    }

@app.patch("/users/settings")
def update_settings(settings_data: dict):
    return {"message": "Settings updated successfully", "settings": settings_data}

@app.get("/dashboard/stats")
def get_dashboard_stats():
    return {"stats": mock_stats}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)