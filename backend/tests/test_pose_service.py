import pytest
import math
from services.pose_service import AngleCalculator, RepetitionCounter, ExerciseState

class MockPoint:
    def __init__(self, x, y, z=0):
        self.x = x
        self.y = y
        self.z = z

def test_calculate_angle():
    # Right angle: (0,1), (0,0), (1,0) should be 90 degrees
    p1 = MockPoint(0, 1, 0)
    p2 = MockPoint(0, 0, 0)
    p3 = MockPoint(1, 0, 0)
    angle = AngleCalculator.calculate_angle(p1, p2, p3)
    assert 89.0 < angle < 91.0
    
    # Straight line: (-1,0), (0,0), (1,0) should be 180 degrees
    p1 = MockPoint(-1, 0, 0)
    p2 = MockPoint(0, 0, 0)
    p3 = MockPoint(1, 0, 0)
    angle = AngleCalculator.calculate_angle(p1, p2, p3)
    assert 179.0 < angle <= 180.0

def test_repetition_counter_arm_raise():
    counter = RepetitionCounter("arm_raise")
    assert counter.rep_count == 0

    # Arm raise: starts DOWN (arms down, angle < 90)
    # Thresholds: down: 90, up: 160
    # From DOWN to RAISING (angle > 90 + 5)
    counter.update({"left_shoulder": 100, "right_shoulder": 100})
    
    # From RAISING to UP (angle >= 160)
    counter.update({"left_shoulder": 170, "right_shoulder": 170})
    
    # From UP to LOWERING (angle < 160 - 5)
    counter.update({"left_shoulder": 100, "right_shoulder": 100})
    
    # From LOWERING back to DOWN (angle <= 90) to complete rep
    counter.update({"left_shoulder": 20, "right_shoulder": 20})

    assert counter.rep_count == 1

def test_repetition_counter_squat():
    # Squat: starts DOWN (which means standing, angle ~ 180)
    # down_threshold: 160, up_threshold: 90 (deep squat)
    counter = RepetitionCounter("squat")
    assert counter.rep_count == 0
    
    # From DOWN(standing) to LOWERING (angle < 155)
    counter.update({"left_knee": 120, "right_knee": 120})

    # From LOWERING to UP (squatting deep, angle <= 90)
    counter.update({"left_knee": 80, "right_knee": 80})

    # From UP to RAISING (angle > 95)
    counter.update({"left_knee": 120, "right_knee": 120})

    # From RAISING to DOWN (standing, angle >= 160) to complete rep
    counter.update({"left_knee": 170, "right_knee": 170})
    assert counter.rep_count == 1

def test_repetition_counter_calf_raise():
    # Calf raise: starts DOWN (feet flat, angle ~90)
    # down_threshold: 120, up_threshold: 140 (raised)
    counter = RepetitionCounter("calf_raise")
    assert counter.rep_count == 0

    # From DOWN to RAISING (angle > 125)
    counter.update({"left_ankle": 130, "right_ankle": 130})

    # From RAISING to UP (angle >= 140)
    counter.update({"left_ankle": 150, "right_ankle": 150})

    # From UP to LOWERING (angle < 135)
    counter.update({"left_ankle": 130, "right_ankle": 130})
    
    # From LOWERING to DOWN (angle <= 120) to complete rep
    counter.update({"left_ankle": 100, "right_ankle": 100})
    assert counter.rep_count == 1

def test_error_tracking():
    counter = RepetitionCounter("squat")
    counter.add_error_to_current_rep("test_error")
    assert "test_error" in counter.current_rep_errors

    # Complete a rep
    counter.update({"left_knee": 120, "right_knee": 120}) # LOWERING
    counter.update({"left_knee": 80, "right_knee": 80})   # UP
    counter.update({"left_knee": 120, "right_knee": 120}) # RAISING
    counter.update({"left_knee": 170, "right_knee": 170}) # DOWN
    
    assert counter.rep_count == 1
    summary = counter.get_error_summary()
    assert summary["test_error"] == 1
    assert len(counter.current_rep_errors) == 0
