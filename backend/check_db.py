from sqlalchemy.orm import Session
from models import Session as DBSession, SessionError, get_db

# Using SQLAlchemy
def check_db_sqlalchemy():
    db = next(get_db())
    try:
        # Get last 5 sessions
        sessions = db.query(DBSession).order_by(DBSession.id.desc()).limit(5).all()
        print('\n Last 5 sessions in database (SQLAlchemy):')
        print('-' * 80)
        for session in sessions:
            print(f'  ID={session.id:<3} Exercise={session.exercise_name:<20} Total={session.total_reps:<3} Correct={session.correct_reps:<3} Accuracy={session.accuracy:.1f}%')

        print('\n Checking session errors (SQLAlchemy):')
        # Get errors for last 3 sessions
        session_ids = [s.id for s in sessions[:3]]
        for session_id in session_ids:
            session = db.query(DBSession).filter(DBSession.id == session_id).first()
            errors = db.query(SessionError).filter(SessionError.session_id == session_id).all()
            error_str = ', '.join([f"{e.error_name}({e.count})" for e in errors]) if errors else "None"
            print(f'  ID={session.id}: {session.exercise_name} - {session.total_reps} reps - Errors: {error_str}')
    finally:
        db.close()

if __name__ == "__main__":
    check_db_sqlalchemy()
