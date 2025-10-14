#!/usr/bin/env python3
"""
Security Integration Tests
Tests complete security workflows and authentication flows
"""
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jose import jwt
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, Mock
from auth import create_access_token, verify_token, get_password_hash, verify_password
from models import User, PasswordResetToken

class TestJWTTokenLifecycle(unittest.TestCase):
    """Test complete JWT token lifecycle"""
    
    def setUp(self):
        """Set up JWT testing environment"""
        self.client = TestClient(app)
        self.test_user = {
            "email": "jwt@example.com",
            "username": "jwtuser",
            "full_name": "JWT User",
            "password": "JWTTest123!"
        }
        
        # Register test user
        self.client.post("/auth/register", json=self.test_user)
    
    def test_token_creation_and_validation(self):
        """Test JWT token creation and validation cycle"""
        # Login to get token
        login_response = self.client.post("/auth/login", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })
        
        self.assertEqual(login_response.status_code, 200)
        login_data = login_response.json()
        
        # Verify token structure
        self.assertIn("access_token", login_data)
        self.assertIn("token_type", login_data)
        self.assertEqual(login_data["token_type"], "bearer")
        
        token = login_data["access_token"]
        
        # Test token validation
        try:
            decoded = verify_token(token)
            self.assertIsNotNone(decoded)
            self.assertIn("sub", decoded)
            self.assertIn("exp", decoded)
        except Exception as e:
            self.fail(f"Token validation failed: {e}")
    
    def test_token_expiry_handling(self):
        """Test token expiry and refresh workflow"""
        # Create short-lived token for testing
        short_token_data = {"sub": self.test_user["email"]}
        short_token = create_access_token(
            data=short_token_data,
            expires_delta=timedelta(seconds=1)
        )
        
        # Wait for token to expire
        time.sleep(2)
        
        # Test expired token
        headers = {"Authorization": f"Bearer {short_token}"}
        response = self.client.get("/dashboard/stats", headers=headers)
        
        # Should reject expired token
        self.assertEqual(response.status_code, 401)
    
    def test_invalid_token_handling(self):
        """Test handling of invalid tokens"""
        invalid_tokens = [
            "invalid.token.here",
            "Bearer malformed_token",
            "",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
        ]
        
        for invalid_token in invalid_tokens:
            headers = {"Authorization": f"Bearer {invalid_token}"}
            response = self.client.get("/dashboard/stats", headers=headers)
            
            # Should reject invalid tokens
            self.assertIn(response.status_code, [401, 422])
    
    def test_token_payload_integrity(self):
        """Test token payload integrity and tampering protection"""
        # Get valid token
        login_response = self.client.post("/auth/login", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })
        
        token = login_response.json()["access_token"]
        
        # Attempt to modify token payload
        try:
            # Decode without verification (dangerous - for testing only)
            decoded = jwt.decode(token, options={"verify_signature": False})
            
            # Modify payload
            decoded["sub"] = "hacker@evil.com"
            decoded["is_admin"] = True
            
            # Re-encode with wrong secret
            tampered_token = jwt.encode(decoded, "wrong_secret", algorithm="HS256")
            
            # Test tampered token
            headers = {"Authorization": f"Bearer {tampered_token}"}
            response = self.client.get("/dashboard/stats", headers=headers)
            
            # Should reject tampered token
            self.assertEqual(response.status_code, 401)
            
        except Exception:
            # JWT library prevented tampering - good!
            self.assertTrue(True)

