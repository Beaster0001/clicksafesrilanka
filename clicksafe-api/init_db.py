"""
Database initialization and admin user creation script
"""
from sqlalchemy.orm import Session
from database import get_db, create_tables
from models import User
from auth import get_password_hash
import os

def create_admin_user():
    """Create default admin user if it doesn't exist"""
    db = next(get_db())
    
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.email == "admin@clicksafe.com").first()
        
        if not admin_user:
            # Create admin user
            admin_user = User(
                email="admin@clicksafe.com",
                username="admin",
                full_name="System Administrator",
                hashed_password=get_password_hash("Password@123"),  # Updated admin password
                is_admin=True,
                is_active=True
            )
            
            db.add(admin_user)
            db.commit()
            
            print("✅ Admin user created successfully!")
            print("📧 Email: admin@clicksafe.com")
            print("� Username: admin") 
            print("�🔐 Password: Password@123")
            print("⚠️  Please change the admin password after first login!")
        else:
            print("ℹ️  Admin user already exists")
    
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def init_database():
    """Initialize database with tables and admin user"""
    print("🔧 Initializing database...")
    
    # Create tables
    create_tables()
    print("✅ Database tables created")
    
    # Create admin user
    create_admin_user()
    
    print("🎉 Database initialization complete!")

if __name__ == "__main__":
    init_database()