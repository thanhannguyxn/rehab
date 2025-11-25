"""
Database Migration Script
Adds biometric and medical fields to existing users table
"""

import sys
from datetime import datetime
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "rehab_v3"
}
def migrate_database():
    """Add new columns to users table for AI personalization"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
    except Error as e:
        print(f" Cannot connect to MySQL: {e}")
        sys.exit(1)

    # Check if 'users' table exists
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = %s AND table_name = 'users'
    """, (DB_CONFIG['database'],))
    users_table_exists = cursor.fetchone()[0] > 0
    if not users_table_exists:
        print(" 'users' table not found — creating a minimal 'users' table.")
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(32) NOT NULL CHECK(role IN ('patient', 'doctor')),
                full_name VARCHAR(255),
                age INT,
                gender VARCHAR(16) CHECK(gender IN ('male', 'female', 'other')),
                height_cm REAL,
                weight_kg REAL,
                bmi REAL,
                medical_conditions TEXT,
                injury_type TEXT,
                mobility_level VARCHAR(32) CHECK(mobility_level IN ('beginner', 'intermediate', 'advanced')),
                pain_level INT CHECK(pain_level BETWEEN 0 AND 10),
                doctor_notes TEXT,
                contraindicated_exercises TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                doctor_id INT,
                FOREIGN KEY (doctor_id) REFERENCES users(id)
            )
        """)
            print(" Created 'users' table.")
        except Error as e:
            print(f" Failed to create 'users' table: {e}")
            cursor.close()
            conn.close()
            sys.exit(1)

    # Get current columns
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
    """, (DB_CONFIG['database'], 'users'))
    existing_columns = {row[0] for row in cursor.fetchall()}
    print(f"Existing columns: {sorted(existing_columns)}")
    
    # Add new columns if they don't exist
    new_columns = [
        ("height_cm", "DOUBLE"),
        ("weight_kg", "DOUBLE"),
        ("bmi", "DOUBLE"),
        ("medical_conditions", "TEXT"),
        ("injury_type", "TEXT"),
        ("mobility_level", "VARCHAR(32)"),
        ("pain_level", "INT"),
        ("doctor_notes", "TEXT"),
        ("contraindicated_exercises", "TEXT"),
    ]
    
    for column_name, column_type in new_columns:
        if column_name in existing_columns:
            print(f"  - Skipping existing column: {column_name}")
            continue
        try:
            # MySQL 8+ supports ADD COLUMN IF NOT EXISTS; using it for safety
            sql = f"ALTER TABLE `users` ADD COLUMN IF NOT EXISTS `{column_name}` {column_type}"
            cursor.execute(sql)
            print(f" Added column: {column_name} ({column_type})")
        except Error as e:
            print(f" Failed to add column {column_name}: {e}")
    
    # Create user_exercise_limits table if not exists
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_exercise_limits (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                exercise_type VARCHAR(64) NOT NULL,
                max_depth_angle DOUBLE,
                min_raise_angle DOUBLE,
                max_reps_per_set INT,
                recommended_rest_seconds INT,
                difficulty_score DOUBLE,
                injury_risk_score DOUBLE,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                CONSTRAINT fk_uel_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE KEY ux_user_exercise (user_id, exercise_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print(" Created/verified user_exercise_limits table")
    except Error as e:
        print(f" Failed to create/verify user_exercise_limits table: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n Database migration completed successfully!")

if __name__ == "__main__":
    print("=" * 60)
    print(" Running Database Migration")
    print("=" * 60)
    migrate_database()
