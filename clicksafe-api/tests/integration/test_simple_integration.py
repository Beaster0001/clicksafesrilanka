#!/usr/bin/env python3
"""
Simple Integration Tests
Basic tests that don't rely on problematic modules
"""
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test simple imports and functions
from database import get_db, Base
from models import User, UserScan, RecentScam
import simple_detector
import auth

class TestSimpleIntegration(unittest.TestCase):
    """Test basic module integration without FastAPI complexity"""
    
    def test_database_import(self):
        """Test that database module imports correctly"""
        self.assertIsNotNone(get_db)
        self.assertIsNotNone(Base)
    
    def test_models_import(self):
        """Test that models import correctly"""
        self.assertIsNotNone(User)
        self.assertIsNotNone(UserScan)
        self.assertIsNotNone(RecentScam)
    
    def test_simple_detector_import(self):
        """Test that simple_detector module imports"""
        self.assertIsNotNone(simple_detector)
        self.assertTrue(hasattr(simple_detector, 'simple_predict'))
    
    def test_auth_import(self):
        """Test that auth module imports"""
        self.assertIsNotNone(auth)
        self.assertTrue(hasattr(auth, 'get_password_hash'))
        self.assertTrue(hasattr(auth, 'verify_password'))
    
    def test_simple_detector_functionality(self):
        """Test basic simple_detector functionality"""
        test_message = "Hello, this is a test message"
        result = simple_detector.simple_predict(test_message)
        
        # Check that result has expected structure
        self.assertIsInstance(result, dict)
        self.assertIn('classification', result)
        self.assertIn('risk_score', result)
        self.assertIn('language', result)
    
    def test_auth_functionality(self):
        """Test basic auth functionality"""
        test_password = "TestPassword123!"
        hashed = auth.get_password_hash(test_password)
        
        # Check password hashing works
        self.assertIsInstance(hashed, str)
        self.assertNotEqual(hashed, test_password)
        
        # Check password verification works
        self.assertTrue(auth.verify_password(test_password, hashed))
        self.assertFalse(auth.verify_password("WrongPassword", hashed))

class TestSchemaValidation(unittest.TestCase):
    """Test schema validation without FastAPI"""
    
    def test_user_model_creation(self):
        """Test creating User model instance"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "hashed_password": "hashedpassword123"
        }
        
        user = User(**user_data)
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.full_name, "Test User")
    
    def test_user_scan_model_creation(self):
        """Test creating UserScan model instance"""
        scan_data = {
            "user_id": 1,
            "scan_type": "message",
            "content": "Test content",
            "classification": "safe",
            "risk_score": 0.1,
            "language": "english"
        }
        
        scan = UserScan(**scan_data)
        self.assertEqual(scan.user_id, 1)
        self.assertEqual(scan.scan_type, "message")
        self.assertEqual(scan.content, "Test content")
        self.assertEqual(scan.classification, "safe")

if __name__ == '__main__':
    unittest.main()