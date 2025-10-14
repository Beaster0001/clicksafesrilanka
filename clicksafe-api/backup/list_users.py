from database import SessionLocal
from models import User

def list_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if users:
            print(f"Found {len(users)} users in database:")
            print("-" * 50)
            for user in users:
                print(f"Email: {user.email}")
                print(f"Username: {user.username}")
                print(f"Full name: {user.full_name}")
                print(f"Created: {user.created_at}")
                print("-" * 30)
        else:
            print('No users found in database')
    finally:
        db.close()

if __name__ == "__main__":
    list_users()