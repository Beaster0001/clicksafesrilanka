from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import warnings
import random
import string
import re
import logging
warnings.filterwarnings('ignore')

# Database stuff
from database import database, create_tables
from auth_routes import auth_router
from admin_routes import admin_router, user_router
from dashboard_routes import dashboard_router, scans_router
from cert_routes import router as cert_router
from qr_routes import qr_router  

from simple_detector import simple_predict



# Setup FastAPI
app = FastAPI(
    title="ClickSafe API", 
    description="Multilingual Phishing Detection API with User Management and QR URL Safety Analysis",
    version="2.0.0"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS setup - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://localhost:5177", "http://localhost:5178", "http://localhost:5179", "http://localhost:5180", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add all the routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(user_router)
app.include_router(dashboard_router)
app.include_router(scans_router)
app.include_router(cert_router)
app.include_router(qr_router)  

# Data models for API requests/responses
class MessageRequest(BaseModel):
    message: str

class PredictionResponse(BaseModel):
    text: str
    language: str
    classification: str
    risk_score: float
    suspicious_terms: List[str]
    explanation: str
    is_safe: bool

# Password stuff
class PasswordRequest(BaseModel):
    length: int = 12
    include_uppercase: bool = True
    include_lowercase: bool = True
    include_numbers: bool = True
    include_symbols: bool = True

class PasswordCheckRequest(BaseModel):
    password: str

class PasswordResponse(BaseModel):
    password: str
    strength_score: float
    feedback: str

class PasswordStrengthResponse(BaseModel):
    password: str
    strength_score: float
    strength_level: str
    feedback: str
    suggestions: list

# Database event handlers
@app.on_event("startup")
async def startup():
    """Connect to database and create tables on startup"""
    await database.connect()
    create_tables()
    
    # Create admin user if it doesn't exist
    from init_db import create_admin_user
    create_admin_user()  # This is not async
    print("✅ Simple detector API ready!")

@app.on_event("shutdown")
async def shutdown():
    """Disconnect from database on shutdown"""
    await database.disconnect()

@app.get("/")
async def root():
    return {"message": "ClickSafe Multilingual Phishing Detection API", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "detector": "simple"}

def calculate_password_strength(password):
    """Calculate password strength using multiple criteria"""
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 12:
        score += 25
    elif len(password) >= 8:
        score += 15
        feedback.append("Consider using a longer password (12+ characters)")
    else:
        score += 5
        feedback.append("Password is too short. Use at least 8 characters")
    
    # Character variety checks
    if re.search(r'[A-Z]', password):
        score += 20
    else:
        feedback.append("Add uppercase letters")
    
    if re.search(r'[a-z]', password):
        score += 20
    else:
        feedback.append("Add lowercase letters")
    
    if re.search(r'\d', password):
        score += 20
    else:
        feedback.append("Add numbers")
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 15
    else:
        feedback.append("Add special characters")
    
    # Complexity bonus
    char_types = sum([
        bool(re.search(r'[A-Z]', password)),
        bool(re.search(r'[a-z]', password)),
        bool(re.search(r'\d', password)),
        bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    ])
    
    if char_types >= 4:
        score += 10
    
    # Common patterns penalty
    if re.search(r'(123|abc|password|qwerty)', password.lower()):
        score -= 20
        feedback.append("Avoid common patterns")
    
    return min(100, max(0, score)), feedback

def generate_smart_password(length=12, include_uppercase=True, include_lowercase=True, 
                           include_numbers=True, include_symbols=True):
    """Generate a secure password with specified criteria"""
    chars = ""
    
    if include_lowercase:
        chars += string.ascii_lowercase
    if include_uppercase:
        chars += string.ascii_uppercase
    if include_numbers:
        chars += string.digits
    if include_symbols:
        chars += "!@#$%^&*(),.?\":{}|<>"
    
    if not chars:
        chars = string.ascii_letters + string.digits
    
    # Ensure at least one character from each required type
    password = []
    
    if include_lowercase and string.ascii_lowercase:
        password.append(random.choice(string.ascii_lowercase))
    if include_uppercase and string.ascii_uppercase:
        password.append(random.choice(string.ascii_uppercase))
    if include_numbers and string.digits:
        password.append(random.choice(string.digits))
    if include_symbols:
        password.append(random.choice("!@#$%^&*(),.?\":{}|<>"))
    
    # Fill the rest randomly
    for _ in range(length - len(password)):
        password.append(random.choice(chars))
    
    # Shuffle to avoid predictable patterns
    random.shuffle(password)
    
    return ''.join(password)

def predict_message(message: str) -> dict:
    """Predict if a message is phishing using simple detector - for internal use"""
    try:
        if not message.strip():
            raise ValueError("Message cannot be empty")
        
        # Use simple detector directly
        from simple_detector import simple_predict
        result = simple_predict(message.strip())
        return result
        
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        raise Exception(f"Prediction error: {str(e)}")

@app.post("/predict", response_model=PredictionResponse)
async def predict_message(request: MessageRequest):
    """Predict if a message is phishing using simple detector"""
    try:
        message = request.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Use simple detector
        result = simple_predict(message)
        
        # Convert to response format
        response = PredictionResponse(
            text=message,
            language=result["language"],
            classification=result["classification"],
            risk_score=result["risk_score"],
            suspicious_terms=result["suspicious_terms"],
            explanation=result["explanation"],
            is_safe=result["is_safe"]
        )
        
        return response
        
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/password/generate", response_model=PasswordResponse)
async def generate_password(request: PasswordRequest):
    """Generate a secure password"""
    try:
        print(f"Generating password with settings: {request}")
        
        password = generate_smart_password(
            length=request.length,
            include_uppercase=request.include_uppercase,
            include_lowercase=request.include_lowercase,
            include_numbers=request.include_numbers,
            include_symbols=request.include_symbols
        )
        
        # Calculate strength
        strength_score, feedback = calculate_password_strength(password)
        
        result = PasswordResponse(
            password=password,
            strength_score=strength_score,
            feedback="; ".join(feedback) if feedback else "Strong password!"
        )
        
        print(f"Generated password successfully: {result.password} (score: {result.strength_score})")
        return result
    
    except Exception as e:
        print(f"Error generating password: {e}")
        raise HTTPException(status_code=500, detail=f"Password generation error: {str(e)}")

@app.post("/password/check", response_model=PasswordStrengthResponse)
async def check_password_strength(request: PasswordCheckRequest):
    """Check password strength"""
    try:
        print(f"Checking password strength for: {request.password[:3]}...")
        
        password = request.password
        strength_score, feedback = calculate_password_strength(password)
        
        # Determine strength level
        if strength_score >= 80:
            strength_level = "Very Strong"
        elif strength_score >= 60:
            strength_level = "Strong"
        elif strength_score >= 40:
            strength_level = "Moderate"
        elif strength_score >= 20:
            strength_level = "Weak"
        else:
            strength_level = "Very Weak"
        
        suggestions = [
            "Use at least 12 characters",
            "Include uppercase and lowercase letters",
            "Add numbers and special characters",
            "Avoid common words and patterns",
            "Consider using a passphrase"
        ]
        
        result = PasswordStrengthResponse(
            password=password,
            strength_score=strength_score,
            strength_level=strength_level,
            feedback="; ".join(feedback) if feedback else "Good password!",
            suggestions=suggestions[:3]
        )
        
        print(f"Password strength check complete: {strength_level} ({strength_score}/100)")
        return result
    
    except Exception as e:
        print(f"Error checking password strength: {e}")
        raise HTTPException(status_code=500, detail=f"Password checking error: {str(e)}")

@app.get("/password/health")
async def password_health():
    """Check password service health"""
    return {
        "generator_model_loaded": False,
        "strength_model_loaded": False,
        "status": "healthy",
        "service": "rule-based password manager"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
    
    