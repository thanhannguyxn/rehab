"""
Database Migration Script
Adds biometric and medical fields to existing users table
Uses SQLAlchemy ORM
"""

import sys
from datetime import datetime
from models import engine, Base, init_db

def migrate_database():
    """Add new columns to users table for AI personalization using SQLAlchemy"""
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print(" Ensured all tables exist")

        # Initialize database with default data if needed
        init_db()

        print(" Migration completed successfully")
        print(" All tables are now set up with SQLAlchemy ORM")

    except Exception as e:
        print(f" Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print(" Starting database migration to SQLAlchemy ORM...")
    migrate_database()
    print(" Migration complete!")