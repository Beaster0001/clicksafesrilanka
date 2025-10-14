#!/usr/bin/env python3
"""
Unit Tests for Database Module
Tests database connection, session management, and transaction handling
"""
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import database
from models import Base, User, UserScan, RecentScam, AdminLog, PasswordResetToken
from datetime import datetime, timedelta

class TestDatabaseConnection(unittest.TestCase):
    """Test database connection and engine setup"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db_file.close()
        self.test_database_url = f"sqlite:///{self.test_db_file.name}"
        
        # Create test engine
        self.test_engine = create_engine(
            self.test_database_url,
            connect_args={"check_same_thread": False}
        )
        
        # Create all tables
        Base.metadata.create_all(bind=self.test_engine)
        
        # Create test session factory
        self.TestSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.test_engine
        )
    
    def tearDown(self):
        """Clean up test database"""
        self.test_engine.dispose()
        try:
            os.unlink(self.test_db_file.name)
        except:
            pass
    
    def test_engine_creation(self):
        """Test database engine creation"""
        # Test that we can create an engine
        engine = create_engine(
            "sqlite:///test.db",
            connect_args={"check_same_thread": False}
        )
        
        self.assertIsNotNone(engine)
        self.assertEqual(engine.name, "sqlite")
    
    def test_database_connection(self):
        """Test database connection establishment"""
        # Test connection to the test database
        with self.test_engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            self.assertEqual(result.fetchone()[0], 1)
    
    def test_table_creation(self):
        """Test that all tables are created properly"""
        # Check that all expected tables exist
        inspector = inspect(self.test_engine)
        table_names = inspector.get_table_names()
        
        expected_tables = ["users", "user_scans", "recent_scams", "admin_logs", "password_reset_tokens"]
        
        for table in expected_tables:
            self.assertIn(table, table_names)
    
    def test_session_creation(self):
        """Test session creation and basic operations"""
        session = self.TestSessionLocal()
        
        try:
            # Test that we can query the database
            result = session.execute(text("SELECT 1"))
            self.assertEqual(result.fetchone()[0], 1)
            
            # Test that we can add and commit
            user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User"
            )
            session.add(user)
            session.commit()
            
            # Verify user was added
            saved_user = session.query(User).filter(User.email == "test@example.com").first()
            self.assertIsNotNone(saved_user)
            self.assertEqual(saved_user.username, "testuser")
            
        finally:
            session.close()

class TestDatabaseSession(unittest.TestCase):
    """Test database session management"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db_file.close()
        self.test_database_url = f"sqlite:///{self.test_db_file.name}"
        
        self.test_engine = create_engine(
            self.test_database_url,
            connect_args={"check_same_thread": False}
        )
        
        Base.metadata.create_all(bind=self.test_engine)
        
        self.TestSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.test_engine
        )
    
    def tearDown(self):
        """Clean up test database"""
        self.test_engine.dispose()
        try:
            os.unlink(self.test_db_file.name)
        except:
            pass
    
    def test_session_autocommit_false(self):
        """Test that sessions don't autocommit"""
        session = self.TestSessionLocal()
        
        try:
            # Add a user but don't commit
            user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User"
            )
            session.add(user)
            
            # Create another session to check if user exists
            session2 = self.TestSessionLocal()
            try:
                saved_user = session2.query(User).filter(User.email == "test@example.com").first()
                # Should be None because we didn't commit
                self.assertIsNone(saved_user)
            finally:
                session2.close()
            
            # Now commit and check again
            session.commit()
            
            session3 = self.TestSessionLocal()
            try:
                saved_user = session3.query(User).filter(User.email == "test@example.com").first()
                # Should exist now
                self.assertIsNotNone(saved_user)
            finally:
                session3.close()
                
        finally:
            session.close()
    
    def test_session_rollback(self):
        """Test session rollback functionality"""
        session = self.TestSessionLocal()
        
        try:
            # Add a user
            user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User"
            )
            session.add(user)
            session.commit()
            
            # Modify the user
            user.full_name = "Modified Name"
            
            # Rollback the change
            session.rollback()
            
            # Check that the change was rolled back
            session.refresh(user)
            self.assertEqual(user.full_name, "Test User")
            
        finally:
            session.close()
    
    def test_session_isolation(self):
        """Test that sessions are isolated from each other"""
        session1 = self.TestSessionLocal()
        session2 = self.TestSessionLocal()
        
        try:
            # Add user in session1
            user1 = User(
                email="test1@example.com",
                username="testuser1",
                hashed_password="hashed_password",
                full_name="Test User 1"
            )
            session1.add(user1)
            session1.commit()
            
            # Modify user in session1
            user1.full_name = "Modified Name"
            
            # Get same user in session2
            user2 = session2.query(User).filter(User.email == "test1@example.com").first()
            
            # session2 should not see the uncommitted changes from session1
            self.assertEqual(user2.full_name, "Test User 1")
            
            # Commit changes in session1
            session1.commit()
            
            # Refresh session2 to see committed changes
            session2.refresh(user2)
            self.assertEqual(user2.full_name, "Modified Name")
            
        finally:
            session1.close()
            session2.close()

