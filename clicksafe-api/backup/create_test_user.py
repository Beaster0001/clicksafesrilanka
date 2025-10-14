#!/usr/bin/env python3

from database import get_db
from models import User
from auth import get_password_hash

def create_test_user():
    db = next(get_db())
    
    print("=== CREATING FRESH TEST USER ===")
    
    # Use existing user heshanrashmika809@gmail.com
    test_user = db.query(User).filter(User.email == "heshanrashmika809@gmail.com").first()
    
    if test_user:
        # Reset password
        test_user.hashed_password = get_password_hash("testpass123")
        db.commit()
        print(f"Password reset for {test_user.email} to 'testpass123'")
        print(f"User ID: {test_user.id}")
    else:
        print("User not found. Available users:")
        users = db.query(User).all()
        for user in users:
            print(f"  - {user.email}")
    
    db.close()

if __name__ == "__main__":
    create_test_user()