# Database connection and configuration
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
    from models import User, UserRole, Gender, hash_password
    from datetime import datetime

    create_tables()

    db = SessionLocal()
    try:
        # Create default users if not exist
        if db.query(User).count() == 0:
            # Default doctor
            doctor = User(
                username="doctor1",
                password_hash=hash_password("doctor123"),
                role=UserRole.doctor,
                full_name="BS. Nguyễn Văn A",
                created_at=datetime.utcnow()
            )
            db.add(doctor)
            db.flush()  # Get the doctor_id

            # Default patients
            patients_data = [
                ("patient1", "patient123", "Trần Thị B", 65, Gender.female),
                ("patient2", "patient123", "Lê Văn C", 70, Gender.male),
            ]

            for username, password, name, age, gender in patients_data:
                patient = User(
                    username=username,
                    password_hash=hash_password(password),
                    role=UserRole.patient,
                    full_name=name,
                    age=age,
                    gender=gender,
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