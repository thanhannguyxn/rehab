import pytest
from routers.auth import create_token
from models import User

def test_get_my_patients(client, db_session, seed_doctor, seed_patient):
    # Assign patient to doctor
    seed_patient.doctor_id = seed_doctor.id
    db_session.commit()

    token = create_token(seed_doctor.id, seed_doctor.username, "doctor")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/doctor/patients", headers=headers)
    assert response.status_code == 200
    patients = response.json()["patients"]
    assert len(patients) == 1
    assert patients[0]["id"] == seed_patient.id

def test_get_my_patients_unauthorized(client, seed_patient):
    token = create_token(seed_patient.id, seed_patient.username, "patient")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/doctor/patients", headers=headers)
    assert response.status_code == 403

def test_get_patient_history(client, db_session, seed_doctor, seed_patient, seed_session_data):
    token = create_token(seed_doctor.id, seed_doctor.username, "doctor")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/api/doctor/patient/{seed_patient.id}/history", headers=headers)
    assert response.status_code == 200
    sessions = response.json()["sessions"]
    assert len(sessions) > 0
    assert sessions[0]["exercise_name"] == "Bài Tập Squat"

def test_get_patient_error_analytics(client, db_session, seed_doctor, seed_patient, seed_session_data):
    token = create_token(seed_doctor.id, seed_doctor.username, "doctor")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/api/doctor/patient/{seed_patient.id}/error-analytics", headers=headers)
    assert response.status_code == 200
    analytics = response.json()["analytics"]
    assert len(analytics) > 0
    assert analytics[0]["exercise_name"] == "Bài Tập Squat"
    assert analytics[0]["errors"][0]["error_name"] == "Gập gối chưa đủ"
