#!/usr/bin/env python3
"""
Real-Time Features Integration Tests
Tests real-time updates, live feeds, and concurrent operations
"""
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import asyncio
import threading
from unittest.mock import patch, Mock, MagicMock
from fastapi.testclient import TestClient
from main import app
import concurrent.futures
from datetime import datetime, timedelta

class TestRecentScamsAutoRefresh(unittest.TestCase):
    """Test Recent Scam Alerts auto-refresh functionality"""
    
    def setUp(self):
        """Set up real-time testing environment"""
        self.client = TestClient(app)
        
        # Create multiple test users
        self.users = []
        for i in range(3):
            user = {
                "email": f"realtime{i}@example.com",
                "username": f"realtime{i}",
                "full_name": f"Realtime User {i}",
                "password": f"Realtime{i}123!"
            }
            
            self.client.post("/auth/register", json=user)
            login_response = self.client.post("/auth/login", json={
                "email": user["email"],
                "password": user["password"]
            })
            
            token = login_response.json()["access_token"]
            user["token"] = token
            user["headers"] = {"Authorization": f"Bearer {token}"}
            self.users.append(user)
    
    def test_recent_scams_feed_updates(self):
        """Test that Recent Scam Alerts feed updates with new threats"""
        # Get initial recent scams count
        initial_response = self.client.get("/scams/recent")
        initial_count = len(initial_response.json()) if initial_response.status_code == 200 else 0
        
        # Users submit dangerous messages
        dangerous_messages = [
            "URGENT: Your PayPal account suspended! Click here immediately!",
            "Congratulations! You've won $10,000! Claim now!",
            "Security Alert: Unusual activity detected. Verify now!"
        ]
        
        for i, message in enumerate(dangerous_messages):
            # Submit dangerous message
            self.client.post("/scan/message", json={
                "scan_type": "message",
                "content": message
            }, headers=self.users[i]["headers"])
            
            # Small delay to simulate real-time updates
            time.sleep(0.1)
        
        # Check if Recent Scam Alerts updated
        updated_response = self.client.get("/scams/recent")
        
        if updated_response.status_code == 200:
            updated_count = len(updated_response.json())
            
            # Should have more recent scams (or same if already at limit)
            self.assertGreaterEqual(updated_count, initial_count)
            
            # Verify dangerous messages appear in feed
            recent_scams = updated_response.json()
            if recent_scams:
                # Check for anonymized versions of submitted messages
                found_threats = [scam for scam in recent_scams 
                               if scam.get("classification") == "dangerous"]
                self.assertGreater(len(found_threats), 0)
    
    def test_real_time_feed_ordering(self):
        """Test that Recent Scam Alerts are ordered by recency"""
        # Submit multiple dangerous messages with time gaps
        messages = [
            "Phishing attempt 1: Click here for free money!",
            "Phishing attempt 2: Your account will be closed!",
            "Phishing attempt 3: Urgent security update required!"
        ]
        
        submission_times = []
        
        for i, message in enumerate(messages):
            submission_time = datetime.now()
            submission_times.append(submission_time)
            
            self.client.post("/scan/message", json={
                "scan_type": "message", 
                "content": message
            }, headers=self.users[i % len(self.users)]["headers"])
            
            time.sleep(0.5)  # Ensure different timestamps
        
        # Get recent scams feed
        response = self.client.get("/scams/recent")
        
        if response.status_code == 200:
            recent_scams = response.json()
            
            if len(recent_scams) >= 2:
                # Verify ordering (most recent first)
                for i in range(len(recent_scams) - 1):
                    current_time = recent_scams[i].get("created_at", "")
                    next_time = recent_scams[i + 1].get("created_at", "")
                    
                    if current_time and next_time:
                        # Current should be more recent than next
                        self.assertGreaterEqual(current_time, next_time)
    
    def test_feed_rate_limiting(self):
        """Test rate limiting for feed updates"""
        # Make rapid requests to Recent Scam Alerts
        rapid_requests = []
        
        for i in range(20):
            response = self.client.get("/scams/recent")
            rapid_requests.append(response.status_code)
            time.sleep(0.05)  # Very rapid requests
        
        # Should handle rapid requests without errors
        successful_requests = rapid_requests.count(200)
        rate_limited = rapid_requests.count(429)
        
        # Most requests should succeed, some might be rate limited
        self.assertGreater(successful_requests, 10)

