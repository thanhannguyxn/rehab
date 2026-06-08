# Database connection and configuration
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from settings import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


DEFAULT_EXERCISES = [
    {
        "id": "squat",
        "name": "Squat (Gập gối)",
        "description": "Bài tập tăng cường cơ chân và khớp gối",
        "target_reps": 16,
        "duration_seconds": 600,
        "down_threshold": 160.0,
        "up_threshold": 90.0,
        "hysteresis": 5.0,
        "difficulty_level": "medium",
        "primary_muscle_group": "legs",
        "video_path": "/squat.mp4",
    },
    {
        "id": "arm_raise",
        "name": "Nâng Tay",
        "description": "Bài tập tăng cường cơ vai và tay",
        "target_reps": 12,
        "duration_seconds": 300,
        "down_threshold": 90.0,
        "up_threshold": 160.0,
        "hysteresis": 5.0,
        "difficulty_level": "easy",
        "primary_muscle_group": "shoulders",
        "video_path": "/arm_raise.mp4",
    },
    {
        "id": "calf_raise",
        "name": "Nâng Gót Chân",
        "description": "Bài tập tăng cường cơ bắp chân",
        "target_reps": 12,
        "duration_seconds": 300,
        "down_threshold": 120.0,
        "up_threshold": 140.0,
        "hysteresis": 5.0,
        "difficulty_level": "easy",
        "primary_muscle_group": "calves",
        "video_path": "/calf_raise.mp4",
    },
    {
        "id": "single_leg_stand",
        "name": "Đứng 1 Chân",
        "description": "Bài tập cân bằng và tăng cường cơ chân",
        "target_reps": 10,
        "duration_seconds": 300,
        "down_threshold": None,
        "up_threshold": None,
        "hysteresis": 5.0,
        "difficulty_level": "medium",
        "primary_muscle_group": "legs",
        "video_path": "/single_leg_stand.mp4",
    },
]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables"""
    from models.base import Base
    Base.metadata.create_all(bind=engine)


def migrate_db():
    """Idempotent column migrations for existing tables."""
    from sqlalchemy import inspect, text
    inspector = inspect(engine)

    existing_cols = {col['name'] for col in inspector.get_columns('users')}
    with engine.connect() as conn:
        if 'email' not in existing_cols:
            conn.execute(text('ALTER TABLE users ADD COLUMN email VARCHAR(255) NULL'))
            conn.commit()
        if 'password_changed' not in existing_cols:
            conn.execute(text('ALTER TABLE users ADD COLUMN password_changed TINYINT(1) NOT NULL DEFAULT 1'))
            conn.commit()

    from models.session import ProgressionSuggestion
    from models.exercise import PatientExerciseAssignment
    ProgressionSuggestion.__table__.create(bind=engine, checkfirst=True)
    PatientExerciseAssignment.__table__.create(bind=engine, checkfirst=True)


def ensure_default_exercises(db):
    """Ensure built-in exercises exist without removing custom exercises."""
    from datetime import datetime
    from models import Exercise

    now = datetime.utcnow()

    for payload in DEFAULT_EXERCISES:
        exercise = db.query(Exercise).filter(Exercise.id == payload["id"]).first()

        if exercise is None:
            db.add(
                Exercise(
                    **payload,
                    is_default=True,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
            )
            continue

        # Keep existing customizations but make sure built-in exercises remain visible.
        exercise.is_default = True
        exercise.is_active = True
        exercise.updated_at = now

        if not exercise.name:
            exercise.name = payload["name"]
        if not exercise.description:
            exercise.description = payload["description"]
        if not exercise.video_path:
            exercise.video_path = payload["video_path"]

def init_db():
    """Initialize database with default data"""
    from models import User, UserRole, Gender, MobilityLevel, hash_password

    create_tables()

    db = SessionLocal()
    try:
        # Ensure default doctor exists.
        doctor = db.query(User).filter(User.username == "doctor1").first()
        if not doctor:
            doctor = User(
                username="doctor1",
                password_hash=hash_password("doctor123"),
                role=UserRole.doctor,
                full_name="BS. Nguyen Van A",
                created_at=datetime.utcnow()
            )
            db.add(doctor)
            db.flush()

        # Second doctor account for testing the new auth flow.
        doctor2 = db.query(User).filter(User.username == "doctor2").first()
        if not doctor2:
            doctor2 = User(
                username="doctor2",
                password_hash=hash_password("Doctor@2024"),
                role=UserRole.doctor,
                full_name="BS. Le Thi D",
                created_at=datetime.utcnow()
            )
            db.add(doctor2)
            db.flush()

        # Ensure default demo patients exist.
        default_patients = [
            ("patient1", "patient123", "Tran Thi B", 65, Gender.female),
            ("patient2", "patient123", "Le Van C", 70, Gender.male),
            ("patient3", "Patient@2024", "Pham Van D", 55, Gender.male),
        ]

        for username, password, name, age, gender in default_patients:
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                continue

            patient = User(
                username=username,
                password_hash=hash_password(password),
                role=UserRole.patient,
                full_name=name,
                age=age,
                gender=gender,
                height_cm=165.0,
                weight_kg=62.0,
                bmi=22.8,
                medical_conditions="[]",
                injury_type="knee_pain",
                mobility_level=MobilityLevel.beginner,
                pain_level=3,
                created_at=datetime.utcnow(),
                doctor_id=doctor.id
            )
            db.add(patient)

        ensure_default_exercises(db)

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()