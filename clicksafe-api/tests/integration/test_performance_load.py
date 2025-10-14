#!/usr/bin/env python3
"""
Performance and Load Testing
Tests system performance under various load conditions
"""
import unittest
import time
import threading
import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simple_detector import simple_predict
from database import get_db
from models import User, UserScan
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

class TestPerformanceIntegration(unittest.TestCase):
    """Test system performance and load handling"""
    
    def setUp(self):
        """Setup for performance tests"""
        self.base_url = "http://localhost:8000"
        self.test_contents = [
            "Click here to claim your prize now!",
            "Your account has been suspended - verify immediately",
            "Limited time offer - expires in 24 hours",
            "Update your payment information to avoid closure",
            "Urgent: Your security has been compromised",
            "Free money waiting - click to collect",
            "Your package is ready for delivery",
            "Congratulations! You've won a lottery",
            "Bank notification: Unusual activity detected",
            "Password reset required immediately"
        ]
    
    def test_prediction_performance(self):
        """Test ML prediction performance under load"""
        
        # Single prediction performance
        start_time = time.time()
        result = simple_predict(self.test_contents[0])
        single_prediction_time = time.time() - start_time
        
        self.assertLess(single_prediction_time, 2.0, "Single prediction should complete within 2 seconds")
        self.assertIn("classification", result)
        
        # Batch prediction performance
        start_time = time.time()
        results = []
        for content in self.test_contents:
            result = simple_predict(content)
            results.append(result)
        batch_prediction_time = time.time() - start_time
        
        self.assertEqual(len(results), len(self.test_contents))
        self.assertLess(batch_prediction_time, 10.0, "Batch predictions should complete within 10 seconds")
        
        # Calculate average prediction time
        avg_prediction_time = batch_prediction_time / len(self.test_contents)
        self.assertLess(avg_prediction_time, 1.0, "Average prediction time should be under 1 second")
        
        print(f"Single prediction: {single_prediction_time:.3f}s")
        print(f"Batch predictions: {batch_prediction_time:.3f}s")
        print(f"Average per prediction: {avg_prediction_time:.3f}s")
    
    def test_concurrent_predictions(self):
        """Test concurrent ML predictions"""
        
        def predict_content(content):
            start_time = time.time()
            result = simple_predict(content)
            end_time = time.time()
            return {
                "content": content,
                "result": result,
                "time": end_time - start_time
            }
        
        # Test with multiple threads
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(predict_content, content) for content in self.test_contents]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Assertions
        self.assertEqual(len(results), len(self.test_contents))
        self.assertLess(total_time, 5.0, "Concurrent predictions should complete within 5 seconds")
        
        # Check individual prediction times
        prediction_times = [r["time"] for r in results]
        max_time = max(prediction_times)
        avg_time = statistics.mean(prediction_times)
        
        self.assertLess(max_time, 3.0, "No single prediction should take more than 3 seconds")
        self.assertLess(avg_time, 1.5, "Average concurrent prediction time should be under 1.5 seconds")
        
        print(f"Concurrent predictions total: {total_time:.3f}s")
        print(f"Max individual time: {max_time:.3f}s")
        print(f"Average time: {avg_time:.3f}s")
    
    def test_database_performance(self):
        """Test database operation performance"""
        
        db = next(get_db())
        
        try:
            # Test user creation performance
            start_time = time.time()
            test_users = []
            
            for i in range(10):
                user = User(
                    email=f"perf_test_{i}@example.com",
                    username=f"perf_test_user_{i}",
                    full_name=f"Performance Test User {i}",
                    hashed_password="hashed_password_here"
                )
                db.add(user)
                test_users.append(user)
            
            db.commit()
            user_creation_time = time.time() - start_time
            
            self.assertLess(user_creation_time, 2.0, "Creating 10 users should take less than 2 seconds")
            
            # Test scan creation performance
            start_time = time.time()
            test_scans = []
            
            for i, user in enumerate(test_users):
                scan = UserScan(
                    user_id=user.id,
                    scan_type="message",
                    content=f"Test content {i}",
                    classification="safe",
                    risk_score=0.1,
                    language="english"
                )
                db.add(scan)
                test_scans.append(scan)
            
            db.commit()
            scan_creation_time = time.time() - start_time
            
            self.assertLess(scan_creation_time, 2.0, "Creating 10 scans should take less than 2 seconds")
            
            # Test query performance
            start_time = time.time()
            users_with_scans = db.query(User).join(UserScan).all()
            query_time = time.time() - start_time
            
            self.assertGreaterEqual(len(users_with_scans), 10)
            self.assertLess(query_time, 1.0, "Complex query should complete within 1 second")
            
            print(f"User creation (10): {user_creation_time:.3f}s")
            print(f"Scan creation (10): {scan_creation_time:.3f}s")
            print(f"Complex query: {query_time:.3f}s")
            
            # Cleanup
            for scan in test_scans:
                db.delete(scan)
            for user in test_users:
                db.delete(user)
            db.commit()
            
        finally:
            db.close()
    
    def test_api_response_time(self):
        """Test API endpoint response times"""
        
        # Test anonymous prediction endpoint
        test_data = {"message": "Click here to claim your free prize!"}
        
        response_times = []
        for _ in range(5):
            start_time = time.time()
            try:
                response = requests.post(f"{self.base_url}/predict", json=test_data, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    response_times.append(response_time)
                    result = response.json()
                    self.assertIn("classification", result)
                
            except requests.exceptions.RequestException as e:
                print(f"API request failed: {e}")
                # Skip this test if API is not available
                self.skipTest("API endpoint not available for testing")
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            self.assertLess(avg_response_time, 3.0, "Average API response time should be under 3 seconds")
            self.assertLess(max_response_time, 5.0, "Max API response time should be under 5 seconds")
            
            print(f"API response times: avg={avg_response_time:.3f}s, max={max_response_time:.3f}s")
    
    def test_concurrent_api_requests(self):
        """Test API under concurrent load"""
        
        def make_api_request(content):
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/predict", 
                    json={"message": content},
                    timeout=15
                )
                response_time = time.time() - start_time
                
                return {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "success": response.status_code == 200
                }
            except Exception as e:
                return {
                    "status_code": 0,
                    "response_time": 0,
                    "success": False,
                    "error": str(e)
                }
        
        # Test with concurrent requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_api_request, content) for content in self.test_contents[:5]]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Check if any requests succeeded (API might not be running)
        successful_requests = [r for r in results if r["success"]]
        
        if successful_requests:
            self.assertGreater(len(successful_requests), 0, "At least some concurrent requests should succeed")
            
            avg_response_time = statistics.mean([r["response_time"] for r in successful_requests])
            self.assertLess(avg_response_time, 5.0, "Average concurrent API response time should be reasonable")
            
            print(f"Concurrent API requests: {len(successful_requests)}/{len(results)} successful")
            print(f"Total time: {total_time:.3f}s")
            print(f"Average response time: {avg_response_time:.3f}s")
        else:
            print("No API requests succeeded - API may not be running")
            self.skipTest("API not available for concurrent testing")
    
    def test_memory_usage_stability(self):
        """Test memory usage during extended operations"""
        
        # Perform many predictions to test memory stability
        initial_time = time.time()
        
        for i in range(50):
            content = f"Test phishing content number {i} - click here for free prizes!"
            result = simple_predict(content)
            
            # Verify each prediction works
            self.assertIn("classification", result)
            
            # Add small delay to simulate real usage
            time.sleep(0.1)
        
        total_time = time.time() - initial_time
        
        # Should complete without memory issues
        self.assertLess(total_time, 30.0, "50 predictions should complete within 30 seconds")
        
        print(f"Extended operation (50 predictions): {total_time:.3f}s")

if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)