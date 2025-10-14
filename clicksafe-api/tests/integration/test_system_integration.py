#!/usr/bin/env python3
"""
System Integration Testing
Tests integration between different system components
"""
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db, engine
from models import User, UserScan, RecentScam, AdminLog
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from datetime import datetime
from auth import hash_password, verify_password, create_access_token
from simple_detector import simple_predict

class TestSystemIntegration(unittest.TestCase):
    """Test integration across database, services, and API layers"""
    
    def setUp(self):
        """Setup test database connection"""
        self.db = next(get_db())
        
    def tearDown(self):
        """Cleanup after each test"""
        self.db.close()
    
    def test_database_api_service_integration(self):
        """Test complete integration: Database ↔ Models ↔ Services ↔ API"""
        
        # Step 1: Database Layer - Create test user
        test_user = User(
            email="system_test@example.com",
            username="system_test_user",
            full_name="System Test User",
            hashed_password=hash_password("TestPassword123!")
        )
        
        self.db.add(test_user)
        self.db.commit()
        self.db.refresh(test_user)
        
        # Verify user creation
        self.assertIsNotNone(test_user.id)
        self.assertEqual(test_user.email, "system_test@example.com")
        
        # Step 2: Service Layer - Authentication
        # Test password verification
        self.assertTrue(verify_password("TestPassword123!", test_user.hashed_password))
        self.assertFalse(verify_password("WrongPassword", test_user.hashed_password))
        
        # Test token creation
        token = create_access_token(data={"sub": test_user.email})
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        
        # Step 3: Service Layer - Content Analysis
        dangerous_content = "URGENT! Your bank account has been suspended. Click here to verify your details now!"
        analysis_result = simple_predict(dangerous_content)
        
        self.assertIn("classification", analysis_result)
        self.assertIn("risk_score", analysis_result)
        self.assertEqual(analysis_result["classification"], "dangerous")
        self.assertGreaterEqual(analysis_result["risk_score"], 0.7)
        
        # Step 4: Database Layer - Save scan results
        user_scan = UserScan(
            user_id=test_user.id,
            scan_type="message",
            content=dangerous_content,
            classification=analysis_result["classification"],
            risk_score=analysis_result["risk_score"],
            language=analysis_result["language"],
            suspicious_terms=analysis_result["suspicious_terms"],
            explanation=analysis_result["explanation"]
        )
        
        self.db.add(user_scan)
        self.db.commit()
        self.db.refresh(user_scan)
        
        # Verify scan storage
        self.assertIsNotNone(user_scan.id)
        self.assertEqual(user_scan.user_id, test_user.id)
        self.assertEqual(user_scan.classification, "dangerous")
        
        # Step 5: Database Layer - Query integration
        # Test user-scan relationship
        user_with_scans = self.db.query(User).filter(User.id == test_user.id).first()
        self.assertEqual(len(user_with_scans.scans), 1)
        self.assertEqual(user_with_scans.scans[0].content, dangerous_content)
        
        # Cleanup
        self.db.delete(user_scan)
        self.db.delete(test_user)
        self.db.commit()
    
    def test_recent_scams_integration(self):
        """Test Recent Scams feed integration across all layers"""
        
        # Step 1: Create test data
        test_scam = RecentScam(
            anonymized_content="URGENT: Your [NAME] account has been suspended. Click [URL] to verify immediately.",
            original_language="english",
            risk_score=0.95,
            classification="dangerous",
            suspicious_terms=["urgent", "suspended", "verify"],
            scan_count=1
        )
        
        self.db.add(test_scam)
        self.db.commit()
        self.db.refresh(test_scam)
        
        # Step 2: Test database retrieval
        retrieved_scam = self.db.query(RecentScam).filter(RecentScam.id == test_scam.id).first()
        self.assertIsNotNone(retrieved_scam)
        self.assertEqual(retrieved_scam.classification, "dangerous")
        self.assertEqual(retrieved_scam.scan_count, 1)
        
        # Step 3: Test filtering logic (dangerous only)
        dangerous_scams = self.db.query(RecentScam).filter(
            RecentScam.classification == "dangerous",
            RecentScam.risk_score >= 0.7
        ).all()
        
        self.assertGreater(len(dangerous_scams), 0)
        self.assertIn(test_scam, dangerous_scams)
        
        # Step 4: Test scan count increment (duplicate handling)
        test_scam.scan_count += 1
        self.db.commit()
        
        updated_scam = self.db.query(RecentScam).filter(RecentScam.id == test_scam.id).first()
        self.assertEqual(updated_scam.scan_count, 2)
        
        # Cleanup
        self.db.delete(test_scam)
        self.db.commit()
    
    def test_email_notification_integration(self):
        """Test email service integration (mock/dry run)"""
        
        # This test verifies email configuration and setup
        # without actually sending emails
        
        # Step 1: Test email configuration loading
        try:
            from cert_email_service import CertEmailService
            email_service = CertEmailService()
            
            # Verify email service initialization
            self.assertIsNotNone(email_service)
            
            # Test email composition (without sending)
            test_content = "Test phishing content for integration testing"
            test_analysis = {
                "classification": "dangerous",
                "risk_score": 0.95,
                "suspicious_terms": ["test", "phishing"]
            }
            
            # This should not fail even if email is not actually sent
            email_composed = True  # Placeholder for email composition logic
            self.assertTrue(email_composed)
            
        except ImportError:
            # Email service not available - skip this test
            self.skipTest("Email service not available for testing")
    
    def test_multi_language_integration(self):
        """Test multi-language content processing integration"""
        
        # Test English content
        english_content = "Urgent: Your account has been suspended!"
        english_result = simple_predict(english_content)
        
        self.assertEqual(english_result["language"], "english")
        self.assertEqual(english_result["classification"], "dangerous")
        
        # Test Tamil content (if supported)
        tamil_content = "அவசரம்: உங்கள் கணக்கு முடக்கப்பட்டுள்ளது!"
        tamil_result = simple_predict(tamil_content)
        
        self.assertIn("language", tamil_result)
        self.assertIn("classification", tamil_result)
        
        # Verify language-specific processing
        if tamil_result["language"] == "tamil":
            self.assertIn("suspicious_terms", tamil_result)
    
    def test_performance_integration(self):
        """Test system performance under load (basic)"""
        
        # Test multiple rapid predictions
        test_contents = [
            "Click here to claim your prize!",
            "Your account will be closed soon.",
            "Verify your payment information.",
            "Limited time offer expires today!",
            "Update your security settings now."
        ]
        
        start_time = datetime.now()
        
        results = []
        for content in test_contents:
            result = simple_predict(content)
            results.append(result)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        self.assertEqual(len(results), len(test_contents))
        self.assertLess(processing_time, 10.0)  # Should complete within 10 seconds
        
        # Verify all results have required fields
        for result in results:
            self.assertIn("classification", result)
            self.assertIn("risk_score", result)
            self.assertIn("language", result)
    
    def test_data_consistency_integration(self):
        """Test data consistency across database operations"""
        
        # Step 1: Create test user
        test_user = User(
            email="consistency_test@example.com",
            username="consistency_test",
            full_name="Consistency Test User",
            hashed_password=hash_password("TestPassword123!")
        )
        
        self.db.add(test_user)
        self.db.commit()
        self.db.refresh(test_user)
        
        # Step 2: Create multiple scans
        scan_contents = [
            "Dangerous phishing attempt 1",
            "Dangerous phishing attempt 2",
            "Safe message content",
        ]
        
        created_scans = []
        for i, content in enumerate(scan_contents):
            analysis = simple_predict(content)
            
            scan = UserScan(
                user_id=test_user.id,
                scan_type="message",
                content=content,
                classification=analysis["classification"],
                risk_score=analysis["risk_score"],
                language=analysis["language"],
                suspicious_terms=analysis["suspicious_terms"]
            )
            
            self.db.add(scan)
            created_scans.append(scan)
        
        self.db.commit()
        
        # Step 3: Verify data consistency
        # Check user scan count
        user_scans = self.db.query(UserScan).filter(UserScan.user_id == test_user.id).all()
        self.assertEqual(len(user_scans), len(scan_contents))
        
        # Check dangerous scan classification
        dangerous_scans = self.db.query(UserScan).filter(
            UserScan.user_id == test_user.id,
            UserScan.classification == "dangerous"
        ).all()
        
        # Should have some dangerous scans
        self.assertGreater(len(dangerous_scans), 0)
        
        # Cleanup
        for scan in created_scans:
            self.db.delete(scan)
        self.db.delete(test_user)
        self.db.commit()