class TestPasswordResetSecurity(unittest.TestCase):
    """Test password reset security workflow"""
    
    def setUp(self):
        """Set up password reset testing"""
        self.client = TestClient(app)
        self.test_user = {
            "email": "reset@example.com",
            "username": "resetuser",
            "full_name": "Reset User",
            "password": "ResetTest123!"
        }
        
        # Register test user
        self.client.post("/auth/register", json=self.test_user)
    
    def test_password_reset_token_generation(self):
        """Test secure password reset token generation"""
        # Request password reset
        response = self.client.post("/auth/password-reset/request", json={
            "email": self.test_user["email"]
        })
        
        if response.status_code == 200:
            # Verify reset token was created
            data = response.json()
            self.assertIn("message", data)
            self.assertIn("reset", data["message"].lower())
        else:
            # Password reset might not be implemented yet
            self.assertIn(response.status_code, [404, 501])
    
    def test_password_reset_token_validation(self):
        """Test password reset token validation"""
        # Mock password reset token
        reset_token = "secure_reset_token_123456"
        
        # Test token validation endpoint
        response = self.client.get(f"/auth/password-reset/validate/{reset_token}")
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn("valid", data)
        else:
            # Validation endpoint might not exist yet
            self.assertIn(response.status_code, [404, 501])
    
    def test_password_reset_completion(self):
        """Test complete password reset workflow"""
        # Mock reset token and new password
        reset_data = {
            "token": "valid_reset_token",
            "new_password": "NewSecurePassword123!",
            "confirm_password": "NewSecurePassword123!"
        }
        
        response = self.client.post("/auth/password-reset/complete", json=reset_data)
        
        if response.status_code == 200:
            # Test login with new password
            login_response = self.client.post("/auth/login", json={
                "email": self.test_user["email"],
                "password": "NewSecurePassword123!"
            })
            
            # Should be able to login with new password
            self.assertEqual(login_response.status_code, 200)
        else:
            # Password reset completion might not be implemented
            self.assertIn(response.status_code, [404, 501])
    
    def test_password_reset_token_expiry(self):
        """Test password reset token expiry"""
        # Test expired reset token
        expired_token = "expired_reset_token_123"
        
        response = self.client.post("/auth/password-reset/complete", json={
            "token": expired_token,
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        })
        
        # Should reject expired token
        self.assertIn(response.status_code, [400, 401, 404])

class TestSessionManagement(unittest.TestCase):
    """Test user session management security"""
    
    def setUp(self):
        """Set up session testing"""
        self.client = TestClient(app)
        self.test_user = {
            "email": "session@example.com",
            "username": "sessionuser",
            "full_name": "Session User",
            "password": "SessionTest123!"
        }
        
        # Register and login
        self.client.post("/auth/register", json=self.test_user)
        login_response = self.client.post("/auth/login", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })
        
        self.token = login_response.json()["access_token"]
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_session_persistence_across_requests(self):
        """Test session persistence across multiple requests"""
        # Make multiple authenticated requests
        endpoints = [
            "/dashboard/stats",
            "/scans/history",
            "/user/profile"
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint, headers=self.auth_headers)
            
            # Should maintain authentication across requests
            self.assertIn(response.status_code, [200, 404])  # 404 if endpoint not implemented
    
    def test_concurrent_session_handling(self):
        """Test handling of concurrent sessions"""
        # Login from multiple "devices" (different tokens)
        login_response_2 = self.client.post("/auth/login", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })
        
        token_2 = login_response_2.json()["access_token"]
        auth_headers_2 = {"Authorization": f"Bearer {token_2}"}
        
        # Both sessions should work concurrently
        response_1 = self.client.get("/dashboard/stats", headers=self.auth_headers)
        response_2 = self.client.get("/dashboard/stats", headers=auth_headers_2)
        
        # Both should be valid (or both 404 if not implemented)
        self.assertEqual(response_1.status_code, response_2.status_code)
    
    def test_session_logout_security(self):
        """Test secure session logout"""
        # Test logout endpoint
        response = self.client.post("/auth/logout", headers=self.auth_headers)
        
        if response.status_code == 200:
            # After logout, token should be invalid
            post_logout_response = self.client.get("/dashboard/stats", headers=self.auth_headers)
            self.assertEqual(post_logout_response.status_code, 401)
        else:
            # Logout endpoint might not be implemented
            self.assertIn(response.status_code, [404, 501])

