"""
Database Management Tool for Rehab System V3
Easy-to-use CLI interface for managing database with SQLAlchemy
"""

from sqlalchemy.orm import Session
from models import User, Session as DBSession, SessionError, SessionFrame, UserExerciseLimits, get_db, engine, Base
from sqlalchemy import text
import sys
from pathlib import Path
from datetime import datetime
import os
import subprocess

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def connect_db():
    """Get SQLAlchemy session"""
    return next(get_db())

def view_all_tables():
    """Show all tables in database"""
    db = connect_db()
    try:
        print_header(" All Tables in Database")
        # Use raw SQL to get table info
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'rehab_v3' ORDER BY table_name"))
        tables = result.fetchall()

        for i, (table_name,) in enumerate(tables, 1):
            # Count rows in each table
            count_result = db.execute(text(f"SELECT COUNT(*) FROM `{table_name}`"))
            count = count_result.fetchone()[0]
            print(f"  {i}. {table_name:<30} ({count} rows)")
    finally:
        db.close()
    input("\n Press Enter to continue...")

def view_users():
    """Show all users"""
    db = connect_db()
    try:
        print_header(" All Users")
        users = db.query(User).order_by(User.role, User.id).all()

        print(f"{'ID':<5} {'Username':<15} {'Role':<10} {'Full Name':<25} {'Age':<5} {'Gender':<10} {'Created':<20}")
        print("-" * 100)

        for user in users:
            age_str = str(user.age) if user.age else 'N/A'
            gender_str = user.gender.value if user.gender else 'N/A'
            created_str = user.created_at.strftime('%Y-%m-%d') if user.created_at else 'N/A'
            print(f"{user.id:<5} {user.username:<15} {user.role.value:<10} {user.full_name or 'N/A':<25} {age_str:<5} {gender_str:<10} {created_str:<20}")
    finally:
        db.close()
    input("\n Press Enter to continue...")

def view_sessions():
    """View recent sessions"""
    db = connect_db()
    try:
        print_header(" Recent Sessions (Last 20)")
        sessions = db.query(DBSession).join(User, DBSession.patient_id == User.id).order_by(DBSession.id.desc()).limit(20).all()

        print(f"{'ID':<5} {'User':<15} {'Name':<20} {'Exercise':<20} {'Date':<12} {'Reps':<8} {'Correct':<8} {'Acc%':<6} {'Duration':<8}")
        print("-" * 120)

        for session in sessions:
            date_str = session.start_time.strftime('%Y-%m-%d') if session.start_time else 'N/A'
            name_str = (session.patient.full_name or session.patient.username)[:18]
            ex_str = session.exercise_name[:18]
            duration_min = f"{session.duration_seconds//60}m" if session.duration_seconds else '0m'
            print(f"{session.id:<5} {session.patient.username:<15} {name_str:<20} {ex_str:<20} {date_str:<12} {session.total_reps:<8} {session.correct_reps:<8} {session.accuracy:<6.1f} {duration_min:<8}")
    finally:
        db.close()
    input("\n Press Enter to continue...")

def delete_user():
    """Delete a user and all their data"""
    db = connect_db()
    try:
        print_header(" Delete User")
        user_id = input(" Enter user ID to delete: ").strip()

        if not user_id.isdigit():
            print(" Invalid user ID")
            return

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            print(" User not found")
            return

        confirm = input(f" Delete user '{user.username}' ({user.full_name})? This will delete ALL their sessions and data! (y/N): ").strip().lower()
        if confirm != 'y':
            print(" Cancelled")
            return

        # Delete user's sessions and related data
        sessions = db.query(DBSession).filter(DBSession.patient_id == user.id).all()
        for session in sessions:
            db.query(SessionError).filter(SessionError.session_id == session.id).delete()
            db.query(SessionFrame).filter(SessionFrame.session_id == session.id).delete()
            db.delete(session)

        # Delete exercise limits
        db.query(UserExerciseLimits).filter(UserExerciseLimits.user_id == user.id).delete()

        # Delete user
        db.delete(user)
        db.commit()

        print(f" User '{user.username}' and all associated data deleted successfully")
    except Exception as e:
        db.rollback()
        print(f" Error deleting user: {e}")
    finally:
        db.close()
    input("\n Press Enter to continue...")

def reset_database(force=False):
    """Reset the entire database"""
    if not force:
        print_header(" Reset Database")
        confirm = input(" This will DELETE ALL DATA! Are you sure? Type 'YES' to confirm: ").strip()
        if confirm != 'YES':
            print(" Cancelled")
            return

    try:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        # Recreate all tables
        Base.metadata.create_all(bind=engine)

        # Initialize with default data
        from models import init_db
        init_db()

        print(" Database reset successfully")
    except Exception as e:
        print(f" Error resetting database: {e}")

    if not force:
        input("\n Press Enter to continue...")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_database(force=True)
        return

    while True:
        clear_screen()
        print_header(" Rehab System V3 - Database Manager")
        print(" 1. View all tables")
        print(" 2. View all users")
        print(" 3. View recent sessions")
        print(" 4. Delete user")
        print(" 5. Reset database")
        print(" 0. Exit")
        print()

        choice = input(" Choose an option: ").strip()

        if choice == '1':
            view_all_tables()
        elif choice == '2':
            view_users()
        elif choice == '3':
            view_sessions()
        elif choice == '4':
            delete_user()
        elif choice == '5':
            reset_database()
        elif choice == '0':
            break
        else:
            print(" Invalid choice")
            input("\n Press Enter to continue...")

if __name__ == "__main__":
    main()