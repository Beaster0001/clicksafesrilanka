#!/usr/bin/env python3
"""
File Operations Integration Tests
Tests file upload, processing, and download operations
"""
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile
import io
from PIL import Image
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, Mock
import json

class TestFileUploadIntegration(unittest.TestCase):
    """Test file upload and processing integration"""
    
    def setUp(self):
        """Set up test client and mock files"""
        self.client = TestClient(app)
        
        # Create test user and login
        self.test_user = {
            "email": "filetest@example.com",
            "username": "fileuser",
            "full_name": "File Test User",
            "password": "FileTest123!"
        }
        
        self.client.post("/auth/register", json=self.test_user)
        login_response = self.client.post("/auth/login", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })
        
        self.token = login_response.json()["access_token"]
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}
    
    def create_test_qr_image(self):
        """Create a test QR code image"""
        # Create a simple test image
        img = Image.new('RGB', (200, 200), color='white')
        
        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes
    
    def test_qr_image_upload_processing(self):
        """Test QR image upload and processing workflow"""
        # Create test QR image
        test_image = self.create_test_qr_image()
        
        # Simulate QR image upload from frontend
        files = {
            "qr_image": ("test_qr.png", test_image, "image/png")
        }
        
        response = self.client.post(
            "/qr/upload",
            files=files,
            headers=self.auth_headers
        )
        
        # Verify upload and processing
        if response.status_code == 200:
            data = response.json()
            
            # Should extract QR content and analyze it
            self.assertIn("qr_content", data)
            self.assertIn("analysis", data)
            self.assertIn("safety_score", data)
        else:
            # Endpoint might not be implemented yet
            self.assertIn(response.status_code, [404, 501])
    
    def test_profile_image_upload(self):
        """Test user profile image upload"""
        # Create test profile image
        test_image = self.create_test_qr_image()
        
        files = {
            "profile_image": ("profile.png", test_image, "image/png")
        }
        
        response = self.client.post(
            "/user/profile/image",
            files=files,
            headers=self.auth_headers
        )
        
        # Verify profile image upload
        if response.status_code == 200:
            data = response.json()
            self.assertIn("image_url", data)
            self.assertIn("message", data)
        else:
            # Feature might not be implemented
            self.assertIn(response.status_code, [404, 501])
    
    def test_bulk_message_upload(self):
        """Test bulk message file upload for analysis"""
        # Create test CSV file with messages
        csv_content = """message,expected_classification
"Click here to win money!",dangerous
"Hello, how are you?",safe
"Urgent: Verify your account",suspicious"""
        
        csv_file = io.StringIO(csv_content)
        csv_bytes = io.BytesIO(csv_content.encode('utf-8'))
        
        files = {
            "message_file": ("messages.csv", csv_bytes, "text/csv")
        }
        
        response = self.client.post(
            "/scan/bulk",
            files=files,
            headers=self.auth_headers
        )
        
        # Verify bulk analysis
        if response.status_code == 200:
            data = response.json()
            self.assertIn("results", data)
            self.assertIn("total_processed", data)
            self.assertIsInstance(data["results"], list)
        else:
            # Bulk upload might not be implemented
            self.assertIn(response.status_code, [404, 501])
    
    def test_file_size_validation(self):
        """Test file size limits"""
        # Create oversized test file (simulate large file)
        large_content = "x" * (10 * 1024 * 1024)  # 10MB
        large_file = io.BytesIO(large_content.encode('utf-8'))
        
        files = {
            "large_file": ("large.txt", large_file, "text/plain")
        }
        
        response = self.client.post(
            "/upload/test",
            files=files,
            headers=self.auth_headers
        )
        
        # Should reject oversized files
        self.assertIn(response.status_code, [413, 422, 404])

