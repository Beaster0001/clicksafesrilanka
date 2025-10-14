"""
Update admin user credentials
"""
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import get_password_hash

def update_admin_user():
    """Update admin user credentials"""
    db = next(get_db())
    
    try:
        # Find the admin user
        admin_user = db.query(User).filter(User.email == "admin@clicksafe.com").first()
        
        if admin_user:
            # Update admin credentials
            admin_user.username = "admin"
            admin_user.hashed_password = get_password_hash("Password@123")
            
            db.commit()
            
            print("✅ Admin user updated successfully!")
            print("📧 Email: admin@clicksafe.com")
            print("👤 Username: admin")
            print("🔐 Password: Password@123")
        else:
            print("❌ Admin user not found")
    
    except Exception as e:
        print(f"❌ Error updating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_admin_user()