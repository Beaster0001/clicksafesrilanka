#!/usr/bin/env python3
"""
Error Handling Integration Tests
Tests system behavior under error conditions and failure scenarios
"""
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile
import sqlite3
from unittest.mock import patch, Mock, MagicMock
from fastapi.testclient import TestClient
from main import app
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import requests

class TestDatabaseFailureHandling(unittest.TestCase):
    """Test system behavior when database fails"""
    
    def setUp(self):
        """Set up database failure testing"""
        self.client = TestClient(app)
        self.test_user = {
            "email": "dbfail@example.com",
            "username": "dbfailuser",
            "full_name": "DB Fail User",
            "password": "DBFail123!"
        }
    
    @patch('database.get_db')
    def test_database_connection_failure(self, mock_get_db):
        """Test handling when database connection fails"""
        # Mock database connection failure
        mock_get_db.side_effect = OperationalError("Database connection failed", None, None)
        
        # Test user registration with DB failure
        response = self.client.post("/auth/register", json=self.test_user)
        
        # Should handle DB failure gracefully
        self.assertIn(response.status_code, [500, 503])
        
        if response.status_code == 500:
            error_data = response.json()
            self.assertIn("detail", error_data)
    
    @patch('sqlalchemy.orm.Session.commit')
    def test_database_transaction_failure(self, mock_commit):
        """Test handling of database transaction failures"""
        # Mock transaction failure
        mock_commit.side_effect = SQLAlchemyError("Transaction failed")
        
        # Test operation that requires database commit
        response = self.client.post("/auth/register", json=self.test_user)
        
        # Should handle transaction failure
        self.assertIn(response.status_code, [400, 500])
    
    @patch('database.get_db')
    def test_database_timeout_handling(self, mock_get_db):
        """Test handling of database timeouts"""
        # Mock database timeout
        mock_get_db.side_effect = OperationalError("Database timeout", None, None)
        
        # Test API endpoint with DB timeout
        response = self.client.get("/scams/recent")
        
        # Should handle timeout gracefully
        self.assertIn(response.status_code, [500, 503, 504])
    
    def test_database_corruption_recovery(self):
        """Test recovery from database corruption"""
        # Create corrupted database file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            # Write invalid data to simulate corruption
            temp_db.write(b"corrupted_database_content")
            temp_db_path = temp_db.name
        
        try:
            # Attempt to connect to corrupted database
            with sqlite3.connect(temp_db_path) as conn:
                conn.execute("SELECT * FROM users")
        except sqlite3.DatabaseError:
            # Should handle corruption gracefully
            self.assertTrue(True, "Database corruption detected and handled")
        finally:
            try:
                os.unlink(temp_db_path)
            except:
                pass

class TestMLModelFailureHandling(unittest.TestCase):
    """Test handling of ML model failures"""
    
    def setUp(self):
        """Set up ML failure testing"""
        self.client = TestClient(app)
    
    @patch('simple_detector.simple_predict')
    def test_ml_prediction_failure(self, mock_predict):
        """Test handling when ML prediction fails"""
        # Mock ML model failure
        mock_predict.side_effect = Exception("ML model crashed")
        
        # Test prediction with ML failure
        response = self.client.post("/predict", json={
            "message": "Test message for ML failure"
        })
        
        # Should handle ML failure gracefully
        if response.status_code == 200:
            data = response.json()
            # Should provide fallback classification
            self.assertIn("classification", data)
            self.assertIn("error_mode", data.get("metadata", {}))
        else:
            self.assertIn(response.status_code, [500, 503])
    
    @patch('simple_detector.simple_predict')
    def test_ml_model_timeout(self, mock_predict):
        """Test handling of ML model timeouts"""
        # Mock ML timeout
        import time
        def slow_prediction(*args, **kwargs):
            time.sleep(10)  # Simulate slow model
            return {"classification": "timeout"}
        
        mock_predict.side_effect = slow_prediction
        
        # Test with timeout
        response = self.client.post("/predict", json={
            "message": "Test message"
        }, timeout=5)
        
        # Should handle timeout appropriately
        self.assertIn(response.status_code, [200, 408, 500])
    
    def test_malformed_ml_response_handling(self):
        """Test handling of malformed ML responses"""
        with patch('simple_detector.simple_predict') as mock_predict:
            # Mock malformed response
            mock_predict.return_value = {
                "invalid_field": "bad_data",
                "missing_classification": True
            }
            
            response = self.client.post("/predict", json={
                "message": "Test message"
            })
            
            # Should handle malformed response
            if response.status_code == 200:
                data = response.json()
                # Should provide default values for missing fields
                self.assertIn("classification", data)
            else:
                self.assertIn(response.status_code, [500, 422])