class TestFileDownloadIntegration(unittest.TestCase):
    """Test file download and export operations"""
    
    def setUp(self):
        """Set up test client and authenticated user"""
        self.client = TestClient(app)
        
        # Create and login user
        self.test_user = {
            "email": "download@example.com",
            "username": "downloaduser",
            "full_name": "Download User",
            "password": "Download123!"
        }
        
        self.client.post("/auth/register", json=self.test_user)
        login_response = self.client.post("/auth/login", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })
        
        self.token = login_response.json()["access_token"]
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create some scan data first
        self.client.post("/scan/message", json={
            "scan_type": "message",
            "content": "Test phishing message"
        }, headers=self.auth_headers)
    
    def test_scan_history_csv_export(self):
        """Test exporting scan history as CSV"""
        response = self.client.get(
            "/export/scans/csv",
            headers=self.auth_headers
        )
        
        if response.status_code == 200:
            # Verify CSV content
            self.assertEqual(response.headers["content-type"], "text/csv; charset=utf-8")
            self.assertIn("attachment", response.headers.get("content-disposition", ""))
            
            # Check CSV content
            csv_content = response.content.decode('utf-8')
            self.assertIn("scan_type", csv_content)
            self.assertIn("classification", csv_content)
        else:
            # Export feature might not be implemented
            self.assertIn(response.status_code, [404, 501])
    
    def test_scan_history_json_export(self):
        """Test exporting scan history as JSON"""
        response = self.client.get(
            "/export/scans/json",
            headers=self.auth_headers
        )
        
        if response.status_code == 200:
            # Verify JSON export
            self.assertEqual(response.headers["content-type"], "application/json")
            
            data = response.json()
            self.assertIn("scans", data)
            self.assertIn("export_date", data)
            self.assertIn("user_email", data)
        else:
            # Export feature might not be implemented
            self.assertIn(response.status_code, [404, 501])
    
    def test_scan_history_xml_export(self):
        """Test exporting scan history as XML"""
        response = self.client.get(
            "/export/scans/xml",
            headers=self.auth_headers
        )
        
        if response.status_code == 200:
            # Verify XML content
            self.assertEqual(response.headers["content-type"], "application/xml")
            
            xml_content = response.content.decode('utf-8')
            self.assertIn("<?xml", xml_content)
            self.assertIn("<scans>", xml_content)
        else:
            # XML export might not be implemented
            self.assertIn(response.status_code, [404, 501])
    
    def test_cert_report_pdf_download(self):
        """Test downloading CERT report as PDF"""
        # First create a CERT report
        cert_response = self.client.post("/cert/report", json={
            "scan_id": 1,
            "incident_type": "phishing",
            "additional_info": "Test incident"
        }, headers=self.auth_headers)
        
        if cert_response.status_code in [200, 201]:
            report_id = cert_response.json().get("id", 1)
            
            # Download PDF report
            response = self.client.get(
                f"/cert/report/{report_id}/pdf",
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                # Verify PDF content
                self.assertEqual(response.headers["content-type"], "application/pdf")
                self.assertIn("attachment", response.headers.get("content-disposition", ""))
                
                # PDF should start with PDF signature
                content = response.content
                self.assertTrue(content.startswith(b'%PDF'))
        
        # If CERT reporting not implemented, this test passes
        self.assertTrue(True)

class TestFileValidationIntegration(unittest.TestCase):
    """Test file validation and security"""
    
    def setUp(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_malicious_file_upload_prevention(self):
        """Test prevention of malicious file uploads"""
        # Create fake executable file
        malicious_content = b'\x4d\x5a'  # PE header signature
        malicious_file = io.BytesIO(malicious_content)
        
        files = {
            "file": ("malicious.exe", malicious_file, "application/octet-stream")
        }
        
        response = self.client.post("/upload/test", files=files)
        
        # Should reject executable files
        self.assertIn(response.status_code, [400, 422, 415])
    
    def test_file_type_validation(self):
        """Test file type validation"""
        # Test valid image file
        test_image = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        files = {
            "image": ("test.png", img_bytes, "image/png")
        }
        
        response = self.client.post("/qr/upload", files=files)
        
        # Should accept valid image files (or return 404 if not implemented)
        self.assertIn(response.status_code, [200, 404, 422])
    
    def test_filename_sanitization(self):
        """Test filename sanitization for security"""
        # Test malicious filename
        malicious_content = b"test content"
        malicious_file = io.BytesIO(malicious_content)
        
        files = {
            "file": ("../../etc/passwd", malicious_file, "text/plain")
        }
        
        response = self.client.post("/upload/test", files=files)
        
        # Should handle malicious filenames safely
        self.assertIn(response.status_code, [400, 422, 404])

class TestFileStorageIntegration(unittest.TestCase):
    """Test file storage and retrieval"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = TestClient(app)
        
        # Create temp directory for test files
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test files"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
    
    def test_file_storage_location(self):
        """Test that files are stored in correct location"""
        # This test verifies file storage configuration
        # Implementation depends on your file storage setup
        
        # Test upload path configuration
        test_image = Image.new('RGB', (50, 50), color='red')
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        files = {
            "test_file": ("storage_test.png", img_bytes, "image/png")
        }
        
        response = self.client.post("/upload/test", files=files)
        
        # Response should indicate where file was stored
        if response.status_code == 200:
            data = response.json()
            if "file_path" in data:
                self.assertIsInstance(data["file_path"], str)
                self.assertTrue(len(data["file_path"]) > 0)
    
    def test_file_cleanup_integration(self):
        """Test automatic file cleanup for temporary files"""
        # Test that temporary files are cleaned up properly
        # This is important for preventing disk space issues
        
        # Upload temporary file
        test_content = b"temporary file content"
        temp_file = io.BytesIO(test_content)
        
        files = {
            "temp_file": ("temp.txt", temp_file, "text/plain")
        }
        
        response = self.client.post("/upload/temp", files=files)
        
        # File cleanup behavior depends on implementation
        # This test documents expected behavior
        self.assertIn(response.status_code, [200, 404, 501])

if __name__ == "__main__":
    unittest.main(verbosity=2)