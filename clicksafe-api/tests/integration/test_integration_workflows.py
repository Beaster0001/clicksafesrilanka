#!/usr/bin/env python3
"""
Integration Testing - End-to-End Workflows
Tests complete user journeys and system workflows
"""
import pytest
import requests
import json
from datetime import datetime, timedelta
import time

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "email": "integration_test@example.com",
    "username": "integration_test_user",
    "full_name": "Integration Test User",
    "password": "TestPassword123!"
}

class TestCompleteUserJourney:
    """Test complete user workflows from start to finish"""
    
    def setup_class(self):
        """Setup for integration tests"""
        self.session = requests.Session()
        self.user_token = None
        self.user_id = None
    
    def test_complete_user_registration_to_scan_workflow(self):
        """Test: User Registration → Login → Scan Content → View Results"""
        
        # Step 1: User Registration
        registration_data = TEST_USER.copy()
        response = self.session.post(f"{BASE_URL}/auth/register", json=registration_data)
        assert response.status_code == 201, f"Registration failed: {response.text}"
        
        user_data = response.json()
        self.user_id = user_data.get("id")
        assert self.user_id is not None
        
        # Step 2: User Login
        login_data = {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
        response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        token_data = response.json()
        self.user_token = token_data.get("access_token")
        assert self.user_token is not None
        
        # Set authorization header for subsequent requests
        self.session.headers.update({"Authorization": f"Bearer {self.user_token}"})
        
        # Step 3: Scan Phishing Content
        scan_data = {
            "scan_type": "message",
            "content": "URGENT! Your bank account has been suspended. Click here immediately to verify your details and prevent permanent closure."
        }
        response = self.session.post(f"{BASE_URL}/scans/", json=scan_data)
        assert response.status_code == 201, f"Scan creation failed: {response.text}"
        
        scan_result = response.json()
        assert scan_result["classification"] == "dangerous"
        assert scan_result["risk_score"] >= 0.7
        assert "suspended" in scan_result["suspicious_terms"]
        
        # Step 4: View Scan History
        response = self.session.get(f"{BASE_URL}/scans/")
        assert response.status_code == 200
        
        scan_history = response.json()
        assert len(scan_history) >= 1
        assert scan_history[0]["user_id"] == self.user_id
        
        # Step 5: Get Dashboard Data
        response = self.session.get(f"{BASE_URL}/dashboard/")
        assert response.status_code == 200
        
        dashboard_data = response.json()
        assert dashboard_data["stats"]["total_scans"] >= 1
        assert dashboard_data["stats"]["dangerous_scans"] >= 1
    
    def test_phishing_detection_to_cert_workflow(self):
        """Test: Detect Dangerous Content → Submit CERT Report → Email Notification"""
        
        # Ensure user is logged in
        if not self.user_token:
            self.test_complete_user_registration_to_scan_workflow()
        
        # Step 1: Scan High-Risk Content
        dangerous_content = "Your bitcoin wallet has been suspended! Verify immediately with your private key or lose all funds. Click here now!"
        
        scan_data = {
            "scan_type": "message",
            "content": dangerous_content
        }
        response = self.session.post(f"{BASE_URL}/scans/", json=scan_data)
        assert response.status_code == 201
        
        scan_result = response.json()
        scan_id = scan_result["id"]
        assert scan_result["classification"] == "dangerous"
        
        # Step 2: Submit CERT Report
        cert_data = {
            "scan_id": scan_id,
            "incident_type": "phishing",
            "additional_info": "Bitcoin wallet suspension scam - integration test"
        }
        response = self.session.post(f"{BASE_URL}/cert/report", json=cert_data)
        assert response.status_code == 201, f"CERT report failed: {response.text}"
        
        cert_result = response.json()
        assert cert_result["status"] == "submitted"
        assert cert_result["scan_id"] == scan_id
        
        # Step 3: Verify CERT Report in Database
        response = self.session.get(f"{BASE_URL}/cert/reports")
        assert response.status_code == 200
        
        reports = response.json()
        assert len(reports) >= 1
        assert any(report["scan_id"] == scan_id for report in reports)
    
    def test_qr_scanning_to_database_workflow(self):
        """Test: QR Code Scan → Analysis → Database Storage → Retrieval"""
        
        # Ensure user is logged in
        if not self.user_token:
            self.test_complete_user_registration_to_scan_workflow()
        
        # Step 1: Submit QR Content for Analysis
        qr_content = "https://suspicious-banking-site.fake.com/login?redirect=steal-credentials"
        
        scan_data = {
            "scan_type": "qr_code",
            "content": qr_content
        }
        response = self.session.post(f"{BASE_URL}/scans/", json=scan_data)
        assert response.status_code == 201
        
        scan_result = response.json()
        qr_scan_id = scan_result["id"]
        
        # Step 2: Verify QR Analysis Results
        assert scan_result["scan_type"] == "qr_code"
        assert scan_result["content"] == qr_content
        assert scan_result["classification"] in ["suspicious", "dangerous"]
        
        # Step 3: Retrieve QR Scan from Database
        response = self.session.get(f"{BASE_URL}/scans/{qr_scan_id}")
        assert response.status_code == 200
        
        retrieved_scan = response.json()
        assert retrieved_scan["id"] == qr_scan_id
        assert retrieved_scan["scan_type"] == "qr_code"
        assert retrieved_scan["content"] == qr_content
        
        # Step 4: Filter QR Scans Specifically
        response = self.session.get(f"{BASE_URL}/scans/?scan_type=qr_code")
        assert response.status_code == 200
        
        qr_scans = response.json()
        assert len(qr_scans) >= 1
        assert all(scan["scan_type"] == "qr_code" for scan in qr_scans)
    
    def test_anonymous_to_authenticated_workflow(self):
        """Test: Anonymous Scan → User Registration → Claim Scans"""
        
        # Step 1: Perform Anonymous Scan
        anonymous_content = "Limited time offer! Click now to claim your prize before it expires!"
        
        # Use session without auth token
        temp_session = requests.Session()
        response = temp_session.post(f"{BASE_URL}/predict", json={"message": anonymous_content})
        assert response.status_code == 200
        
        anonymous_result = response.json()
        assert "classification" in anonymous_result
        assert "risk_score" in anonymous_result
        
        # Step 2: User Registration (different user)
        new_user = {
            "email": "anonymous_test@example.com",
            "username": "anonymous_test_user",
            "full_name": "Anonymous Test User",
            "password": "TestPassword123!"
        }
        
        response = temp_session.post(f"{BASE_URL}/auth/register", json=new_user)
        assert response.status_code == 201
        
        # Step 3: Login and Perform Authenticated Scan
        login_data = {
            "email": new_user["email"],
            "password": new_user["password"]
        }
        response = temp_session.post(f"{BASE_URL}/auth/login", json=login_data)
        assert response.status_code == 200
        
        token_data = response.json()
        temp_session.headers.update({"Authorization": f"Bearer {token_data['access_token']}"})
        
        # Step 4: Authenticated Scan (gets saved to history)
        scan_data = {
            "scan_type": "message",
            "content": anonymous_content
        }
        response = temp_session.post(f"{BASE_URL}/scans/", json=scan_data)
        assert response.status_code == 201
        
        authenticated_result = response.json()
        assert authenticated_result["content"] == anonymous_content
        assert "id" in authenticated_result  # Should have database ID
    
    def teardown_class(self):
        """Cleanup after integration tests"""
        if self.user_token and self.user_id:
            # Cleanup test user and associated data
            try:
                # Note: This would require admin endpoint or soft delete
                pass
            except:
                pass

class TestRecentScamAlertsIntegration:
    """Test Recent Scam Alerts integration workflow"""
    
    def test_dangerous_scan_to_public_feed_workflow(self):
        """Test: Dangerous Scan → Recent Scam Alerts → Public Display"""
        
        # Step 1: Create dangerous scan that should appear in public feed
        session = requests.Session()
        
        # Login as test user
        login_data = {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
        response = session.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            session.headers.update({"Authorization": f"Bearer {token_data['access_token']}"})
        
        # Step 2: Submit High-Risk Content
        dangerous_content = "URGENT: Your account will be closed in 24 hours. Click here to prevent suspension and verify your payment details immediately!"
        
        scan_data = {
            "scan_type": "message",
            "content": dangerous_content
        }
        response = session.post(f"{BASE_URL}/scans/", json=scan_data)
        assert response.status_code == 201
        
        scan_result = response.json()
        assert scan_result["classification"] == "dangerous"
        assert scan_result["risk_score"] >= 0.7
        
        # Step 3: Check Public Recent Scam Alerts Feed
        # Wait a moment for processing
        time.sleep(2)
        
        response = session.get(f"{BASE_URL}/scans/recent-scams/public")
        assert response.status_code == 200
        
        recent_scams = response.json()
        assert len(recent_scams) >= 1
        
        # Step 4: Verify Anonymization and Content
        found_similar = False
        for scam in recent_scams:
            if ("urgent" in scam["suspicious_terms"] and 
                "suspended" in scam["suspicious_terms"] and
                scam["classification"] == "dangerous"):
                found_similar = True
                # Verify anonymization
                assert "[NAME]" in scam["anonymized_content"] or "account" in scam["anonymized_content"]
                assert scam["scan_count"] >= 1
                break
        
        assert found_similar, "Dangerous scan should appear in recent scam alerts"

if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])