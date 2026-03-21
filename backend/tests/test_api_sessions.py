from routers.auth import create_token
from services import session_runtime


def test_start_and_end_session_with_live_stats(client, seed_patient):
    token = create_token(seed_patient.id, seed_patient.username, "patient")
    headers = {"Authorization": f"Bearer {token}"}

    start = client.post("/api/sessions/start", params={"exercise_name": "squat"}, headers=headers)
    assert start.status_code == 200
    session_id = start.json()["session_id"]

    session_runtime._live_session_stats[session_id] = {
        "total_reps": 5,
        "correct_reps": 4,
        "accuracy": 80.0,
        "error_counts": {"not_deep": 2},
    }

    end = client.post(f"/api/sessions/{session_id}/end", headers=headers)
    assert end.status_code == 200
    payload = end.json()
    assert payload["session_id"] == session_id
    assert payload["total_reps"] == 5
    assert payload["correct_reps"] == 4
    assert payload["accuracy"] == 80.0
    assert payload["common_errors"]["Gập gối chưa đủ"]["count"] == 2


def test_my_history_and_error_analytics(client, seed_patient, seed_session_data):
    token = create_token(seed_patient.id, seed_patient.username, "patient")
    headers = {"Authorization": f"Bearer {token}"}

    history = client.get("/api/sessions/my-history", headers=headers)
    assert history.status_code == 200
    sessions = history.json()["sessions"]
    assert len(sessions) == 1
    assert sessions[0]["exercise_name"] == "Bài Tập Squat"
    assert sessions[0]["errors"][0]["name"] == "Gập gối chưa đủ"

    analytics = client.get("/api/sessions/error-analytics", headers=headers)
    assert analytics.status_code == 200
    data = analytics.json()["analytics"]
    assert len(data) == 1
    assert data[0]["exercise_name"] == "Bài Tập Squat"
    assert data[0]["errors"][0]["error_name"] == "Gập gối chưa đủ"