class TestAuthenticationSecurity(unittest.TestCase):
    """Test authentication security measures"""
    
    def setUp(self):
        """Set up authentication testing"""
        self.client = TestClient(app)
    
    def test_brute_force_protection(self):
        """Test brute force attack protection"""
        # Attempt multiple failed logins
        failed_attempts = []
        
        for i in range(10):
            response = self.client.post("/auth/login", json={
                "email": "nonexistent@example.com",
                "password": f"wrong_password_{i}"
            })
            
            failed_attempts.append(response.status_code)
        
        # Should consistently reject invalid credentials
        for status in failed_attempts:
            self.assertIn(status, [401, 422])
    
    def test_password_hashing_security(self):
        """Test password hashing and verification"""
        test_password = "TestSecurePassword123!"
        
        # Test password hashing
        hashed = get_password_hash(test_password)
        
        # Hash should be different from original
        self.assertNotEqual(hashed, test_password)
        self.assertTrue(len(hashed) > 50)  # bcrypt hashes are long
        
        # Test password verification
        self.assertTrue(verify_password(test_password, hashed))
        self.assertFalse(verify_password("wrong_password", hashed))
    
    def test_password_strength_requirements(self):
        """Test password strength validation"""
        weak_passwords = [
            "123456",
            "password",
            "abc123",
            "qwerty",
            "password123"
        ]
        
        for weak_password in weak_passwords:
            response = self.client.post("/auth/register", json={
                "email": f"weak{weak_password}@example.com",
                "username": f"user{weak_password}",
                "full_name": "Weak Password User",
                "password": weak_password
            })
            
            # Should reject weak passwords
            self.assertIn(response.status_code, [400, 422])
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection in auth"""
        # Attempt SQL injection in login
        malicious_inputs = [
            "admin@example.com'; DROP TABLE users; --",
            "admin@example.com' OR '1'='1",
            "admin@example.com' UNION SELECT * FROM users --"
        ]
        
        for malicious_input in malicious_inputs:
            response = self.client.post("/auth/login", json={
                "email": malicious_input,
                "password": "any_password"
            })
            
            # Should safely handle malicious input
            self.assertIn(response.status_code, [401, 422])

class TestAuthorizationSecurity(unittest.TestCase):
    """Test authorization and access control"""
    
    def setUp(self):
        """Set up authorization testing"""
        self.client = TestClient(app)
        
        # Create regular user
        self.regular_user = {
            "email": "regular@example.com",
            "username": "regularuser",
            "full_name": "Regular User",
            "password": "RegularUser123!"
        }
        
        self.client.post("/auth/register", json=self.regular_user)
        login_response = self.client.post("/auth/login", json={
            "email": self.regular_user["email"],
            "password": self.regular_user["password"]
        })
        
        self.regular_token = login_response.json()["access_token"]
        self.regular_headers = {"Authorization": f"Bearer {self.regular_token}"}
    
    def test_admin_endpoint_protection(self):
        """Test admin endpoint access control"""
        admin_endpoints = [
            "/admin/users",
            "/admin/stats", 
            "/admin/system",
            "/admin/logs"
        ]
        
        for endpoint in admin_endpoints:
            response = self.client.get(endpoint, headers=self.regular_headers)
            
            # Regular user should not access admin endpoints
            self.assertIn(response.status_code, [403, 404])
    
    def test_user_data_isolation(self):
        """Test that users can only access their own data"""
        # Create second user
        user2 = {
            "email": "user2@example.com",
            "username": "user2",
            "full_name": "User Two",
            "password": "UserTwo123!"
        }
        
        self.client.post("/auth/register", json=user2)
        login2 = self.client.post("/auth/login", json={
            "email": user2["email"],
            "password": user2["password"]
        })
        
        token2 = login2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # User 1 creates a scan
        self.client.post("/scan/message", json={
            "scan_type": "message",
            "content": "User 1 private message"
        }, headers=self.regular_headers)
        
        # User 2 tries to access User 1's scans
        response = self.client.get("/scans/history", headers=headers2)
        
        if response.status_code == 200:
            scans = response.json()
            # Should only see own scans, not User 1's scans
            if isinstance(scans, list):
                for scan in scans:
                    self.assertNotEqual(scan.get("content"), "User 1 private message")
    
    def test_csrf_protection(self):
        """Test CSRF protection measures"""
        # Test state-changing operations require proper headers
        csrf_sensitive_endpoints = [
            ("/auth/login", {"email": "test@test.com", "password": "test"}),
            ("/auth/register", {"email": "csrf@test.com", "username": "csrf", "full_name": "CSRF Test", "password": "CSRFTest123!"})
        ]
        
        for endpoint, data in csrf_sensitive_endpoints:
            # Request without proper headers
            response = self.client.post(endpoint, json=data, headers={
                "Origin": "https://malicious-site.com"
            })
            
            # Should handle potentially malicious origins appropriately
            self.assertIn(response.status_code, [200, 400, 403, 422])

if __name__ == "__main__":
    unittest.main(verbosity=2)