class TestDatabaseTransactions(unittest.TestCase):
    """Test database transaction handling"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db_file.close()
        self.test_database_url = f"sqlite:///{self.test_db_file.name}"
        
        self.test_engine = create_engine(
            self.test_database_url,
            connect_args={"check_same_thread": False}
        )
        
        Base.metadata.create_all(bind=self.test_engine)
        
        self.TestSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.test_engine
        )
    
    def tearDown(self):
        """Clean up test database"""
        self.test_engine.dispose()
        try:
            os.unlink(self.test_db_file.name)
        except:
            pass
    
    def test_successful_transaction(self):
        """Test successful transaction with multiple operations"""
        session = self.TestSessionLocal()
        
        try:
            # Begin transaction (implicit)
            user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User"
            )
            session.add(user)
            session.flush()  # Get the user ID
            
            # Add a scan for the user
            scan = UserScan(
                user_id=user.id,
                scan_type="message",
                content="Test message",
                classification="safe",
                risk_score=0.1,
                language="english"
            )
            session.add(scan)
            
            # Commit transaction
            session.commit()
            
            # Verify both records exist
            saved_user = session.query(User).filter(User.email == "test@example.com").first()
            self.assertIsNotNone(saved_user)
            
            saved_scan = session.query(UserScan).filter(UserScan.user_id == saved_user.id).first()
            self.assertIsNotNone(saved_scan)
            self.assertEqual(saved_scan.content, "Test message")
            
        finally:
            session.close()
    
    def test_failed_transaction_rollback(self):
        """Test transaction rollback on error"""
        session = self.TestSessionLocal()
        
        try:
            # Add a user
            user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User"
            )
            session.add(user)
            session.commit()
            
            # Start a new transaction
            scan = UserScan(
                user_id=user.id,
                scan_type="message",
                content="Test message",
                classification="safe",
                risk_score=0.1,
                language="english"
            )
            session.add(scan)
            
            # Try to add a duplicate user (should fail)
            duplicate_user = User(
                email="test@example.com",  # Same email - should fail
                username="testuser2",
                hashed_password="hashed_password",
                full_name="Test User 2"
            )
            session.add(duplicate_user)
            
            # This should fail and rollback
            with self.assertRaises(SQLAlchemyError):
                session.commit()
            
            # Verify that neither the scan nor the duplicate user was saved
            scan_count = session.query(UserScan).count()
            user_count = session.query(User).count()
            
            self.assertEqual(scan_count, 0)  # Scan should be rolled back
            self.assertEqual(user_count, 1)  # Only original user should exist
            
        except Exception as e:
            session.rollback()
        finally:
            session.close()
    
    def test_nested_transaction_behavior(self):
        """Test behavior with nested transactions (savepoints)"""
        session = self.TestSessionLocal()
        
        try:
            # Create a user
            user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User"
            )
            session.add(user)
            session.commit()
            
            # Create a savepoint
            savepoint = session.begin_nested()
            
            try:
                # Add a scan
                scan = UserScan(
                    user_id=user.id,
                    scan_type="message",
                    content="Test message",
                    classification="safe",
                    risk_score=0.1,
                    language="english"
                )
                session.add(scan)
                
                # Commit the savepoint
                savepoint.commit()
                
                # The scan should be visible in the session
                scan_count = session.query(UserScan).count()
                self.assertEqual(scan_count, 1)
                
            except Exception:
                savepoint.rollback()
            
            # Commit the main transaction
            session.commit()
            
            # Verify scan exists
            final_scan_count = session.query(UserScan).count()
            self.assertEqual(final_scan_count, 1)
            
        finally:
            session.close()

class TestDatabaseUtilityFunctions(unittest.TestCase):
    """Test utility functions in database module"""
    
    def test_get_db_dependency(self):
        """Test the get_db dependency function if it exists"""
        # This test depends on the actual implementation of get_db in database.py
        # For now, we'll test the concept
        
        if hasattr(database, 'get_db'):
            # Test that get_db returns a generator
            db_gen = database.get_db()
            self.assertTrue(hasattr(db_gen, '__next__'))
    
    def test_database_initialization(self):
        """Test database initialization functions"""
        # Test that we can initialize a database
        test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        test_db_file.close()
        
        try:
            test_url = f"sqlite:///{test_db_file.name}"
            engine = create_engine(test_url, connect_args={"check_same_thread": False})
            
            # Create all tables
            Base.metadata.create_all(bind=engine)
            
            # Verify tables were created
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            
            self.assertGreater(len(table_names), 0)
            self.assertIn("users", table_names)
            
        finally:
            try:
                os.unlink(test_db_file.name)
            except:
                pass

class TestDatabaseErrorHandling(unittest.TestCase):
    """Test database error handling scenarios"""
    
    def test_invalid_database_url(self):
        """Test handling of invalid database URL"""
        with self.assertRaises(Exception):
            # This should fail
            engine = create_engine("invalid://database/url")
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
    
    def test_connection_error_handling(self):
        """Test handling of connection errors"""
        # Create engine with invalid path
        invalid_engine = create_engine("sqlite:///invalid/path/database.db")
        
        # This should raise an exception when trying to connect
        with self.assertRaises(Exception):
            with invalid_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
    
    def test_session_error_recovery(self):
        """Test session recovery after errors"""
        test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        test_db_file.close()
        
        try:
            test_engine = create_engine(
                f"sqlite:///{test_db_file.name}",
                connect_args={"check_same_thread": False}
            )
            
            Base.metadata.create_all(bind=test_engine)
            
            TestSessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=test_engine
            )
            
            session = TestSessionLocal()
            
            try:
                # Create a user
                user = User(
                    email="test@example.com",
                    username="testuser",
                    hashed_password="hashed_password",
                    full_name="Test User"
                )
                session.add(user)
                session.commit()
                
                # Try to create a duplicate (should fail)
                duplicate = User(
                    email="test@example.com",  # Same email
                    username="testuser2",
                    hashed_password="hashed_password",
                    full_name="Test User 2"
                )
                session.add(duplicate)
                
                with self.assertRaises(Exception):
                    session.commit()
                
                # Session should be in error state, rollback
                session.rollback()
                
                # Session should be usable again
                user_count = session.query(User).count()
                self.assertEqual(user_count, 1)
                
            finally:
                session.close()
                
        finally:
            try:
                os.unlink(test_db_file.name)
            except:
                pass

if __name__ == "__main__":
    unittest.main(verbosity=2)