import pytest
from routers.auth import create_token
from models import User

def test_update_profile(client, db_session, seed_patient):
    token = create_token(seed_patient.id, seed_patient.username, "patient")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "age": 30,
        "gender": "male",
        "height_cm": 175.5,
        "weight_kg": 70.0,
        "medical_conditions": "None",
        "mobility_level": "intermediate",
        "pain_level": 2
    }

    response = client.post("/api/profile/update", json=payload, headers=headers)
    print("RES:", response.json())
    assert response.status_code == 200
    assert response.json()["message"] == "Profile updated successfully"

    db_session.expire_all()
    # Verify db was updated
    user = db_session.query(User).filter(User.id == seed_patient.id).first()
    assert user.age == 30
    assert user.gender.value == "male"
    assert user.height_cm == 175.5
    assert user.weight_kg == 70.0
    assert user.medical_conditions == "None"
    assert user.mobility_level.value == "intermediate"
    assert user.pain_level == 2

def test_get_profile(client, db_session, seed_patient):
    token = create_token(seed_patient.id, seed_patient.username, "patient")
    headers = {"Authorization": f"Bearer {token}"}

    seed_patient.age = 45
    seed_patient.pain_level = 5
    db_session.commit()

    response = client.get("/api/profile/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["age"] == 45
    assert data["pain_level"] == 5

def test_get_personalized_params(client, db_session, seed_patient, monkeypatch):
    token = create_token(seed_patient.id, seed_patient.username, "patient")
    headers = {"Authorization": f"Bearer {token}"}
    
    seed_patient.age = 25
    seed_patient.pain_level = 2
    seed_patient.height_cm = 175.0
    seed_patient.weight_kg = 70.0
    seed_patient.medical_conditions = "None"
    db_session.commit()

    payload = {
        "exercise_type": "squat"
    }

    response = client.post("/api/profile/personalized-params", json=payload, headers=headers)
    print("PARAMS RES:", response.json())
    assert response.status_code == 200
    assert "down_angle" in response.json()
    assert "up_angle" in response.json()
