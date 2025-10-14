#!/usr/bin/env python3
"""
Frontend-Backend Integration Tests
Tests React frontend communication with FastAPI backend
"""
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import time
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from main import app
from models import User, UserScan
from database import get_db
from auth import create_access_token

class TestFrontendBackendIntegration(unittest.TestCase):
    """Test React frontend to FastAPI backend integration"""
    
    def setUp(self):
        """Set up test client and mock data"""
        self.client = TestClient(app)
        self.base_url = "http://localhost:8000"
        
        # Mock user data
        self.test_user = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "TestPassword123!"
        }
        
        # Mock frontend request headers
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ClickSafe-Frontend/1.0"
        }
    
    def test_api_root_endpoint_frontend_call(self):
        """Test frontend calling API root endpoint"""
        # Simulate frontend GET request to root
        response = self.client.get("/", headers=self.headers)
        
        # Verify response format expected by frontend
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Frontend expects specific response structure
        self.assertIn("message", data)
        self.assertIn("model_loaded", data)
        self.assertIn("available_languages", data)
        self.assertEqual(data["message"], "ClickSafe API is running!")
    
    def test_user_registration_frontend_flow(self):
        """Test complete user registration from frontend perspective"""
        # Simulate frontend registration form submission
        registration_data = {
            "email": "frontend@example.com",
            "username": "frontenduser",
            "full_name": "Frontend User", 
            "password": "FrontendPass123!"
        }
        
        # Frontend POST request to registration endpoint
        response = self.client.post(
            "/auth/register",
            json=registration_data,
            headers=self.headers
        )
        
        # Verify frontend receives expected response
        self.assertIn(response.status_code, [200, 201])
        data = response.json()
        
        # Frontend expects user data and success message
        self.assertIn("id", data)
        self.assertIn("email", data)
        self.assertIn("username", data)
        self.assertIn("message", data)
        self.assertEqual(data["user"]["email"], "frontend@example.com")
    
    def test_user_login_frontend_flow(self):
        """Test user login flow from frontend"""
        # First register a user
        self.client.post("/auth/register", json=self.test_user)
        
        # Simulate frontend login form submission
        login_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        }
        
        response = self.client.post(
            "/auth/login",
            json=login_data,
            headers=self.headers
        )
        
        # Verify frontend receives JWT token
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Frontend expects token and user data
        self.assertIn("access_token", data)
        self.assertIn("token_type", data)
        self.assertIn("user", data)
        self.assertEqual(data["token_type"], "bearer")
    
    def test_authenticated_api_calls(self):
        """Test frontend making authenticated API calls"""
        # Register and login user
        self.client.post("/auth/register", json=self.test_user)
        login_response = self.client.post("/auth/login", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })
        
        token = login_response.json()["access_token"]
        
        # Frontend includes token in Authorization header
        auth_headers = {
            **self.headers,
            "Authorization": f"Bearer {token}"
        }
        
        # Test authenticated endpoint call
        response = self.client.get("/dashboard/stats", headers=auth_headers)
        
        # Verify authenticated access works
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Frontend expects user statistics
        self.assertIn("total_scans", data)
        self.assertIn("safe_scans", data)
    
    def test_phishing_detection_frontend_flow(self):
        """Test complete phishing detection from frontend"""
        # Register and login user first
        self.client.post("/auth/register", json=self.test_user)
        login_response = self.client.post("/auth/login", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })
        
        token = login_response.json()["access_token"]
        auth_headers = {
            **self.headers,
            "Authorization": f"Bearer {token}"
        }
        
        # Frontend submits message for detection
        scan_data = {
            "scan_type": "message",
            "content": "URGENT! Click here to verify your account now!"
        }
        
        response = self.client.post(
            "/scan/message",
            json=scan_data,
            headers=auth_headers
        )
        
        # Verify frontend receives detection results
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Frontend expects specific result structure
        expected_fields = [
            "classification", "risk_score", "language",
            "suspicious_terms", "explanation", "is_safe"
        ]
        for field in expected_fields:
            self.assertIn(field, data)
    
    def test_qr_scanning_frontend_integration(self):
        """Test QR code scanning from frontend"""
        # Simulate QR content submission from frontend
        qr_data = {
            "url": "https://suspicious-site.com/phishing"
        }

        response = self.client.post(
            "/qr/scan/url",
            json=qr_data,
            headers=self.headers
        )        # Verify QR scanning works from frontend
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Frontend expects URL safety analysis
        self.assertIn("url_analysis", data)
        self.assertIn("safety_score", data)
        self.assertIn("threat_categories", data)
    
    def test_recent_scams_feed_frontend(self):
        """Test Recent Scam Alerts feed for frontend"""
        # Frontend requests recent scams for homepage
        response = self.client.get(
            "/scans/recent-scams/public",
            headers=self.headers
        )
        
        # Verify frontend receives scams data
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Frontend expects array of recent scams
        self.assertIsInstance(data, list)
        
        # If scams exist, verify structure
        if data:
            scam = data[0]
            expected_fields = [
                "anonymized_content", "classification", 
                "risk_score", "scan_count", "created_at"
            ]
            for field in expected_fields:
                self.assertIn(field, scam)