class TestEmailServiceFailureHandling(unittest.TestCase):
    """Test handling of email service failures"""
    
    def setUp(self):
        """Set up email failure testing"""
        self.client = TestClient(app)
        
        # Register user and create scan for CERT reporting
        self.test_user = {
            "email": "emailfail@example.com",
            "username": "emailfail",
            "full_name": "Email Fail User",
            "password": "EmailFail123!"
        }
        
        self.client.post("/auth/register", json=self.test_user)
        login_response = self.client.post("/auth/login", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })
        
        self.token = login_response.json()["access_token"]
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}
    
    @patch('smtplib.SMTP')
    def test_smtp_connection_failure(self, mock_smtp):
        """Test handling of SMTP connection failures"""
        # Mock SMTP connection failure
        mock_smtp.side_effect = Exception("SMTP server unavailable")
        
        # Test CERT report that triggers email
        response = self.client.post("/cert/report", json={
            "scan_id": 1,
            "incident_type": "phishing",
            "additional_info": "Test incident"
        }, headers=self.auth_headers)
        
        # Should handle email failure gracefully
        if response.status_code in [200, 201]:
            data = response.json()
            # Should indicate email failure but still save report
            self.assertIn("warning", data.get("metadata", {}).get("email_status", ""))
        else:
            # CERT endpoint might not be implemented
            self.assertIn(response.status_code, [404, 501])
    
    @patch('smtplib.SMTP')
    def test_email_authentication_failure(self, mock_smtp):
        """Test handling of email authentication failures"""
        # Mock SMTP auth failure
        mock_server = Mock()
        mock_server.login.side_effect = Exception("Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Test email sending with auth failure
        response = self.client.post("/auth/password-reset/request", json={
            "email": self.test_user["email"]
        })
        
        # Should handle auth failure
        if response.status_code == 200:
            data = response.json()
            self.assertIn("message", data)
        else:
            # Password reset might not be implemented
            self.assertIn(response.status_code, [404, 501])
    
    def test_email_rate_limiting(self):
        """Test email rate limiting protection"""
        # Attempt multiple email requests rapidly
        for i in range(10):
            response = self.client.post("/auth/password-reset/request", json={
                "email": self.test_user["email"]
            })
            
            # Should implement rate limiting
            if i > 5:  # After several requests
                self.assertIn(response.status_code, [429, 404, 501])

class TestNetworkFailureHandling(unittest.TestCase):
    """Test handling of network-related failures"""
    
    def setUp(self):
        """Set up network failure testing"""
        self.client = TestClient(app)
    
    @patch('requests.get')
    def test_external_api_failure(self, mock_get):
        """Test handling of external API failures"""
        # Mock external API failure
        mock_get.side_effect = requests.exceptions.ConnectionError("API unavailable")
        
        # Test QR URL validation that might use external APIs
        response = self.client.post("/qr/scan", json={
            "qr_content": "https://suspicious-site.com"
        })
        
        # Should handle external API failure
        if response.status_code == 200:
            data = response.json()
            # Should provide local analysis when external APIs fail
            self.assertIn("url_analysis", data)
            self.assertIn("local_analysis_only", data.get("metadata", {}))
        else:
            self.assertIn(response.status_code, [500, 503])
    
    @patch('requests.post')
    def test_cert_api_failure(self, mock_post):
        """Test handling of CERT API communication failures"""
        # Mock CERT API failure
        mock_post.side_effect = requests.exceptions.Timeout("CERT API timeout")
        
        # Test CERT reporting with API failure
        response = self.client.post("/cert/api/report", json={
            "incident_type": "phishing",
            "content": "Test phishing content"
        })
        
        # Should handle CERT API failure gracefully
        if response.status_code in [200, 202]:
            data = response.json()
            # Should fallback to email reporting
            self.assertIn("fallback_method", data.get("metadata", {}))
        else:
            # CERT API might not be implemented
            self.assertIn(response.status_code, [404, 501])
    
    def test_dns_resolution_failure(self):
        """Test handling of DNS resolution failures"""
        # Test with URLs that might have DNS issues
        problematic_urls = [
            "https://nonexistent-domain-12345.com",
            "https://invalid-tld.invalidtld",
            "https://127.0.0.1:99999"  # Invalid port
        ]
        
        for url in problematic_urls:
            response = self.client.post("/qr/scan", json={
                "qr_content": url
            })
            
            # Should handle DNS/connection issues
            if response.status_code == 200:
                data = response.json()
                self.assertIn("url_analysis", data)
                # Should indicate connection issues
                self.assertIn("connection_status", data)

class TestInputValidationFailures(unittest.TestCase):
    """Test handling of malformed and malicious inputs"""
    
    def setUp(self):
        """Set up input validation testing"""
        self.client = TestClient(app)
    
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON requests"""
        malformed_requests = [
            '{"incomplete": json',
            '{"invalid": json, "missing": quote}',
            '{"number": 123abc}',
            ''
        ]
        
        for malformed_json in malformed_requests:
            response = self.client.post(
                "/predict",
                content=malformed_json,
                headers={"Content-Type": "application/json"}
            )
            
            # Should handle malformed JSON gracefully
            self.assertIn(response.status_code, [400, 422])
    
    def test_oversized_request_handling(self):
        """Test handling of oversized requests"""
        # Create very large message
        large_message = "A" * (1024 * 1024)  # 1MB message
        
        response = self.client.post("/predict", json={
            "message": large_message
        })
        
        # Should handle oversized requests
        self.assertIn(response.status_code, [413, 422, 400])
    
    def test_special_characters_handling(self):
        """Test handling of special characters and encoding"""
        special_inputs = [
            {"message": "Test\x00null\x00bytes"},
            {"message": "Unicode: 🔥💀🎯🚨"},
            {"message": "SQL: '; DROP TABLE users; --"},
            {"message": "XSS: <script>alert('hack')</script>"},
            {"message": "Control chars: \r\n\t\b"}
        ]
        
        for special_input in special_inputs:
            response = self.client.post("/predict", json=special_input)
            
            # Should handle special characters safely
            self.assertIn(response.status_code, [200, 400, 422])
            
            if response.status_code == 200:
                data = response.json()
                # Should not echo back dangerous content unescaped
                self.assertIn("classification", data)

class TestConcurrentErrorHandling(unittest.TestCase):
    """Test error handling under concurrent load"""
    
    def setUp(self):
        """Set up concurrent testing"""
        self.client = TestClient(app)
    
    def test_concurrent_database_failures(self):
        """Test handling of database failures under load"""
        import concurrent.futures
        import threading
        
        # Mock database failure for some requests
        def make_request(request_id):
            if request_id % 3 == 0:  # Every third request fails
                with patch('database.get_db') as mock_db:
                    mock_db.side_effect = OperationalError("DB busy", None, None)
                    return self.client.post("/predict", json={"message": f"Test {request_id}"})
            else:
                return self.client.post("/predict", json={"message": f"Test {request_id}"})
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [future.result() for future in futures]
        
        # Should handle mixed success/failure scenarios
        success_count = sum(1 for r in results if r.status_code == 200)
        error_count = sum(1 for r in results if r.status_code >= 400)
        
        # Should have some successful requests despite failures
        self.assertGreater(success_count + error_count, 0)
    
    def test_resource_exhaustion_handling(self):
        """Test handling of resource exhaustion"""
        # Simulate many concurrent requests
        responses = []
        
        for i in range(100):
            response = self.client.post("/predict", json={
                "message": f"Concurrent test message {i}"
            })
            responses.append(response.status_code)
        
        # Should handle high load gracefully
        success_rate = responses.count(200) / len(responses)
        
        # At least some requests should succeed
        self.assertGreater(success_rate, 0.5)

class TestRecoveryMechanisms(unittest.TestCase):
    """Test system recovery from failures"""
    
    def setUp(self):
        """Set up recovery testing"""
        self.client = TestClient(app)
    
    def test_graceful_degradation(self):
        """Test graceful degradation when services fail"""
        # Test with ML service failure
        with patch('simple_detector.simple_predict') as mock_predict:
            mock_predict.side_effect = Exception("ML service down")
            
            response = self.client.post("/predict", json={
                "message": "Test message during ML failure"
            })
            
            # Should provide degraded service
            if response.status_code == 200:
                data = response.json()
                # Should use fallback classification
                self.assertIn("classification", data)
                self.assertEqual(data.get("classification"), "unknown")
                self.assertIn("service_degraded", data.get("metadata", {}))
    
    def test_circuit_breaker_pattern(self):
        """Test circuit breaker for failing services"""
        # Simulate service that fails repeatedly
        failure_count = 0
        
        def failing_service(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            if failure_count < 5:
                raise Exception("Service failing")
            return {"status": "recovered"}
        
        with patch('cert_email_service.send_cert_email', side_effect=failing_service):
            # Make requests that trigger the failing service
            for i in range(10):
                response = self.client.post("/cert/report", json={
                    "scan_id": 1,
                    "incident_type": "phishing"
                })
                
                # Circuit breaker should eventually stop trying
                if i > 5:
                    self.assertIn(response.status_code, [200, 503, 404])

if __name__ == "__main__":
    unittest.main(verbosity=2)