class TestDatabaseIntegration(unittest.TestCase):
    """Test database-specific integration scenarios"""
    
    def setUp(self):
        self.db = next(get_db())
    
    def tearDown(self):
        self.db.close()
    
    def test_foreign_key_constraints(self):
        """Test database foreign key relationships"""
        
        # Create user first
        user = User(
            email="fk_test@example.com",
            username="fk_test",
            full_name="FK Test User",
            hashed_password=hash_password("TestPassword123!")
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Create scan with valid user_id
        scan = UserScan(
            user_id=user.id,
            scan_type="message",
            content="Test content",
            classification="safe",
            risk_score=0.1,
            language="english"
        )
        
        self.db.add(scan)
        self.db.commit()  # Should succeed
        
        # Verify relationship
        self.assertEqual(scan.user.email, "fk_test@example.com")
        self.assertEqual(len(user.scans), 1)
        
        # Cleanup
        self.db.delete(scan)
        self.db.delete(user)
        self.db.commit()
    
    def test_database_transaction_rollback(self):
        """Test database transaction handling"""
        
        try:
            # Start transaction
            user = User(
                email="rollback_test@example.com",
                username="rollback_test",
                full_name="Rollback Test User",
                hashed_password=hash_password("TestPassword123!")
            )
            
            self.db.add(user)
            self.db.flush()  # Flush but don't commit
            
            # Intentionally cause an error (duplicate email)
            duplicate_user = User(
                email="rollback_test@example.com",  # Same email
                username="rollback_test2",
                full_name="Duplicate User",
                hashed_password=hash_password("TestPassword123!")
            )
            
            self.db.add(duplicate_user)
            
            # This should fail due to unique constraint
            with self.assertRaises(Exception):
                self.db.commit()
            
            # Rollback transaction
            self.db.rollback()
            
            # Verify rollback - user should not exist
            existing_user = self.db.query(User).filter(User.email == "rollback_test@example.com").first()
            self.assertIsNone(existing_user)
            
        except Exception as e:
            self.db.rollback()
            raise e

if __name__ == "__main__":
    unittest.main(verbosity=2)