# Pose analysis service
import cv2
import mediapipe as mp
import numpy as np
from enum import Enum
from collections import deque
import time

# MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=1
)

class AngleCalculator:
    @staticmethod
    def calculate_angle(point1, point2, point3):
        a = np.array([point1.x, point1.y])
        b = np.array([point2.x, point2.y])
        c = np.array([point3.x, point3.y])

        ba = a - b
        bc = c - b

        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))

        return np.degrees(angle)

    @staticmethod
    def get_angles(landmarks, exercise_type):
        if exercise_type == "squat":
            return {
                'left_knee': AngleCalculator.calculate_angle(
                    landmarks[mp_pose.PoseLandmark.LEFT_HIP],
                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE],
                    landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
                ),
                'right_knee': AngleCalculator.calculate_angle(
                    landmarks[mp_pose.PoseLandmark.RIGHT_HIP],
                    landmarks[mp_pose.PoseLandmark.RIGHT_KNEE],
                    landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
                ),
            }
        elif exercise_type == "arm_raise":
            return {
                'left_shoulder': AngleCalculator.calculate_angle(
                    landmarks[mp_pose.PoseLandmark.LEFT_HIP],
                    landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER],
                    landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
                ),
                'right_shoulder': AngleCalculator.calculate_angle(
                    landmarks[mp_pose.PoseLandmark.RIGHT_HIP],
                    landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER],
                    landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW]
                ),
                'left_elbow': AngleCalculator.calculate_angle(
                    landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER],
                    landmarks[mp_pose.PoseLandmark.LEFT_ELBOW],
                    landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
                ),
                'right_elbow': AngleCalculator.calculate_angle(
                    landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER],
                    landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW],
                    landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
                ),
            }
        # THÊM MỚI: single_leg_stand
        elif exercise_type == "single_leg_stand":
            # GÓC KNEE FLEXION (gập gối): HIP -> KNEE -> ANKLE
            left_knee_flexion = AngleCalculator.calculate_angle(
                landmarks[mp_pose.PoseLandmark.LEFT_HIP],
                landmarks[mp_pose.PoseLandmark.LEFT_KNEE],
                landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
            )
            right_knee_flexion = AngleCalculator.calculate_angle(
                landmarks[mp_pose.PoseLandmark.RIGHT_HIP],
                landmarks[mp_pose.PoseLandmark.RIGHT_KNEE],
                landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
            )

            # KIỂM TRA CHÂN RA SAU bằng Z-coordinate (độ sâu)
            # Nếu knee.z > hip.z => chân ra SAU (gối xa camera hơn hông)
            left_knee_z = landmarks[mp_pose.PoseLandmark.LEFT_KNEE].z
            left_hip_z = landmarks[mp_pose.PoseLandmark.LEFT_HIP].z
            left_leg_behind = left_knee_z - left_hip_z  # Dương = ra sau, Âm = ra trước

            right_knee_z = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].z
            right_hip_z = landmarks[mp_pose.PoseLandmark.RIGHT_HIP].z
            right_leg_behind = right_knee_z - right_hip_z  # Dương = ra sau, Âm = ra trước

            angles = {
                # Gập gối (knee flexion)
                'left_knee': left_knee_flexion,
                'right_knee': right_knee_flexion,

                # Chân ra sau (dùng Z-coordinate thay vì góc)
                'left_leg_behind': left_leg_behind,
                'right_leg_behind': right_leg_behind,

                # Keep Y positions for height check
                'left_knee_y': landmarks[mp_pose.PoseLandmark.LEFT_KNEE].y,
                'right_knee_y': landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].y,
                'left_hip_y': landmarks[mp_pose.PoseLandmark.LEFT_HIP].y,
                'right_hip_y': landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y,
            }

            # Debug information
            print(f" Left - Knee Flexion: {left_knee_flexion:.1f}°, Leg Behind: {left_leg_behind:.3f} {'RA SAU' if left_leg_behind > 0.05 else 'RA TRƯỚC'}")
            print(f" Right - Knee Flexion: {right_knee_flexion:.1f}°, Leg Behind: {right_leg_behind:.3f} {'RA SAU' if right_leg_behind > 0.05 else 'RA TRƯỚC'}")

            return angles

        # THÊM MỚI: calf_raise
        elif exercise_type == "calf_raise":
            # Tính góc mắt cá chân (ankle)
            left_ankle_angle = AngleCalculator.calculate_angle(
                landmarks[mp_pose.PoseLandmark.LEFT_KNEE],
                landmarks[mp_pose.PoseLandmark.LEFT_ANKLE],
                landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX]
            )
            right_ankle_angle = AngleCalculator.calculate_angle(
                landmarks[mp_pose.PoseLandmark.RIGHT_KNEE],
                landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE],
                landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX]
            )

            # Tính góc gối (đảm bảo chân thẳng)
            left_knee_angle = AngleCalculator.calculate_angle(
                landmarks[mp_pose.PoseLandmark.LEFT_HIP],
                landmarks[mp_pose.PoseLandmark.LEFT_KNEE],
                landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
            )
            right_knee_angle = AngleCalculator.calculate_angle(
                landmarks[mp_pose.PoseLandmark.RIGHT_HIP],
                landmarks[mp_pose.PoseLandmark.RIGHT_KNEE],
                landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
            )

            # Lấy vị trí Y của gót và mũi chân
            left_heel_y = landmarks[mp_pose.PoseLandmark.LEFT_HEEL].y
            right_heel_y = landmarks[mp_pose.PoseLandmark.RIGHT_HEEL].y
            left_foot_index_y = landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX].y
            right_foot_index_y = landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX].y

            angles = {
                'left_ankle': left_ankle_angle,
                'right_ankle': right_ankle_angle,
                'left_knee': left_knee_angle,
                'right_knee': right_knee_angle,
                'left_heel_y': left_heel_y,
                'right_heel_y': right_heel_y,
                'left_foot_index_y': left_foot_index_y,
                'right_foot_index_y': right_foot_index_y,
            }

            # Debug
            print(f"Ankle angles - Left: {left_ankle_angle:.1f}°, Right: {right_ankle_angle:.1f}°")
            print(f"Heel height - Left: {left_heel_y:.3f}, Right: {right_heel_y:.3f}")

            return angles

        return {}


