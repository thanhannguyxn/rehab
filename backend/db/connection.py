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

        # Ensure default demo patients exist.
        default_patients = [
            ("patient1", "patient123", "Tran Thi B", 65, Gender.female),
            ("patient2", "patient123", "Le Van C", 70, Gender.male),
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
                height_cm=160.0,
                weight_kg=58.0,
                bmi=22.7,
                medical_conditions="[]",
                injury_type="knee_pain",
                mobility_level=MobilityLevel.beginner,
                pain_level=3,
                created_at=datetime.utcnow(),
                doctor_id=doctor.id
            )
            db.add(patient)

        # Seed 100 deterministic dummy patients for team development.
        dummy_prefix = "dummy_patient_"
        existing_dummy_usernames = {
            row[0]
            for row in db.query(User.username)
            .filter(User.username.like(f"{dummy_prefix}%"))
            .all()
        }

        for idx in range(1, 101):
            username = f"{dummy_prefix}{idx:03d}"
            if username in existing_dummy_usernames:
                continue

            age = 58 + (idx % 25)
            height_cm = 150.0 + float(idx % 25)
            weight_kg = 48.0 + float((idx * 3) % 35)
            bmi = round(weight_kg / ((height_cm / 100.0) ** 2), 1)
            gender = Gender.male if idx % 2 == 0 else Gender.female
            mobility = [
                MobilityLevel.beginner,
                MobilityLevel.intermediate,
                MobilityLevel.advanced,
            ][idx % 3]
            pain_level = idx % 8
            injury_type = [
                "knee_pain",
                "shoulder_pain",
                "back_pain",
                "balance_issue",
            ][idx % 4]

            patient = User(
                username=username,
                password_hash=hash_password("patient123"),
                role=UserRole.patient,
                full_name=f"Dummy Patient {idx:03d}",
                age=age,
                gender=gender,
                height_cm=height_cm,
                weight_kg=weight_kg,
                bmi=bmi,
                medical_conditions='["hypertension"]' if idx % 5 == 0 else "[]",
                injury_type=injury_type,
                mobility_level=mobility,
                pain_level=pain_level,
                created_at=datetime.utcnow(),
                doctor_id=doctor.id
            )
            db.add(patient)

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()