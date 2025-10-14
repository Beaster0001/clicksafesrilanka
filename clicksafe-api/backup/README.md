# ClickSafe Backup Files

This directory contains files that are not essential for running the ClickSafe application in production. These files have been moved here to keep the main directory clean while preserving them for reference or potential future use.

## Categories of Backup Files

### 🔧 **Development Utilities**
- `cleanup_duplicates.py` - Script to clean duplicate messages from database
- `compare_data_formats.py` - Utility to compare different data formats
- `create_test_user.py` - Script to create test users for development
- `list_users.py` - Utility to list all users in the database
- `migrate_user_profile.py` - User profile migration script
- `update_admin.py` - Admin user update utility

### 📧 **Email Testing & Diagnostics**
- `diagnostic_email_test.py` - Email system diagnostic tests
- `direct_email_test.py` - Direct email sending tests
- `simple_email_test.py` - Basic email functionality tests
- `email_status_check.py` - Email service status verification

### 🛡️ **CERT Testing & Diagnostics**
- `cert_diagnostic.py` - CERT system diagnostic script
- `cert_diagnostic.html` - CERT diagnostic web interface
- `final_cert_test.py` - Final CERT functionality tests
- `quick_cert_test.py` - Quick CERT system tests
- `comprehensive_cert_fix.py` - CERT system comprehensive fixes

### 🔍 **QR Code Testing**
- `qr_cert_email_diagnostic.py` - QR-CERT email diagnostic
- `qr_cert_fix_test.html` - QR CERT fix testing interface
- `qr_cert_test.html` - QR CERT testing interface

### 📦 **Backup Services**
- `cert_email_service_backup.py` - Backup version of CERT email service

**Note**: `simple_detector.py` was initially moved here but restored to main directory as it's required by the application.

### 🧪 **Content Testing**
- `final_content_test.py` - Final content analysis tests

## Why These Files Were Moved

- **Clean Production Environment**: Main directory contains only essential files
- **Development History**: Preserve development utilities and test scripts
- **Reference**: Keep diagnostic and debugging tools for troubleshooting
- **Backup Safety**: Maintain backup versions of critical services

## Usage Notes

- These files can be moved back to main directory if needed for development
- Some utilities may require database access or specific environment setup
- Test files may need updating if database schema changes
- HTML files can be opened directly in browsers for diagnostic interfaces

## Restoration

To restore any file to the main directory:
```bash
# Example: Restore a utility file
cp backup/cleanup_duplicates.py ../

# Example: Restore diagnostic tools
cp backup/*diagnostic* ../
```

---
*Files moved on: October 8, 2025*  
*Total files in backup: 20*  
*Note: simple_detector.py was restored to main directory as it's required by the application*