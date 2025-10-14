import sqlite3

conn = sqlite3.connect('clicksafe.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [table[0] for table in cursor.fetchall()]
print('Available tables:', tables)

# Check if recent_scams table exists
if 'recent_scams' in tables:
    print('\nRecent scams table exists!')
    cursor.execute("SELECT COUNT(*) FROM recent_scams")
    count = cursor.fetchone()[0]
    print(f'Number of records in recent_scams: {count}')
    
    if count > 0:
        cursor.execute("SELECT * FROM recent_scams LIMIT 3")
        records = cursor.fetchall()
        print('Sample records:')
        for record in records:
            print(record)
else:
    print('\nRecent scams table does NOT exist!')

conn.close()