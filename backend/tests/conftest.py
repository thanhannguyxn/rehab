import os
import sys
from datetime import datetime
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ["DATABASE_URL"] = "sqlite:///./test_rehab.db"

from db.connection import get_db  # noqa: E402
from models import (  # noqa: E402
    Base,
    DBSession,
    SessionError,
    SessionFrame,
    User,
    UserRole,
    hash_password,
)
from routers import auth, sessions  # noqa: E402
from services import session_runtime  # noqa: E402

TEST_DB_URL = "sqlite:///./test_rehab.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app = FastAPI()
app.include_router(auth.router, prefix="/api/auth")
app.include_router(sessions.router, prefix="/api/sessions")


@pytest.fixture(autouse=True)
def clean_db():
    session_runtime._live_session_stats.clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    session_runtime._live_session_stats.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seed_patient(db_session):
    patient = User(
        username="patient_test",
        password_hash=hash_password("patient123"),
        role=UserRole.patient,
        full_name="Test Patient",
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


@pytest.fixture
def seed_doctor(db_session):
    doctor = User(
        username="doctor_test",
        password_hash=hash_password("doctor123"),
        role=UserRole.doctor,
        full_name="Test Doctor",
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)
    return doctor


@pytest.fixture
def seed_session_data(db_session, seed_patient):
    session = DBSession(
        patient_id=seed_patient.id,
        exercise_name="squat",
        start_time=datetime(2026, 1, 1, 0, 0, 0),
        total_reps=10,
        correct_reps=8,
        accuracy=80.0,
        duration_seconds=120,
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    db_session.add_all(
        [
            SessionFrame(
                session_id=session.id,
                timestamp=datetime(2026, 1, 1, 0, 0, 1),
                rep_count=1,
                angles="{}",
                errors="[]",
            ),
            SessionFrame(
                session_id=session.id,
                timestamp=datetime(2026, 1, 1, 0, 0, 2),
                rep_count=2,
                angles="{}",
                errors='["not_deep"]',
            ),
        ]
    )
    db_session.add(SessionError(session_id=session.id, error_name="not_deep", count=2, severity="high"))
    db_session.commit()
    return session

