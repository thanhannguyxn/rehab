from services.pain_service import ErrorDetector
from services.pose_service import ExerciseState

class DummyRepCounter:
    def __init__(self):
        self.errors = []
    def add_error_to_current_rep(self, error_name):
        self.errors.append(error_name)

def test_error_detector_requires_persistence(monkeypatch):
    detector = ErrorDetector("arm_raise")
    rep_counter = DummyRepCounter()
    angles = {"left_shoulder": 120, "right_shoulder": 120, "left_elbow": 170, "right_elbow": 170}
    monkeypatch.setattr("services.pain_service.time.time", lambda: 100.0)
    first = detector.detect_errors([], angles, ExerciseState.DOWN, rep_counter)
    assert first == []
    assert rep_counter.errors == []
    monkeypatch.setattr("services.pain_service.time.time", lambda: 104.0)
    second = detector.detect_errors([], angles, ExerciseState.DOWN, rep_counter)
    assert len(second) == 2
    error_names = [e["name"] for e in second]
    assert "Góc vai chưa đủ" in error_names
    assert "Chưa hạ hết" in error_names

def test_single_leg_errors_cleared_outside_holding(monkeypatch):
    detector = ErrorDetector("single_leg_stand")
    rep_counter = DummyRepCounter()
    angles = {"left_knee": 80, "right_knee": 80, "left_leg_behind": 0.0, "right_leg_behind": 0.0}
    monkeypatch.setattr("services.pain_service.time.time", lambda: 100.0)
    result = detector.detect_errors([], angles, ExerciseState.READY, rep_counter)
    assert result == []
    assert rep_counter.errors == []

def test_squat_errors(monkeypatch):
    detector = ErrorDetector('squat')
    rep_counter = DummyRepCounter()
    angles = {'left_knee': 100, 'right_knee': 100, 'left_hip': 100, 'right_hip': 100, 'shoulder_hip_knee': 100, 'hip_knee_ankle': 100}
    monkeypatch.setattr('services.pain_service.time.time', lambda: 100.0)
    detector.detect_errors([], angles, ExerciseState.DOWN, rep_counter)
    monkeypatch.setattr('services.pain_service.time.time', lambda: 104.0)
    res = detector.detect_errors([], angles, ExerciseState.DOWN, rep_counter)
    assert len(res) > 0

def test_calf_raise_errors(monkeypatch):
    detector = ErrorDetector('calf_raise')
    rep_counter = DummyRepCounter()
    angles = {'left_ankle': 100, 'right_ankle': 100, 'left_knee': 150, 'right_knee': 150}
    monkeypatch.setattr('services.pain_service.time.time', lambda: 100.0)
    detector.detect_errors([], angles, ExerciseState.UP, rep_counter)
    monkeypatch.setattr('services.pain_service.time.time', lambda: 104.0)
    res = detector.detect_errors([], angles, ExerciseState.UP, rep_counter)
    assert len(res) > 0
 