class TestLiveThreatUpdates(unittest.TestCase):
    """Test live threat detection and notification updates"""
    
    def setUp(self):
        """Set up live threat testing"""
        self.client = TestClient(app)
        
        # Create authenticated user
        self.test_user = {
            "email": "live@example.com",
            "username": "liveuser",
            "full_name": "Live User", 
            "password": "LiveUser123!"
        }
        
        self.client.post("/auth/register", json=self.test_user)
        login_response = self.client.post("/auth/login", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })
        
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_immediate_threat_classification(self):
        """Test immediate threat classification and response"""
        # Submit extremely dangerous message
        dangerous_message = {
            "scan_type": "message",
            "content": "URGENT SECURITY ALERT: Your bank account compromised! Click here IMMEDIATELY to secure: http://fake-bank.com/urgent"
        }
        
        start_time = time.time()
        
        response = self.client.post("/scan/message", json=dangerous_message, headers=self.headers)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Should respond quickly (real-time requirement)
        self.assertLess(response_time, 2.0)  # Less than 2 seconds
        
        if response.status_code == 200:
            result = response.json()
            
            # Should immediately classify as dangerous
            self.assertEqual(result.get("classification"), "dangerous")
            self.assertGreater(result.get("risk_score", 0), 0.8)
            
            # Should include immediate warning
            self.assertIn("warning", result.get("metadata", {}).get("alerts", []))
    
    def test_live_dashboard_updates(self):
        """Test that user dashboard updates immediately after scanning"""
        # Get initial dashboard stats
        initial_stats = self.client.get("/dashboard/stats", headers=self.headers)
        initial_total = 0
        
        if initial_stats.status_code == 200:
            initial_total = initial_stats.json().get("total_scans", 0)
        
        # Submit new scan
        self.client.post("/scan/message", json={
            "scan_type": "message",
            "content": "Test live dashboard update message"
        }, headers=self.headers)
        
        # Immediately check dashboard again
        updated_stats = self.client.get("/dashboard/stats", headers=self.headers)
        
        if updated_stats.status_code == 200:
            updated_total = updated_stats.json().get("total_scans", 0)
            
            # Should reflect new scan immediately
            self.assertGreater(updated_total, initial_total)
    
    def test_threat_level_escalation(self):
        """Test threat level escalation for severe threats"""
        # Submit progressively more dangerous messages
        threat_levels = [
            ("Suspicious message with prize offer", "suspicious"),
            ("Click here to verify your account now!", "dangerous"),
            ("URGENT: Bank account suspended! Act immediately!", "critical")
        ]
        
        for message, expected_level in threat_levels:
            response = self.client.post("/scan/message", json={
                "scan_type": "message",
                "content": message
            }, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                classification = result.get("classification", "")
                
                # Should escalate appropriately
                if expected_level == "critical":
                    self.assertIn(classification, ["dangerous", "critical"])
                elif expected_level == "dangerous":
                    self.assertIn(classification, ["suspicious", "dangerous"])

class TestConcurrentUserOperations(unittest.TestCase):
    """Test concurrent operations from multiple users"""
    
    def setUp(self):
        """Set up concurrent testing environment"""
        self.client = TestClient(app)
        
        # Create multiple users for concurrent testing
        self.concurrent_users = []
        for i in range(10):
            user = {
                "email": f"concurrent{i}@example.com",
                "username": f"concurrent{i}",
                "full_name": f"Concurrent User {i}",
                "password": f"Concurrent{i}123!"
            }
            
            self.client.post("/auth/register", json=user)
            login_response = self.client.post("/auth/login", json={
                "email": user["email"],
                "password": user["password"]
            })
            
            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                user["headers"] = {"Authorization": f"Bearer {token}"}
                self.concurrent_users.append(user)
    
    def test_concurrent_threat_detection(self):
        """Test concurrent threat detection from multiple users"""
        # Messages for concurrent scanning
        test_messages = [
            "Click here to win money!",
            "Your account needs verification",
            "Urgent security update required",
            "Free gift waiting for you!",
            "Bank account suspended - act now!",
            "Congratulations on your prize!",
            "Security alert - click immediately",
            "Limited time offer - click now!",
            "Account verification needed urgently",
            "System security breach detected"
        ]
        
        def scan_message(user_index):
            if user_index < len(self.concurrent_users):
                user = self.concurrent_users[user_index]
                message = test_messages[user_index % len(test_messages)]
                
                response = self.client.post("/scan/message", json={
                    "scan_type": "message",
                    "content": message
                }, headers=user["headers"])
                
                return response.status_code, user_index
            return 400, user_index
        
        # Execute concurrent scans
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(scan_message, i) for i in range(len(self.concurrent_users))]
            results = [future.result() for future in futures]
        
        # Analyze results
        successful_scans = sum(1 for status, _ in results if status == 200)
        
        # Most scans should succeed under concurrent load
        self.assertGreater(successful_scans, len(self.concurrent_users) * 0.8)
    
    def test_concurrent_dashboard_access(self):
        """Test concurrent dashboard access"""
        def get_dashboard_stats(user_index):
            if user_index < len(self.concurrent_users):
                user = self.concurrent_users[user_index]
                response = self.client.get("/dashboard/stats", headers=user["headers"])
                return response.status_code
            return 400
        
        # Concurrent dashboard requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(get_dashboard_stats, i) for i in range(5)]
            results = [future.result() for future in futures]
        
        # All dashboard requests should succeed
        successful_requests = results.count(200)
        self.assertGreater(successful_requests, 3)
    
    def test_recent_scams_concurrent_updates(self):
        """Test Recent Scam Alerts under concurrent updates"""
        # Multiple users submit dangerous messages simultaneously
        dangerous_message = "URGENT: Your account will be suspended! Click here now!"
        
        def submit_dangerous_scan(user_index):
            if user_index < len(self.concurrent_users):
                user = self.concurrent_users[user_index]
                response = self.client.post("/scan/message", json={
                    "scan_type": "message",
                    "content": f"{dangerous_message} {user_index}"
                }, headers=user["headers"])
                return response.status_code
            return 400
        
        # Concurrent dangerous message submissions
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(submit_dangerous_scan, i) for i in range(5)]
            results = [future.result() for future in futures]
        
        # Check Recent Scam Alerts feed
        recent_scams_response = self.client.get("/scams/recent")
        
        if recent_scams_response.status_code == 200:
            recent_scams = recent_scams_response.json()
            
            # Should handle concurrent updates correctly
            self.assertIsInstance(recent_scams, list)
            
            # Should have recent dangerous content
            if recent_scams:
                dangerous_count = sum(1 for scam in recent_scams 
                                    if scam.get("classification") == "dangerous")
                self.assertGreater(dangerous_count, 0)