class ExerciseState(Enum):
    DOWN = "down"
    RAISING = "raising"
    UP = "up"
    LOWERING = "lowering"
    # THÊM MỚI cho single_leg_stand
    READY = "ready"
    LIFTING = "lifting"
    HOLDING = "holding"
    SWITCH_SIDE = "switch_side"
    COMPLETE = "complete"


class RepetitionCounter:
    def __init__(self, exercise_type, custom_thresholds=None):
        """
        Initialize RepetitionCounter.

        Args:
            exercise_type: Type of exercise (squat, arm_raise, calf_raise, single_leg_stand)
            custom_thresholds: Optional dict with custom thresholds from database
                             {'down_threshold': float, 'up_threshold': float, 'hysteresis': float}
        """
        self.exercise_type = exercise_type
        self.rep_count = 0

        # Khởi tạo state dựa trên exercise type
        if exercise_type == "single_leg_stand":
            self.state = ExerciseState.READY
        else:
            self.state = ExerciseState.DOWN

        self.last_state_change = time.time()

        # REP-BASED ERROR TRACKING
        self.current_rep_errors = set()  # Lỗi trong rep hiện tại (unique)
        self.all_rep_errors = []  # Danh sách lỗi của tất cả reps: [[errors_rep1], [errors_rep2], ...]
        self.rep_completed = False  # Flag để track khi rep hoàn thành

        # For single_leg_stand
        self.current_side = "left"  # Start with left leg
        self.hold_start_time = None
        self.hold_duration = 3.0  # 10 seconds
        self.left_completed = False
        self.right_completed = False

        # Default Thresholds
        if exercise_type == "arm_raise":
            self.down_threshold = 90
            self.up_threshold = 160
            self.hysteresis = 5
        elif exercise_type == "squat":
            self.down_threshold = 160
            self.up_threshold = 90
            self.hysteresis = 5
        elif exercise_type == "single_leg_stand":
            self.knee_threshold = 90  # Góc gập gối
            self.knee_height_threshold = 0.1  # Chân phải nâng cao hơn 0.1 (tỉ lệ)
            # Set default thresholds for compatibility
            self.down_threshold = 90
            self.up_threshold = 60
            self.hysteresis = 5
        elif exercise_type == "calf_raise":
            # Ngưỡng cho nâng gót chân - CHỈ CẦN NÂNG MỘT CHÚT
            self.down_threshold = 120  # Góc ankle khi gót chạm đất
            self.up_threshold = 140    # Góc ankle khi nâng gót lên cao
            self.hysteresis = 5
        else:
            # Unknown exercise - use generic thresholds
            self.down_threshold = 160
            self.up_threshold = 90
            self.hysteresis = 5

        # Apply custom thresholds from database (override defaults)
        if custom_thresholds:
            if 'down_threshold' in custom_thresholds and custom_thresholds['down_threshold'] is not None:
                self.down_threshold = custom_thresholds['down_threshold']
            if 'up_threshold' in custom_thresholds and custom_thresholds['up_threshold'] is not None:
                self.up_threshold = custom_thresholds['up_threshold']
            if 'hysteresis' in custom_thresholds and custom_thresholds['hysteresis'] is not None:
                self.hysteresis = custom_thresholds['hysteresis']
            print(f"Applied custom thresholds: down={self.down_threshold}, up={self.up_threshold}, hysteresis={self.hysteresis}")

    def add_error_to_current_rep(self, error_name: str):
        """Add error to current rep (will only count once per rep)"""
        self.current_rep_errors.add(error_name)

    def get_error_summary(self):
        """Get total count of each error across all reps"""
        error_counts = {}
        for rep_errors in self.all_rep_errors:
            for error in rep_errors:
                error_counts[error] = error_counts.get(error, 0) + 1
        return error_counts

    def _complete_rep(self):
        """Called when a rep is completed - save errors for this rep"""
        self.rep_count += 1
        self.all_rep_errors.append(list(self.current_rep_errors))
        print(f" Rep {self.rep_count} completed! Errors in this rep: {list(self.current_rep_errors)}")
        print(f" Total all_rep_errors so far: {self.all_rep_errors}")
        self.current_rep_errors.clear()  # Reset for next rep
        self.rep_completed = True

    def update(self, angles):
        """Update state machine and return current rep count"""
        self.rep_completed = False  # Reset flag

        if self.exercise_type == "arm_raise":
            return self._count_arm_raise(angles)
        elif self.exercise_type == "squat":
            return self._count_squat(angles)
        elif self.exercise_type == "single_leg_stand":
            return self._count_single_leg(angles)
        elif self.exercise_type == "calf_raise":
            return self._count_calf_raise(angles)
        return self.rep_count

    def _count_single_leg(self, angles):
        """State machine for single leg stand - CHÂN RA SAU"""
        current_time = time.time()

        # Lấy các góc theo bên hiện tại
        if self.current_side == "left":
            knee_flexion = angles.get('left_knee', 180)
            leg_behind_value = angles.get('left_leg_behind', 0)
        else:
            knee_flexion = angles.get('right_knee', 180)
            leg_behind_value = angles.get('right_leg_behind', 0)

        # KIỂM TRA TƯ THẾ ĐÚNG (CHÂN RA SAU):
        # 1. Gối gập sâu < 50° (knee flexion)
        # 2. Chân ra sau: knee.z > hip.z + 0.05 (gối phía sau hông)

        knee_bent_enough = knee_flexion < 50  # Gối gập sâu
        leg_behind = leg_behind_value > 0.05  # Chân ra sau (KHÔNG ra trước!)

        # Tư thế đúng khi: gối gập + chân ra sau
        is_correct_position = knee_bent_enough and leg_behind

        # Debug information
        print(f" {self.current_side.upper()} side:")
        print(f"   Knee Flexion: {knee_flexion:.1f}° ({'Right' if knee_bent_enough else 'Wrong'} <50°)")
        print(f"   Leg Behind: {leg_behind_value:.3f} ({'Right' if leg_behind else 'Wrong'} >0.05)")
        print(f"   Correct Position: {' YES' if is_correct_position else ' NO'}")

        # State machine
        if self.state == ExerciseState.READY:
            # Waiting to start - đợi người dùng làm tư thế đúng
            if is_correct_position:
                self.state = ExerciseState.LIFTING
                self.last_state_change = current_time

        elif self.state == ExerciseState.LIFTING:
            # Leg is being lifted - đang nâng chân lên tư thế
            if is_correct_position:
                # Đã vào tư thế đúng, bắt đầu giữ
                self.state = ExerciseState.HOLDING
                self.hold_start_time = current_time
                self.last_state_change = current_time
            elif knee_flexion > 160:  # Chân hạ xuống
                # Quay về ready
                self.state = ExerciseState.READY
                self.last_state_change = current_time

        elif self.state == ExerciseState.HOLDING:
            # Holding the position - đang giữ tư thế
            if self.hold_start_time:
                elapsed = current_time - self.hold_start_time

                # Mất tư thế nếu:
                # 1. Gối không gập đủ (>70°)
                # 2. Chân không còn ở phía sau (leg_behind < 0.03)
                lost_position = (knee_flexion > 70) or (leg_behind_value < 0.03)

                if lost_position:
                    # Mất tư thế
                    self.state = ExerciseState.LOWERING
                    self.hold_start_time = None
                    self.last_state_change = current_time
                    print(f" Mất tư thế! Knee: {knee_flexion:.1f}°, Leg Behind: {leg_behind_value:.3f}")

                elif elapsed >= self.hold_duration:
                    # Giữ đủ 10 giây!
                    self.state = ExerciseState.LOWERING
                    self.hold_start_time = None
                    self.last_state_change = current_time

                    # Mark side as completed
                    if self.current_side == "left":
                        self.left_completed = True
                        print(" Hoàn thành bên TRÁI!")
                    else:
                        self.right_completed = True
                        print(" Hoàn thành bên PHẢI!")

        elif self.state == ExerciseState.LOWERING:
            # Lowering the leg - đang hạ chân xuống
            # Chân đã hạ xuống khi knee flexion > 160° (gần duỗi thẳng)
            if knee_flexion > 160:
                # Leg is down
                if self.left_completed and self.right_completed:
                    # Both sides done - complete!
                    self.state = ExerciseState.COMPLETE
                    self._complete_rep()  #  Rep hoàn thành!
                    self.left_completed = False
                    self.right_completed = False
                    self.last_state_change = current_time
                    print(" Hoàn thành CẢ 2 BÊN! +1 Rep")
                else:
                    # Switch to other side
                    self.state = ExerciseState.SWITCH_SIDE
                    self.current_side = "right" if self.current_side == "left" else "left"
                    self.last_state_change = current_time
                    print(f" Chuyển sang bên {self.current_side.upper()}")

        elif self.state == ExerciseState.SWITCH_SIDE:
            # Wait a moment, then ready for other side
            if current_time - self.last_state_change > 2.0:  # 2 second pause
                self.state = ExerciseState.READY
                self.last_state_change = current_time

        elif self.state == ExerciseState.COMPLETE:
            # Wait a moment, then ready for next rep
            if current_time - self.last_state_change > 3.0:  # 3 second pause
                self.state = ExerciseState.READY
                self.current_side = "left"
                self.last_state_change = current_time

        return self.rep_count

    def _count_arm_raise(self, angles):
        #  YÊU CẦU CẢ 2 TAY - cả 2 tay phải đạt ngưỡng
        left_shoulder = angles.get('left_shoulder', 0)
        right_shoulder = angles.get('right_shoulder', 0)
        # Dùng MIN để đảm bảo CẢ 2 TAY đều đạt ngưỡng (tay thấp nhất phải đủ cao)
        shoulder_angle = min(left_shoulder, right_shoulder)

        current_time = time.time()

        if self.state == ExerciseState.DOWN:
            if shoulder_angle > self.down_threshold + self.hysteresis:
                self.state = ExerciseState.RAISING
                self.last_state_change = current_time

        elif self.state == ExerciseState.RAISING:
            if shoulder_angle >= self.up_threshold:
                self.state = ExerciseState.UP
                self.last_state_change = current_time
            elif shoulder_angle < self.down_threshold:
                self.state = ExerciseState.DOWN
                self.last_state_change = current_time

        elif self.state == ExerciseState.UP:
            if shoulder_angle < self.up_threshold - self.hysteresis:
                self.state = ExerciseState.LOWERING
                self.last_state_change = current_time

        elif self.state == ExerciseState.LOWERING:
            if shoulder_angle < self.down_threshold:
                self.state = ExerciseState.DOWN
                self._complete_rep()  #  Rep hoàn thành!
                self.last_state_change = current_time
            elif shoulder_angle > self.up_threshold:
                self.state = ExerciseState.UP
                self.last_state_change = current_time

        return self.rep_count

    def _count_squat(self, angles):
        #  YÊU CẦU CẢ 2 CHÂN - cả 2 chân phải đạt ngưỡng
        left_knee = angles.get('left_knee', 180)
        right_knee = angles.get('right_knee', 180)
        # Dùng MAX để đảm bảo CẢ 2 CHÂN đều gập đủ sâu (chân cao nhất phải đủ thấp)
        knee_angle = max(left_knee, right_knee)

        current_time = time.time()

        if self.state == ExerciseState.DOWN:
            if knee_angle < self.down_threshold - self.hysteresis:
                self.state = ExerciseState.LOWERING
                self.last_state_change = current_time

        elif self.state == ExerciseState.LOWERING:
            if knee_angle <= self.up_threshold:
                self.state = ExerciseState.UP
                self.last_state_change = current_time
            elif knee_angle > self.down_threshold:
                self.state = ExerciseState.DOWN
                self.last_state_change = current_time

        elif self.state == ExerciseState.UP:
            if knee_angle > self.up_threshold + self.hysteresis:
                self.state = ExerciseState.RAISING
                self.last_state_change = current_time

        elif self.state == ExerciseState.RAISING:
            if knee_angle >= self.down_threshold:
                self.state = ExerciseState.DOWN
                self._complete_rep()  #  Rep hoàn thành!
                self.last_state_change = current_time
            elif knee_angle < self.up_threshold:
                self.state = ExerciseState.UP
                self.last_state_change = current_time

        return self.rep_count

    def _count_calf_raise(self, angles):
        """State machine for calf raise - YÊU CẦU CẢ 2 CHÂN"""
        left_ankle = angles.get('left_ankle', 90)
        right_ankle = angles.get('right_ankle', 90)
        # Dùng MIN để đảm bảo CẢ 2 CHÂN đều nâng đủ cao (chân thấp nhất phải đủ cao)
        ankle_angle = min(left_ankle, right_ankle)

        current_time = time.time()

        if self.state == ExerciseState.DOWN:
            if ankle_angle > self.down_threshold + self.hysteresis:
                self.state = ExerciseState.RAISING
                self.last_state_change = current_time

        elif self.state == ExerciseState.RAISING:
            if ankle_angle >= self.up_threshold:
                self.state = ExerciseState.UP
                self.last_state_change = current_time
            elif ankle_angle < self.down_threshold:
                self.state = ExerciseState.DOWN
                self.last_state_change = current_time

        elif self.state == ExerciseState.UP:
            if ankle_angle < self.up_threshold - self.hysteresis:
                self.state = ExerciseState.LOWERING
                self.last_state_change = current_time

        elif self.state == ExerciseState.LOWERING:
            if ankle_angle <= self.down_threshold:
                self.state = ExerciseState.DOWN
                self._complete_rep()  #  Rep hoàn thành!
                self.last_state_change = current_time
            elif ankle_angle > self.up_threshold:
                self.state = ExerciseState.UP
                self.last_state_change = current_time

        return self.rep_count

    def get_hold_time_remaining(self):
        """Get remaining hold time for single_leg_stand"""
        if self.exercise_type != "single_leg_stand":
            return None
        if self.state != ExerciseState.HOLDING or not self.hold_start_time:
            return None

        elapsed = time.time() - self.hold_start_time
        remaining = max(0, self.hold_duration - elapsed)
        return remaining

    def get_current_side(self):
        """Get current side for single_leg_stand"""
        if self.exercise_type != "single_leg_stand":
            return None
        return self.current_side

    def reset(self):
        self.rep_count = 0
        self.state = ExerciseState.DOWN if self.exercise_type != "single_leg_stand" else ExerciseState.READY
        self.last_state_change = time.time()
        self.hold_start_time = None
        self.left_completed = False
        self.right_completed = False
        self.current_side = "left"
        #  Reset error tracking
        self.current_rep_errors.clear()
        self.all_rep_errors.clear()
        self.rep_completed = False

    def get_state(self):
        return self.state