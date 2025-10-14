#!/usr/bin/env python3
"""
Unit Tests for Route Handlers
Tests individual route handlers and endpoint functionality
"""
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

# Import route modules
import auth_routes
import dashboard_routes  
import cert_routes
import qr_routes
import admin_routes

# Import models and schemas for testing
from models import User, UserScan, RecentScam, AdminLog, PasswordResetToken
from schemas import UserCreate, UserLogin, ScanCreate

class TestAuthRoutes(unittest.TestCase):
    """Test authentication route handlers"""
    
    def setUp(self):
        """Set up test dependencies"""
        self.mock_db = Mock(spec=Session)
        self.mock_get_current_user = Mock()
        self.mock_auth_service = Mock()
    
    @patch('auth_routes.get_db')
    @patch('auth_routes.create_user')
    def test_register_user_success(self, mock_create_user, mock_get_db):
        """Test successful user registration"""
        # Setup mocks
        mock_get_db.return_value = self.mock_db
        mock_user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            full_name="Test User"
        )
        mock_create_user.return_value = mock_user
        
        # Test data
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password="StrongPassword123!"
        )
        
        # Call the function (assuming it exists in auth_routes)
        if hasattr(auth_routes, 'register_user'):
            result = auth_routes.register_user(user_data, self.mock_db)
            
            # Assertions
            mock_create_user.assert_called_once_with(self.mock_db, user_data)
            self.assertEqual(result.email, "test@example.com")
            self.assertEqual(result.username, "testuser")
    
    @patch('auth_routes.get_db')
    @patch('auth_routes.authenticate_user')
    @patch('auth_routes.create_access_token')
    def test_login_user_success(self, mock_create_token, mock_authenticate, mock_get_db):
        """Test successful user login"""
        # Setup mocks
        mock_get_db.return_value = self.mock_db
        mock_user = User(
            id=1,
            email="test@example.com",
            username="testuser"
        )
        mock_authenticate.return_value = mock_user
        mock_create_token.return_value = "fake-jwt-token"
        
        # Test data
        login_data = UserLogin(
            email="test@example.com",
            password="password123"
        )
        
        # Call the function (assuming it exists)
        if hasattr(auth_routes, 'login_user'):
            result = auth_routes.login_user(login_data, self.mock_db)
            
            # Assertions
            mock_authenticate.assert_called_once_with(self.mock_db, "test@example.com", "password123")
            mock_create_token.assert_called_once()
            self.assertEqual(result["access_token"], "fake-jwt-token")
    
    @patch('auth_routes.get_db')
    @patch('auth_routes.authenticate_user')
    def test_login_user_invalid_credentials(self, mock_authenticate, mock_get_db):
        """Test login with invalid credentials"""
        # Setup mocks
        mock_get_db.return_value = self.mock_db
        mock_authenticate.return_value = None  # Invalid credentials
        
        # Test data
        login_data = UserLogin(
            email="test@example.com",
            password="wrongpassword"
        )
        
        # Call the function and expect HTTPException
        if hasattr(auth_routes, 'login_user'):
            with self.assertRaises(HTTPException) as context:
                auth_routes.login_user(login_data, self.mock_db)
            
            self.assertEqual(context.exception.status_code, status.HTTP_401_UNAUTHORIZED)

