"""
Database migration script to add new profile fields to users table
"""
import sqlite3
import os

def run_migration():
    """Add new profile fields to users table"""
    
    # Get database path
    db_path = os.path.join(os.path.dirname(__file__), 'clicksafe.db')
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add new columns if they don't exist
        new_columns = [
            ('phone', 'VARCHAR(20)'),
            ('location', 'VARCHAR(255)'),
            ('bio', 'TEXT'),
            ('website', 'VARCHAR(500)')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in columns:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                print(f"Added column: {column_name}")
            else:
                print(f"Column {column_name} already exists")
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    run_migration()