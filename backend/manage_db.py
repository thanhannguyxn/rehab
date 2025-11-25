"""
Database Management Tool for Rehab System V3
Easy-to-use CLI interface for managing SQLite database
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime
import os
import subprocess
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "rehab_v3"
}
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def connect_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f" Cannot connect to MySQL: {e}")
        sys.exit(1)

def view_all_tables():
    """Show all tables in database"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print_header(" All Tables in Database")
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s ORDER BY table_name", (DB_CONFIG['database'],))
    tables = cursor.fetchall()
    
    for i, (table_name,) in enumerate(tables, 1):
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        count = cursor.fetchone()[0]
        print(f"  {i}. {table_name:<30} ({count} rows)")
    
    cursor.close()
    conn.close()
    input("\n Press Enter to continue...")

def view_users():
    """View all users"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print_header(" All Users")
    cursor.execute("""
        SELECT id, username, role, full_name, age, gender, created_at 
        FROM users 
        ORDER BY role, id
    """)
    
    print(f"{'ID':<5} {'Username':<15} {'Role':<10} {'Full Name':<25} {'Age':<5} {'Gender':<10} {'Created':<20}")
    print("-" * 100)
    
    for row in cursor.fetchall():
        user_id, username, role, full_name, age, gender, created = row
        age_str = str(age) if age else 'N/A'
        gender_str = gender or 'N/A'
        created_str = created[:10] if created else 'N/A'
        print(f"{user_id:<5} {username:<15} {role:<10} {full_name or 'N/A':<25} {age_str:<5} {gender_str:<10} {created_str:<20}")
    cursor.close()
    conn.close()
    input("\n Press Enter to continue...")

def view_sessions():
    """View recent sessions"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print_header(" Recent Sessions (Last 20)")
    cursor.execute("""
        SELECT s.id, u.username, u.full_name, s.exercise_name, s.start_time, 
               s.total_reps, s.correct_reps, s.accuracy, s.duration_seconds
        FROM sessions s
        JOIN users u ON s.patient_id = u.id
        ORDER BY s.id DESC
        LIMIT 20
    """)
    
    print(f"{'ID':<5} {'User':<15} {'Name':<20} {'Exercise':<20} {'Date':<12} {'Reps':<8} {'Correct':<8} {'Acc%':<6} {'Duration':<8}")
    print("-" * 120)
    
    for row in cursor.fetchall():
        sid, username, full_name, exercise, start_time, total, correct, acc, duration = row
        date_str = start_time[:10] if start_time else 'N/A'
        name_str = (full_name or username)[:18]
        ex_str = exercise[:18]
        duration_min = f"{duration//60}m" if duration else '0m'
        print(f"{sid:<5} {username:<15} {name_str:<20} {ex_str:<20} {date_str:<12} {total:<8} {correct:<8} {acc:<6.1f} {duration_min:<8}")
    
    cursor.close()
    conn.close()
    input("\n Press Enter to continue...")

