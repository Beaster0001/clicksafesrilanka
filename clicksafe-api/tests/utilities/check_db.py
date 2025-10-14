import sqlite3

conn = sqlite3.connect('clicksafe.db')
cursor = conn.cursor()

# Check table schema
cursor.execute('PRAGMA table_info(users)')
columns = cursor.fetchall()
print('Users table columns:')
for col in columns:
    print(f'{col[1]} ({col[2]})')

# Check user data
cursor.execute('SELECT id, email, full_name, phone, location, bio, website FROM users')
rows = cursor.fetchall()
print('\nUsers table data:')
for row in rows:
    print(f'ID: {row[0]}, Email: {row[1]}, Name: {row[2]}, Phone: {row[3]}, Location: {row[4]}, Bio: {row[5]}, Website: {row[6]}')

conn.close()