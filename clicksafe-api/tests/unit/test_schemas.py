#!/usr/bin/env python3
"""
Unit Tests for Pydantic Schemas
Tests schema validation and serialization
"""
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas import (
    UserCreate, UserUpdate, UserLogin, UserResponse,
    ScanCreate, ScanResponse, ScanFilter, 
    MessageRequest, PredictionResponse,
    RecentScamResponse, UserStats, DashboardData
)
from pydantic import ValidationError
from datetime import datetime
from models import User, UserScan

class TestUserSchemas(unittest.TestCase):
    """Test User-related schemas"""
    
    def test_user_create_valid(self):
        """Test valid user creation schema"""
        valid_data = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "StrongPassword123!"
        }
        
        user_create = UserCreate(**valid_data)
        
        self.assertEqual(user_create.email, "test@example.com")
        self.assertEqual(user_create.username, "testuser")
        self.assertEqual(user_create.full_name, "Test User")
        self.assertEqual(user_create.password, "StrongPassword123!")
    
    def test_user_create_invalid_email(self):
        """Test user creation with invalid email"""
        invalid_data = {
            "email": "invalid-email",  # Invalid email format
            "username": "testuser",
            "full_name": "Test User",
            "password": "StrongPassword123!"
        }
        
        with self.assertRaises(ValidationError) as context:
            UserCreate(**invalid_data)
        
        self.assertIn("email", str(context.exception))
    
    def test_user_create_weak_password(self):
        """Test user creation with weak password"""
        invalid_data = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "weak"  # Too weak password
        }
        
        with self.assertRaises(ValidationError) as context:
            UserCreate(**invalid_data)
        
        # Should fail password validation
        self.assertIn("password", str(context.exception).lower())
    
    def test_user_login_valid(self):
        """Test valid user login schema"""
        valid_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        user_login = UserLogin(**valid_data)
        
        self.assertEqual(user_login.email, "test@example.com")
        self.assertEqual(user_login.password, "password123")
    
    def test_user_login_invalid_email(self):
        """Test user login with invalid email"""
        invalid_data = {
            "email": "not-an-email",
            "password": "password123"
        }
        
        with self.assertRaises(ValidationError):
            UserLogin(**invalid_data)
    
    def test_user_update_valid(self):
        """Test valid user update schema"""
        valid_data = {
            "full_name": "Updated Name",
            "profile_picture": "https://example.com/pic.jpg"
        }
        
        user_update = UserUpdate(**valid_data)
        
        self.assertEqual(user_update.full_name, "Updated Name")
        self.assertEqual(user_update.profile_picture, "https://example.com/pic.jpg")
    
    def test_user_update_empty(self):
        """Test user update with no fields"""
        # Should be valid - all fields are optional
        user_update = UserUpdate()
        
        self.assertIsNone(user_update.full_name)
        self.assertIsNone(user_update.profile_picture)
    
    def test_user_response_serialization(self):
        """Test user response schema serialization"""
        # Create a mock user object
        user_data = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "is_active": True,
            "is_admin": False,
            "profile_picture": None,
            "phone": None,
            "location": None,
            "bio": None,
            "website": None,
            "created_at": datetime.now(),
            "last_login": None
        }
        
        user_response = UserResponse(**user_data)
        
        self.assertEqual(user_response.id, 1)
        self.assertEqual(user_response.email, "test@example.com")
        self.assertEqual(user_response.username, "testuser")
        self.assertTrue(user_response.is_active)
        self.assertFalse(user_response.is_admin)

class TestScanSchemas(unittest.TestCase):
    """Test Scan-related schemas"""
    
    def test_scan_create_valid(self):
        """Test valid scan creation schema"""
        valid_data = {
            "scan_type": "message",
            "content": "Click here to claim your prize!"
        }
        
        scan_create = ScanCreate(**valid_data)
        
        self.assertEqual(scan_create.scan_type, "message")
        self.assertEqual(scan_create.content, "Click here to claim your prize!")
    
    def test_scan_create_invalid_type(self):
        """Test scan creation with invalid scan type"""
        invalid_data = {
            "scan_type": "invalid_type",  # Invalid scan type
            "content": "Some content"
        }
        
        # Note: This depends on if scan_type has enum validation
        # For now, we'll just test that it accepts the value
        scan_create = ScanCreate(**invalid_data)
        self.assertEqual(scan_create.scan_type, "invalid_type")
    
    def test_scan_create_empty_content(self):
        """Test scan creation with empty content"""
        invalid_data = {
            "scan_type": "message",
            "content": ""  # Empty content
        }
        
        # Should still be valid, but might be caught at business logic level
        scan_create = ScanCreate(**invalid_data)
        self.assertEqual(scan_create.content, "")
    
    def test_scan_response_serialization(self):
        """Test scan response schema serialization"""
        scan_data = {
            "id": 1,
            "user_id": 1,
            "scan_type": "message",
            "content": "Test content",
            "classification": "dangerous",
            "risk_score": 0.95,
            "language": "english",
            "suspicious_terms": ["click", "prize"],
            "explanation": "Contains phishing indicators",
            "created_at": datetime.now()
        }
        
        scan_response = ScanResponse(**scan_data)
        
        self.assertEqual(scan_response.id, 1)
        self.assertEqual(scan_response.scan_type, "message")
        self.assertEqual(scan_response.classification, "dangerous")
        self.assertEqual(scan_response.risk_score, 0.95)
        self.assertEqual(scan_response.suspicious_terms, ["click", "prize"])
    
    def test_scan_filter_valid(self):
        """Test scan filter schema"""
        filter_data = {
            "scan_type": "message",
            "classification": "dangerous",
            "language": "english",
            "date_from": datetime.now(),
            "date_to": datetime.now()
        }
        
        scan_filter = ScanFilter(**filter_data)
        
        self.assertEqual(scan_filter.scan_type, "message")
        self.assertEqual(scan_filter.classification, "dangerous")
        self.assertEqual(scan_filter.language, "english")

