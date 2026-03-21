from services.pose_service import AngleCalculator


class Point:
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z


def test_calculate_angle_90_degrees():
    p1 = Point(1, 0)
    p2 = Point(0, 0)
    p3 = Point(0, 1)
    angle = AngleCalculator.calculate_angle(p1, p2, p3)
    assert 89 <= angle <= 91


def test_calculate_angle_straight_line():
    p1 = Point(-1, 0)
    p2 = Point(0, 0)
    p3 = Point(1, 0)
    angle = AngleCalculator.calculate_angle(p1, p2, p3)
    assert 179 <= angle <= 181

