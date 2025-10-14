#!/usr/bin/env python3

from database import get_db
from models import User
from auth import get_password_hash

def reset_test_password():
    db = next(get_db())
    
    print("=== RESETTING TEST USER PASSWORD ===")
    
    # Find test@gmail.com user
    test_user = db.query(User).filter(User.email == "test@gmail.com").first()
    
    if test_user:
        # Set password to "password123"
        new_password = "password123"
        test_user.password_hash = get_password_hash(new_password)
        db.commit()
        print(f"Password reset for {test_user.email} to '{new_password}'")
    else:
        print("test@gmail.com not found. Available users:")
        users = db.query(User).all()
        for user in users:
            print(f"  - {user.email}")
        
        # Use the first non-admin user
        if users:
            first_user = None
            for user in users:
                if user.email != "admin@clicksafe.com":
                    first_user = user
                    break
            
            if first_user:
                new_password = "password123"
                first_user.password_hash = get_password_hash(new_password)
                db.commit()
                print(f"Password reset for {first_user.email} to '{new_password}'")
    
    db.close()

if __name__ == "__main__":
    reset_test_password()