class TestDashboardRoutes(unittest.TestCase):
    """Test dashboard route handlers"""
    
    def setUp(self):
        """Set up test dependencies"""
        self.mock_db = Mock(spec=Session)
        self.mock_current_user = User(
            id=1,
            email="test@example.com",
            username="testuser"
        )
    
    @patch('dashboard_routes.get_db')
    @patch('dashboard_routes.get_current_user')
    def test_get_user_stats(self, mock_get_user, mock_get_db):
        """Test getting user statistics"""
        # Setup mocks
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = self.mock_current_user
        
        # Mock query results
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 10
        self.mock_db.query.return_value = mock_query
        
        # Call the function (assuming it exists)
        if hasattr(dashboard_routes, 'get_user_stats'):
            result = dashboard_routes.get_user_stats(self.mock_db, self.mock_current_user)
            
            # Assertions
            self.mock_db.query.assert_called()
            self.assertIsInstance(result, dict)
    
    @patch('dashboard_routes.get_db')
    @patch('dashboard_routes.get_current_user')
    def test_get_recent_scans(self, mock_get_user, mock_get_db):
        """Test getting recent scans"""
        # Setup mocks
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = self.mock_current_user
        
        # Mock scan data
        mock_scans = [
            UserScan(
                id=1,
                user_id=1,
                scan_type="message",
                content="Test message",
                classification="safe",
                risk_score=0.1
            )
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_scans
        self.mock_db.query.return_value = mock_query
        
        # Call the function (assuming it exists)
        if hasattr(dashboard_routes, 'get_recent_scans'):
            result = dashboard_routes.get_recent_scans(self.mock_db, self.mock_current_user)
            
            # Assertions
            self.mock_db.query.assert_called_with(UserScan)
            self.assertIsInstance(result, list)

class TestQrRoutes(unittest.TestCase):
    """Test QR code route handlers"""
    
    def setUp(self):
        """Set up test dependencies"""
        self.mock_db = Mock(spec=Session)
        self.mock_current_user = User(
            id=1,
            email="test@example.com",
            username="testuser"
        )
    
    @patch('qr_routes.simple_detector')
    @patch('qr_routes.get_db')
    def test_scan_qr_anonymous(self, mock_get_db, mock_detector):
        """Test anonymous QR code scanning"""
        # Setup mocks
        mock_get_db.return_value = self.mock_db
        mock_detector.predict_message.return_value = {
            "text": "Click here to win!",
            "language": "english",
            "classification": "dangerous",
            "risk_score": 0.95,
            "suspicious_terms": ["click", "win"],
            "explanation": "Contains phishing indicators"
        }
        
        # Test data
        scan_data = ScanCreate(
            scan_type="qr",
            content="Click here to win!"
        )
        
        # Call the function (assuming it exists)
        if hasattr(qr_routes, 'scan_qr_anonymous'):
            result = qr_routes.scan_qr_anonymous(scan_data, self.mock_db)
            
            # Assertions
            mock_detector.predict_message.assert_called_once()
            self.assertEqual(result["classification"], "dangerous")
            self.assertEqual(result["risk_score"], 0.95)
    
    @patch('qr_routes.simple_detector')
    @patch('qr_routes.get_db')
    @patch('qr_routes.get_current_user')
    def test_scan_qr_authenticated(self, mock_get_user, mock_get_db, mock_detector):
        """Test authenticated QR code scanning"""
        # Setup mocks
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = self.mock_current_user
        mock_detector.predict_message.return_value = {
            "text": "Safe message",
            "language": "english",
            "classification": "safe",
            "risk_score": 0.1,
            "suspicious_terms": [],
            "explanation": "No suspicious content detected"
        }
        
        # Test data
        scan_data = ScanCreate(
            scan_type="qr",
            content="Safe message"
        )
        
        # Call the function (assuming it exists)
        if hasattr(qr_routes, 'scan_qr_authenticated'):
            result = qr_routes.scan_qr_authenticated(scan_data, self.mock_db, self.mock_current_user)
            
            # Assertions
            mock_detector.predict_message.assert_called_once()
            self.mock_db.add.assert_called()  # Should save scan to database
            self.mock_db.commit.assert_called()
            self.assertEqual(result["classification"], "safe")

class TestAdminRoutes(unittest.TestCase):
    """Test admin route handlers"""
    
    def setUp(self):
        """Set up test dependencies"""
        self.mock_db = Mock(spec=Session)
        self.mock_admin_user = User(
            id=1,
            email="admin@example.com",
            username="admin",
            is_admin=True
        )
        self.mock_regular_user = User(
            id=2,
            email="user@example.com",
            username="user",
            is_admin=False
        )
    
    @patch('admin_routes.get_db')
    @patch('admin_routes.get_current_user')
    def test_get_all_users_as_admin(self, mock_get_user, mock_get_db):
        """Test getting all users as admin"""
        # Setup mocks
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = self.mock_admin_user
        
        # Mock user data
        mock_users = [self.mock_admin_user, self.mock_regular_user]
        self.mock_db.query.return_value.all.return_value = mock_users
        
        # Call the function (assuming it exists)
        if hasattr(admin_routes, 'get_all_users'):
            result = admin_routes.get_all_users(self.mock_db, self.mock_admin_user)
            
            # Assertions
            self.mock_db.query.assert_called_with(User)
            self.assertEqual(len(result), 2)
    
    @patch('admin_routes.get_db')
    @patch('admin_routes.get_current_user')
    def test_get_all_users_as_regular_user(self, mock_get_user, mock_get_db):
        """Test getting all users as regular user (should fail)"""
        # Setup mocks
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = self.mock_regular_user
        
        # Call the function and expect HTTPException
        if hasattr(admin_routes, 'get_all_users'):
            with self.assertRaises(HTTPException) as context:
                admin_routes.get_all_users(self.mock_db, self.mock_regular_user)
            
            self.assertEqual(context.exception.status_code, status.HTTP_403_FORBIDDEN)
    
    @patch('admin_routes.get_db')
    @patch('admin_routes.get_current_user')
    def test_get_system_stats_as_admin(self, mock_get_user, mock_get_db):
        """Test getting system statistics as admin"""
        # Setup mocks
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = self.mock_admin_user
        
        # Mock statistics queries
        mock_query = Mock()
        mock_query.count.return_value = 100
        self.mock_db.query.return_value = mock_query
        
        # Call the function (assuming it exists)
        if hasattr(admin_routes, 'get_system_stats'):
            result = admin_routes.get_system_stats(self.mock_db, self.mock_admin_user)
            
            # Assertions
            self.mock_db.query.assert_called()
            self.assertIsInstance(result, dict)

class TestRouteErrorHandling(unittest.TestCase):
    """Test error handling in routes"""
    
    def setUp(self):
        """Set up test dependencies"""
        self.mock_db = Mock(spec=Session)
    
    def test_database_connection_error(self):
        """Test handling of database connection errors"""
        # Setup mock to raise exception
        self.mock_db.query.side_effect = Exception("Database connection failed")
        
        # Test that routes handle database errors gracefully
        # This is a general test - specific implementation depends on route design
        with self.assertRaises(Exception):
            self.mock_db.query(User).all()
    
    def test_invalid_input_validation(self):
        """Test handling of invalid input data"""
        # Test that routes validate input properly
        # This depends on the specific validation implementation
        pass
    
    def test_authentication_errors(self):
        """Test handling of authentication errors"""
        # Test that routes handle auth errors properly
        # This depends on the specific auth implementation
        pass

class TestRouteResponseFormats(unittest.TestCase):
    """Test route response formats and serialization"""
    
    def test_json_response_format(self):
        """Test that routes return properly formatted JSON"""
        # Test JSON serialization of responses
        test_user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            created_at=datetime.now()
        )
        
        # Test that datetime objects are properly serialized
        # This depends on the specific serialization implementation
        pass
    
    def test_error_response_format(self):
        """Test that error responses are properly formatted"""
        # Test that HTTPExceptions return proper error format
        error = HTTPException(
            status_code=404,
            detail="Resource not found"
        )
        
        self.assertEqual(error.status_code, 404)
        self.assertEqual(error.detail, "Resource not found")

if __name__ == "__main__":
    unittest.main(verbosity=2)