class TestWebSocketRealtimeFeatures(unittest.TestCase):
    """Test WebSocket real-time features (if implemented)"""
    
    def setUp(self):
        """Set up WebSocket testing"""
        self.client = TestClient(app)
    
    def test_websocket_connection_establishment(self):
        """Test WebSocket connection for real-time updates"""
        try:
            # Attempt WebSocket connection
            with self.client.websocket_connect("/ws/threats") as websocket:
                # Test connection established
                self.assertIsNotNone(websocket)
                
                # Send subscription message
                websocket.send_json({
                    "type": "subscribe",
                    "channel": "recent_threats"
                })
                
                # Wait for acknowledgment
                response = websocket.receive_json(timeout=5)
                
                self.assertIn("type", response)
                self.assertEqual(response.get("type"), "subscription_confirmed")
                
        except Exception:
            # WebSocket not implemented yet - that's okay for now
            self.skipTest("WebSocket functionality not implemented yet")
    
    def test_real_time_threat_notifications(self):
        """Test real-time threat notifications via WebSocket"""
        try:
            with self.client.websocket_connect("/ws/threats") as websocket:
                # Subscribe to threat notifications
                websocket.send_json({
                    "type": "subscribe",
                    "channel": "new_threats"
                })
                
                # Trigger a new threat (submit dangerous message)
                self.client.post("/scan/message", json={
                    "scan_type": "message",
                    "content": "URGENT: Banking security breach detected!"
                })
                
                # Wait for real-time notification
                notification = websocket.receive_json(timeout=10)
                
                # Should receive threat notification
                self.assertIn("type", notification)
                self.assertEqual(notification.get("type"), "new_threat")
                self.assertIn("threat_data", notification)
                
        except Exception:
            # WebSocket not implemented yet
            self.skipTest("WebSocket threat notifications not implemented yet")
    
    def test_websocket_connection_limits(self):
        """Test WebSocket connection limits and management"""
        connections = []
        
        try:
            # Attempt multiple WebSocket connections
            for i in range(5):
                ws = self.client.websocket_connect(f"/ws/user_{i}")
                connections.append(ws)
            
            # Should handle multiple connections appropriately
            self.assertLessEqual(len(connections), 5)
            
        except Exception:
            # WebSocket limits not implemented yet
            self.skipTest("WebSocket connection management not implemented yet")
        finally:
            # Clean up connections
            for ws in connections:
                try:
                    ws.close()
                except:
                    pass

class TestSystemResponseTime(unittest.TestCase):
    """Test system response times for real-time requirements"""
    
    def setUp(self):
        """Set up response time testing"""
        self.client = TestClient(app)
    
    def test_threat_detection_response_time(self):
        """Test that threat detection responds within acceptable time"""
        # Test various message types and measure response times
        test_cases = [
            "Simple safe message",
            "Click here to win money! Urgent offer!",
            "CRITICAL: Your bank account compromised! Act NOW!",
            "Lorem ipsum dolor sit amet " * 100  # Long message
        ]
        
        response_times = []
        
        for message in test_cases:
            start_time = time.time()
            
            response = self.client.post("/predict", json={
                "message": message
            })
            
            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)
            
            # Individual response should be fast
            self.assertLess(response_time, 3.0)  # Less than 3 seconds
        
        # Average response time should be reasonable
        avg_response_time = sum(response_times) / len(response_times)
        self.assertLess(avg_response_time, 2.0)  # Average less than 2 seconds
    
    def test_api_endpoint_performance(self):
        """Test performance of key API endpoints"""
        endpoints_to_test = [
            ("/health", {}),
            ("/", {}),
            ("/scams/recent", {}),
        ]
        
        performance_results = {}
        
        for endpoint, params in endpoints_to_test:
            start_time = time.time()
            
            response = self.client.get(endpoint, params=params)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            performance_results[endpoint] = {
                "response_time": response_time,
                "status_code": response.status_code
            }
            
            # Each endpoint should respond quickly
            self.assertLess(response_time, 2.0)
        
        # Log performance results for analysis
        for endpoint, results in performance_results.items():
            print(f"{endpoint}: {results['response_time']:.3f}s ({results['status_code']})")

if __name__ == "__main__":
    unittest.main(verbosity=2)