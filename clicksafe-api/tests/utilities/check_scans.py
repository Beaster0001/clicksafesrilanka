#!/usr/bin/env python3

from database import get_db
from models import UserScan, User

def check_database():
    db = next(get_db())
    
    print("=== DATABASE CHECK ===")
    
    # Check users
    users = db.query(User).all()
    print(f"\nUsers ({len(users)}):")
    for user in users:
        print(f"  - {user.email} (ID: {user.id})")
    
    # Check all scans
    all_scans = db.query(UserScan).all()
    print(f"\nAll UserScan records ({len(all_scans)}):")
    
    # Group by scan type
    qr_scans = db.query(UserScan).filter(UserScan.scan_type == 'qr_code').all()
    url_scans = db.query(UserScan).filter(UserScan.scan_type == 'url').all()
    
    print(f"  - QR Code scans: {len(qr_scans)}")
    print(f"  - URL scans: {len(url_scans)}")
    
    if all_scans:
        print(f"\nRecent scans:")
        recent_scans = db.query(UserScan).order_by(UserScan.created_at.desc()).limit(5).all()
        for scan in recent_scans:
            content_preview = scan.content[:50] + "..." if len(scan.content) > 50 else scan.content
            print(f"  - User {scan.user_id}: {scan.scan_type} - {content_preview} ({scan.classification}) - {scan.created_at}")
    else:
        print("  No scans found!")
    
    db.close()

if __name__ == "__main__":
    check_database()