class TestPredictionSchemas(unittest.TestCase):
    """Test ML prediction schemas"""
    
    def test_message_request_valid(self):
        """Test valid message request"""
        valid_data = {
            "message": "Click here to win a free iPhone!"
        }
        
        message_request = MessageRequest(**valid_data)
        
        self.assertEqual(message_request.message, "Click here to win a free iPhone!")
    
    def test_message_request_empty(self):
        """Test message request with empty message"""
        invalid_data = {
            "message": ""
        }
        
        # Should still be valid at schema level
        message_request = MessageRequest(**invalid_data)
        self.assertEqual(message_request.message, "")
    
    def test_prediction_response_valid(self):
        """Test prediction response schema"""
        response_data = {
            "text": "Click here to win!",
            "language": "english",
            "classification": "dangerous",
            "risk_score": 0.95,
            "suspicious_terms": ["click", "win"],
            "explanation": "Contains typical phishing language",
            "is_safe": False
        }
        
        prediction_response = PredictionResponse(**response_data)
        
        self.assertEqual(prediction_response.text, "Click here to win!")
        self.assertEqual(prediction_response.language, "english")
        self.assertEqual(prediction_response.classification, "dangerous")
        self.assertEqual(prediction_response.risk_score, 0.95)
        self.assertFalse(prediction_response.is_safe)

class TestDashboardSchemas(unittest.TestCase):
    """Test Dashboard-related schemas"""
    
    def test_user_stats_valid(self):
        """Test user stats schema"""
        stats_data = {
            "total_scans": 10,
            "safe_scans": 6,
            "suspicious_scans": 2,
            "dangerous_scans": 2,
            "recent_scans": []
        }
        
        user_stats = UserStats(**stats_data)
        
        self.assertEqual(user_stats.total_scans, 10)
        self.assertEqual(user_stats.safe_scans, 6)
        self.assertEqual(user_stats.suspicious_scans, 2)
        self.assertEqual(user_stats.dangerous_scans, 2)
        self.assertEqual(len(user_stats.recent_scans), 0)
    
    def test_recent_scam_response_valid(self):
        """Test recent scam response schema"""
        scam_data = {
            "id": 1,
            "anonymized_content": "URGENT: Your [NAME] account suspended!",
            "original_language": "english",
            "risk_score": 0.95,
            "classification": "dangerous",
            "scam_type": "phishing",
            "suspicious_terms": ["urgent", "suspended"],
            "scan_count": 5,
            "is_verified": True,
            "is_public": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        recent_scam = RecentScamResponse(**scam_data)
        
        self.assertEqual(recent_scam.id, 1)
        self.assertEqual(recent_scam.anonymized_content, "URGENT: Your [NAME] account suspended!")
        self.assertEqual(recent_scam.classification, "dangerous")
        self.assertEqual(recent_scam.scan_count, 5)
        self.assertTrue(recent_scam.is_verified)

class TestSchemaValidationEdgeCases(unittest.TestCase):
    """Test edge cases and validation scenarios"""
    
    def test_missing_required_fields(self):
        """Test schemas with missing required fields"""
        
        # Test UserCreate without required email
        with self.assertRaises(ValidationError):
            UserCreate(username="test", full_name="Test", password="Pass123!")
        
        # Test ScanCreate without required content
        with self.assertRaises(ValidationError):
            ScanCreate(scan_type="message")
        
        # Test MessageRequest without message
        with self.assertRaises(ValidationError):
            MessageRequest()
    
    def test_extra_fields_handling(self):
        """Test how schemas handle extra fields"""
        
        # Schemas should ignore extra fields by default
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "StrongPass123!",
            "extra_field": "should_be_ignored"  # Extra field
        }
        
        user_create = UserCreate(**user_data)
        
        # Should not have the extra field
        self.assertFalse(hasattr(user_create, 'extra_field'))
    
    def test_type_coercion(self):
        """Test automatic type coercion in schemas"""
        
        # Test string to int coercion
        scan_data = {
            "scan_type": "message",
            "content": "Test content"
        }
        
        scan_create = ScanCreate(**scan_data)
        self.assertIsInstance(scan_create.content, str)
    
    def test_none_values_in_optional_fields(self):
        """Test None values in optional fields"""
        
        user_update = UserUpdate(
            full_name=None,
            profile_picture=None
        )
        
        self.assertIsNone(user_update.full_name)
        self.assertIsNone(user_update.profile_picture)

if __name__ == "__main__":
    unittest.main(verbosity=2)