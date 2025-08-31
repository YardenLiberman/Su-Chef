#!/usr/bin/env python3
"""
Database migration script to add 'saved' field to existing recipes
"""
import sqlite3
import os

def migrate_database():
    db_path = 'su_chef_web.db'
    
    if not os.path.exists(db_path):
        print("Database file not found. Creating new database...")
        return
    
    print("Starting database migration...")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if 'saved' column already exists
        cursor.execute("PRAGMA table_info(recipe)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'saved' not in columns:
            print("Adding 'saved' column to recipe table...")
            cursor.execute("ALTER TABLE recipe ADD COLUMN saved BOOLEAN DEFAULT FALSE")
            
            # Set existing recipes as saved (to maintain backward compatibility)
            cursor.execute("UPDATE recipe SET saved = TRUE WHERE liked = TRUE OR cooked = TRUE")
            
            print("Migration completed successfully!")
        else:
            print("'saved' column already exists. No migration needed.")
        
        # Commit changes
        conn.commit()
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
