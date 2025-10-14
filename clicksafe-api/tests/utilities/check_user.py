from database import SessionLocal
from models import User

def check_user():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == 'sanujan@gmail.com').first()
        if user:
            print(f'User found: {user.email}')
            print(f'Username: {user.username}')
            print(f'Full name: {user.full_name}')
            print(f'Created: {user.created_at}')
            print('Note: Password is hashed and cannot be displayed in plain text')
            print('If you need to reset the password, I can help with that.')
        else:
            print('User sanujan@gmail.com not found in database')
    finally:
        db.close()

if __name__ == "__main__":
    check_user()