def view_session_errors():
    """View errors from sessions"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print_header(" Session Errors Summary")
    cursor.execute("""
        SELECT s.exercise_name, se.error_name, SUM(se.count) as total_count, COUNT(DISTINCT s.id) as session_count
        FROM session_errors se
        JOIN sessions s ON se.session_id = s.id
        GROUP BY s.exercise_name, se.error_name
        ORDER BY total_count DESC
        LIMIT 20
    """)
    
    print(f"{'Exercise':<30} {'Error Name':<30} {'Total Count':<15} {'Sessions':<10}")
    print("-" * 90)
    
    for row in cursor.fetchall():
        exercise, error, total, sessions = row
        print(f"{exercise:<30} {error:<30} {total:<15} {sessions:<10}")
    cursor.close()
    conn.close()
    input("\n Press Enter to continue...")

def delete_user():
    """Delete a user and all their sessions"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print_header(" Delete User")
    
    # Show users
    cursor.execute("SELECT id, username, role, full_name FROM users ORDER BY id")
    users = cursor.fetchall()
    
    print("Available users:")
    for user_id, username, role, full_name in users:
        print(f"  {user_id}. {username:<15} ({role}) - {full_name or 'N/A'}")
    
    try:
        user_id = input("\n Enter user ID to delete (or 0 to cancel): ").strip()
        if user_id == '0':
            print("Cancelled.")
            cursor.close()
            conn.close()
            input("\n Press Enter to continue...")
            return
        
        user_id = int(user_id)
        
        # Get user info
        cursor.execute("SELECT username, role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            print(f" User with ID {user_id} not found.")
            cursor.close()
            conn.close()
            input("\n Press Enter to continue...")
            return
        
        username, role = user
        
        # Confirm
        confirm = input(f"\n Delete user '{username}' ({role}) and ALL their data? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Cancelled.")
            cursor.close()

            conn.close()
            input("\n Press Enter to continue...")
            return
        
        # Delete sessions and errors first
        cursor.execute("DELETE FROM session_errors WHERE session_id IN (SELECT id FROM sessions WHERE patient_id = %s)", (user_id,))
        cursor.execute("DELETE FROM session_frames WHERE session_id IN (SELECT id FROM sessions WHERE patient_id = %s)", (user_id,))
        cursor.execute("DELETE FROM sessions WHERE patient_id = %s", (user_id,))
        cursor.execute("DELETE FROM user_exercise_limits WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        conn.commit()
        print(f" User '{username}' and all related data deleted successfully!")
        
    except ValueError:
        print(" Invalid input. Please enter a number.")
    except Exception as e:
        print(f" Error: {e}")
        conn.rollback()
    
    cursor.close()
    conn.close()
    input("\n Press Enter to continue...")

def delete_session():
    """Delete a specific session"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print_header(" Delete Session")
    
    # Show recent sessions
    cursor.execute("""
        SELECT s.id, u.username, s.exercise_name, s.start_time, s.total_reps, s.accuracy
        FROM sessions s
        JOIN users u ON s.patient_id = u.id
        ORDER BY s.id DESC
        LIMIT 20
    """)
    sessions = cursor.fetchall()
    
    print("Recent sessions:")
    print(f"{'ID':<5} {'User':<15} {'Exercise':<25} {'Date':<12} {'Reps':<8} {'Accuracy':<10}")
    print("-" * 80)
    for sid, username, exercise, start_time, reps, acc in sessions:
        date_str = start_time[:10] if start_time else 'N/A'
        print(f"{sid:<5} {username:<15} {exercise:<25} {date_str:<12} {reps:<8} {acc:<10.1f}%")
    
    try:
        session_id = input("\n Enter session ID to delete (or 0 to cancel): ").strip()
        if session_id == '0':
            print(" Cancelled.")
            cursor.close()
            conn.close()
            input("\n Press Enter to continue...")
            return
        
        session_id = int(session_id)
        
        # Confirm
        confirm = input(f"\n Delete session {session_id}? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print(" Cancelled.")
            cursor.close()
            conn.close()
            input("\n Press Enter to continue...")
            return
        
        # Delete
        cursor.execute("DELETE FROM session_errors WHERE session_id = %s", (session_id,))
        cursor.execute("DELETE FROM session_frames WHERE session_id = %s", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
        
        conn.commit()
        print(f" Session {session_id} deleted successfully!")
        
    except ValueError:
        print(" Invalid input. Please enter a number.")
    except Exception as e:
        print(f" Error: {e}")
        conn.rollback()
    
    cursor.close()
    conn.close()
    input("\n Press Enter to continue...")

def clear_all_sessions():
    """Delete all sessions but keep users"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print_header(" Clear All Sessions")
    
    # Get count
    cursor.execute("SELECT COUNT(*) FROM sessions")
    count = cursor.fetchone()[0]
    
    print(f" This will delete ALL {count} sessions and their related data.")
    print("   Users will NOT be deleted.")
    
    confirm = input("\n Type 'DELETE ALL' to confirm: ").strip()
    if confirm != 'DELETE ALL':
        print(" Cancelled.")
        cursor.close()
        conn.close()
        input("\n Press Enter to continue...")
        return
    
    try:
        cursor.execute("DELETE FROM session_errors")
        cursor.execute("DELETE FROM session_frames")
        cursor.execute("DELETE FROM sessions")
        conn.commit()
        print(f" All {count} sessions deleted successfully!")
    except Exception as e:
        print(f" Error: {e}")
        conn.rollback()
    
    cursor.close()
    conn.close()
    input("\n Press Enter to continue...")

def backup_database():
    """Create a backup of the database"""
    print_header(" Backup Database")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"rehab_v3_backup_{timestamp}.sql"
    
    host = DB_CONFIG['host']
    user = DB_CONFIG['user']
    password = DB_CONFIG['ducanh']
    database = DB_CONFIG['database']
    
    # Try mysqldump
    cmd = f'mysqldump -h {host} -u {user} -p{password} {database} > "{backup_path}"'
    try:
        res = subprocess.run(cmd, shell=True)
        if res.returncode == 0:
            size_kb = Path(backup_path).stat().st_size / 1024
            print(f" Backup created: {backup_path}")
            print(f"   Size: {size_kb:.2f} KB")
        else:
            print(" mysqldump failed or not available. Ensure mysqldump is in PATH.")
    except Exception as e:
        print(f" Backup failed: {e}")
    
    input("\n Press Enter to continue...")

def show_database_stats():
    """Show database statistics"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print_header(" Database Statistics")
    
    # Users
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='patient'")
    patient_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='doctor'")
    doctor_count = cursor.fetchone()[0]
    
    # Sessions
    cursor.execute("SELECT COUNT(*) FROM sessions")
    session_count = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(total_reps) FROM sessions")
    total_reps = cursor.fetchone()[0] or 0
    cursor.execute("SELECT AVG(accuracy) FROM sessions")
    avg_accuracy = cursor.fetchone()[0] or 0.0
    
    # Errors
    cursor.execute("SELECT COUNT(*) FROM session_errors")
    error_count = cursor.fetchone()[0]
    
     # Database size in KB (data + index)
    cursor.execute("""
        SELECT IFNULL(SUM(data_length + index_length) / 1024, 0)
        FROM information_schema.TABLES
        WHERE table_schema = %s
    """, (DB_CONFIG['database'],))
    db_size = cursor.fetchone()[0] or 0.0
    
    print(f" Users:")
    print(f"   - Patients: {patient_count}")
    print(f"   - Doctors: {doctor_count}")
    print(f"   - Total: {patient_count + doctor_count}")
    
    print(f"\n Sessions:")
    print(f"   - Total sessions: {session_count}")
    print(f"   - Total reps: {total_reps}")
    print(f"   - Average accuracy: {avg_accuracy:.1f}%")
    
    print(f"\n Errors:")
    print(f"   - Total error records: {error_count}")
    
    print(f"\n Database: {DB_CONFIG['database']}")
    print(f"   - Size: {db_size:.2f} KB")
    
    cursor.close()
    conn.close()
    input("\n Press Enter to continue...")

def execute_custom_query():
    """Execute custom SQL query"""
    print_header(" Execute Custom SQL Query")
    
    print(" Be careful! This allows direct SQL execution.")
    print("   Examples:")
    print("   - SELECT * FROM users LIMIT 5")
    print("   - UPDATE users SET age=70 WHERE id=1")
    print("   - DELETE FROM sessions WHERE accuracy < 50")
    
    query = input("\n Enter SQL query (or 'cancel' to exit): ").strip()
    
    if query.lower() == 'cancel':
        return
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            # Show results
            results = cursor.fetchall()
            if results:
                print(f"\n Found {len(results)} rows:")
                for i, row in enumerate(results[:20], 1):  # Limit to 20 rows
                    print(f"   {i}. {row}")
                if len(results) > 20:
                    print(f"   ... and {len(results) - 20} more rows")
            else:
                print(" Query executed, no results returned.")
        else:
            # Commit changes
            conn.commit()
            print(f" Query executed successfully!")
            print(f"   Rows affected: {cursor.rowcount}")
    
    except Exception as e:
        print(f" Error: {e}")
        conn.rollback()
    
    cursor.close()
    conn.close()
    input("\n Press Enter to continue...")

def main_menu():
    while True:
        clear_screen()
        print_header(" Rehab System V3 - Database Management Tool")
        
        print(" VIEW DATA:")
        print("  1. View all tables")
        print("  2. View users")
        print("  3. View sessions")
        print("  4. View session errors")
        print("  5. Show database statistics")
        
        print("\n DELETE DATA:")
        print("  6. Delete a user")
        print("  7. Delete a session")
        print("  8. Clear all sessions (keep users)")
        
        print("\n ADVANCED:")
        print("  9. Execute custom SQL query")
        print("  10. Backup database")
        
        print("\n  0. Exit")
        
        choice = input("\n Select option: ").strip()
        
        if choice == '0':
            print("\n Goodbye!")
            break
        elif choice == '1':
            view_all_tables()
        elif choice == '2':
            view_users()
        elif choice == '3':
            view_sessions()
        elif choice == '4':
            view_session_errors()
        elif choice == '5':
            show_database_stats()
        elif choice == '6':
            delete_user()
        elif choice == '7':
            delete_session()
        elif choice == '8':
            clear_all_sessions()
        elif choice == '9':
            execute_custom_query()
        elif choice == '10':
            backup_database()
        else:
            print(" Invalid option. Please try again.")
            input("\n Press Enter to continue...")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n Interrupted. Goodbye!")
        sys.exit(0)