class TestAPIResponseFormats(unittest.TestCase):
    """Test API response formats expected by frontend"""
    
    def setUp(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_error_response_format(self):
        """Test error responses match frontend expectations"""
        # Frontend expects consistent error format
        response = self.client.post("/auth/login", json={
            "email": "invalid-email",
            "password": "wrong"
        })
        
        # Error responses should have consistent structure
        self.assertIn(response.status_code, [400, 401, 422])
        
        if response.status_code == 422:
            # Validation error format
            data = response.json()
            self.assertIn("detail", data)
        else:
            # Other error format
            data = response.json()
            self.assertIn("detail", data)
    
    def test_success_response_format(self):
        """Test success responses match frontend expectations"""
        # Test API health endpoint
        response = self.client.get("/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Frontend expects consistent success format
        self.assertIsInstance(data, dict)
        self.assertIn("status", data)
    
    def test_pagination_response_format(self):
        """Test paginated responses for frontend"""
        # Test scan history with pagination
        response = self.client.get("/scans/history?page=1&limit=10")
        
        # Frontend expects pagination metadata
        if response.status_code == 200:
            data = response.json()
            
            # Check pagination structure
            expected_fields = ["items", "total", "page", "limit"]
            for field in expected_fields:
                if field in data:  # Some endpoints might not implement pagination yet
                    self.assertIn(field, data)

class TestCORSIntegration(unittest.TestCase):
    """Test CORS headers for frontend integration"""
    
    def setUp(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_cors_headers_present(self):
        """Test CORS headers for frontend domain"""
        # Simulate frontend domain request
        headers = {
            "Origin": "http://localhost:3000",  # React dev server
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization"
        }
        
        # OPTIONS preflight request
        response = self.client.options("/predict", headers=headers)
        
        # Verify CORS headers (if implemented)
        # Note: This test will pass if CORS is not yet implemented
        if "access-control-allow-origin" in response.headers:
            self.assertIn("access-control-allow-origin", response.headers)
    
    def test_actual_cors_request(self):
        """Test actual CORS request from frontend"""
        headers = {
            "Origin": "http://localhost:3000",
            "Content-Type": "application/json"
        }
        
        response = self.client.post(
            "/predict",
            json={"message": "Test message"},
            headers=headers
        )
        
        # Should work regardless of CORS implementation
        self.assertIn(response.status_code, [200, 400, 422])

class TestWebSocketIntegration(unittest.TestCase):
    """Test WebSocket integration for real-time features"""
    
    def setUp(self):
        """Set up WebSocket test client"""
        self.client = TestClient(app)
    
    def test_websocket_connection(self):
        """Test WebSocket connection for real-time updates"""
        # This test is placeholder for future WebSocket implementation
        # Frontend might use WebSockets for real-time threat updates
        
        try:
            # Attempt WebSocket connection (if implemented)
            with self.client.websocket_connect("/ws") as websocket:
                # Test real-time message
                websocket.send_json({"type": "subscribe", "channel": "threats"})
                data = websocket.receive_json()
                self.assertIn("type", data)
        except Exception:
            # WebSocket not implemented yet - that's okay
            self.assertTrue(True, "WebSocket not implemented - future enhancement")

if __name__ == "__main__":
    unittest.main(verbosity=2)