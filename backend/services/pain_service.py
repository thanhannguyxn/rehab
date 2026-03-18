# Pain and error detection service
import time

class ErrorDetector:
    def __init__(self, exercise_type):
        self.exercise_type = exercise_type
        # Track error timestamps: {error_name: first_detected_time}
        self.error_timers = {}
        self.error_threshold = 3  # seconds - only count error if persists for this long

    def detect_errors(self, landmarks, angles, state, rep_counter):
        """
        Detect errors and add them to the current rep.
        Only records an error if it persists for error_threshold (3s) continuously.
        Returns errors for real-time feedback display.
        """
        errors = []
        current_time = time.time()

        if self.exercise_type == "arm_raise":
            errors.extend(self._check_arm_raise_errors(landmarks, angles, state, rep_counter, current_time))
        elif self.exercise_type == "squat":
            errors.extend(self._check_squat_errors(landmarks, angles, state, rep_counter, current_time))
        elif self.exercise_type == "single_leg_stand":
            errors.extend(self._check_single_leg_errors(landmarks, angles, state, rep_counter, current_time))
        elif self.exercise_type == "calf_raise":
            errors.extend(self._check_calf_raise_errors(landmarks, angles, state, rep_counter, current_time))

        return errors

    def _should_record_error(self, error_name: str, current_time: float) -> bool:
        """
        Check if error should be recorded based on persistence time.
        Returns True if error has persisted for >= error_threshold seconds.
        """
        if error_name not in self.error_timers:
            # First time seeing this error, start timer
            self.error_timers[error_name] = current_time
            return False

        # Check if error has persisted long enough
        elapsed = current_time - self.error_timers[error_name]
        return elapsed >= self.error_threshold

    def _clear_error_timer(self, error_name: str):
        """Clear error timer when error is no longer detected"""
        if error_name in self.error_timers:
            del self.error_timers[error_name]

    def reset_timers(self):
        """Reset all error timers (called when starting new rep)"""
        self.error_timers.clear()

    def _check_single_leg_errors(self, landmarks, angles, state, rep_counter, current_time):
        from services.pose_service import ExerciseState

        errors = []

        # Only check errors during HOLDING state
        if state != ExerciseState.HOLDING:
            # Clear timers when not in HOLDING state
            self._clear_error_timer('Gối chưa gập đủ sâu')
            self._clear_error_timer('Chân không ra sau')
            return errors

        # Lấy góc của cả 2 bên
        left_knee_flexion = angles.get('left_knee', 180)
        right_knee_flexion = angles.get('right_knee', 180)
        left_leg_behind = angles.get('left_leg_behind', 0)
        right_leg_behind = angles.get('right_leg_behind', 0)

        # Xác định bên nào đang nâng (bên có knee flexion nhỏ hơn)
        if left_knee_flexion < right_knee_flexion:
            # Left leg is lifted
            knee_flexion = left_knee_flexion
            leg_behind_value = left_leg_behind
            side = "left"
        else:
            # Right leg is lifted
            knee_flexion = right_knee_flexion
            leg_behind_value = right_leg_behind
            side = "right"

        # Error 1: Gối không gập đủ sâu (phải < 50°)
        if knee_flexion > 50:
            error_name = 'Gối chưa gập đủ sâu'

            # Only record and show error if it persists for 1.5s
            if self._should_record_error(error_name, current_time):
                rep_counter.add_error_to_current_rep(error_name)
                # Show in real-time feedback only after 1.5s
                errors.append({
                    'name': error_name,
                    'message': f' Gập gối sâu hơn! (hiện tại: {knee_flexion:.0f}°, cần: <50°)',
                    'severity': 'high'
                })
        else:
            self._clear_error_timer('Gối chưa gập đủ sâu')

        # Error 2: CHÂN KHÔNG RA SAU - ra trước (dùng Z-coordinate)
        if leg_behind_value < 0.05:
            error_name = 'Chân không ra sau'

            # Only record and show error if it persists for 1.5s
            if self._should_record_error(error_name, current_time):
                rep_counter.add_error_to_current_rep(error_name)
                # Show in real-time feedback only after 1.5s
                errors.append({
                    'name': error_name,
                    'message': f' Đưa chân RA SAU, không ra trước! (hiện tại: {leg_behind_value:.3f}, cần: >0.05)',
                    'severity': 'critical'
                })
        else:
            self._clear_error_timer('Chân không ra sau')

        return errors

    def _check_arm_raise_errors(self, landmarks, angles, state, rep_counter, current_time):
        errors = []

        # Get angles
        left_shoulder = angles.get('left_shoulder', 0)
        right_shoulder = angles.get('right_shoulder', 0)
        left_elbow = angles.get('left_elbow', 0)
        right_elbow = angles.get('right_elbow', 0)

        # Error 1: Arms not high enough (shoulder angle < 160°)
        shoulder_angle = min(left_shoulder, right_shoulder)
        if shoulder_angle < 160:
            error_name = 'not_high'
            if self._should_record_error(error_name, current_time):
                rep_counter.add_error_to_current_rep('Góc vai chưa đủ')
                errors.append({
                    'name': 'Góc vai chưa đủ',
                    'message': f'Giơ tay cao hơn! (hiện tại: {shoulder_angle:.0f}°, cần: >160°)',
                    'severity': 'high'
                })
        else:
            self._clear_error_timer('not_high')

        # Error 2: Arms bent (elbow angle < 160°)
        elbow_angle = min(left_elbow, right_elbow)
        if elbow_angle < 160:
            error_name = 'arms_bent'
            if self._should_record_error(error_name, current_time):
                rep_counter.add_error_to_current_rep('Tay không thẳng')
                errors.append({
                    'name': 'Tay không thẳng',
                    'message': f'Duỗi thẳng tay! (hiện tại: {elbow_angle:.0f}°, cần: >160°)',
                    'severity': 'medium'
                })
        else:
            self._clear_error_timer('arms_bent')

        # Error 3: Not lowering enough (shoulder angle > 90°)
        if shoulder_angle > 90:
            error_name = 'not_low'
            if self._should_record_error(error_name, current_time):
                rep_counter.add_error_to_current_rep('Chưa hạ hết')
                errors.append({
                    'name': 'Chưa hạ hết',
                    'message': f'Hạ tay xuống thấp hơn! (hiện tại: {shoulder_angle:.0f}°, cần: <90°)',
                    'severity': 'medium'
                })
        else:
            self._clear_error_timer('not_low')

        return errors

    def _check_squat_errors(self, landmarks, angles, state, rep_counter, current_time):
        errors = []

        # Get angles
        left_knee = angles.get('left_knee', 180)
        right_knee = angles.get('right_knee', 180)
        knee_angle = max(left_knee, right_knee)  # Use the straighter leg

        # Error 1: Not deep enough (knee angle > 90°)
        if knee_angle > 90:
            error_name = 'not_deep'
            if self._should_record_error(error_name, current_time):
                rep_counter.add_error_to_current_rep('Gập gối chưa đủ')
                errors.append({
                    'name': 'Gập gối chưa đủ',
                    'message': f'Gập gối sâu hơn! (hiện tại: {knee_angle:.0f}°, cần: <90°)',
                    'severity': 'high'
                })
        else:
            self._clear_error_timer('not_deep')

        # Error 2: Knees forward (check if knees are in front of toes)
        # This is a simplified check - in real implementation you'd check alignment
        if knee_angle < 120:  # Only check when squatting
            # Simplified: if knee angle is very acute, likely knees are forward
            error_name = 'knees_forward'
            if self._should_record_error(error_name, current_time):
                rep_counter.add_error_to_current_rep('Gối đẩy ra trước')
                errors.append({
                    'name': 'Gối đẩy ra trước',
                    'message': 'Giữ gối không đẩy ra trước mũi chân!',
                    'severity': 'high'
                })
        else:
            self._clear_error_timer('knees_forward')

        # Error 3: Not standing straight (knee angle < 160° when should be up)
        if knee_angle < 160:
            error_name = 'not_straight'
            if self._should_record_error(error_name, current_time):
                rep_counter.add_error_to_current_rep('Chưa đứng thẳng')
                errors.append({
                    'name': 'Chưa đứng thẳng',
                    'message': f'Đứng thẳng người! (hiện tại: {knee_angle:.0f}°, cần: >160°)',
                    'severity': 'medium'
                })
        else:
            self._clear_error_timer('not_straight')

        return errors

    def _check_calf_raise_errors(self, landmarks, angles, state, rep_counter, current_time):
        errors = []

        # Get angles
        left_ankle = angles.get('left_ankle', 90)
        right_ankle = angles.get('right_ankle', 90)
        left_knee = angles.get('left_knee', 180)
        right_knee = angles.get('right_knee', 180)

        ankle_angle = min(left_ankle, right_ankle)  # Use the lower ankle
        knee_angle = min(left_knee, right_knee)     # Use the more bent knee

        # Error 1: Not raised high enough (ankle angle < 140°)
        if ankle_angle < 140:
            error_name = 'not_raised'
            if self._should_record_error(error_name, current_time):
                rep_counter.add_error_to_current_rep('Chưa nâng đủ cao')
                errors.append({
                    'name': 'Chưa nâng đủ cao',
                    'message': f'Nâng gót cao hơn! (hiện tại: {ankle_angle:.0f}°, cần: >140°)',
                    'severity': 'high'
                })
        else:
            self._clear_error_timer('not_raised')

        # Error 2: Knees bent (knee angle < 160°)
        if knee_angle < 160:
            error_name = 'knees_bent'
            if self._should_record_error(error_name, current_time):
                rep_counter.add_error_to_current_rep('Gập gối')
                errors.append({
                    'name': 'Gập gối',
                    'message': f'Duỗi thẳng chân! (hiện tại: {knee_angle:.0f}°, cần: >160°)',
                    'severity': 'medium'
                })
        else:
            self._clear_error_timer('knees_bent')

        # Error 3: Not lowered enough (ankle angle > 120°)
        if ankle_angle > 120:
            error_name = 'not_lowered'
            if self._should_record_error(error_name, current_time):
                rep_counter.add_error_to_current_rep('Chưa hạ hết')
                errors.append({
                    'name': 'Chưa hạ hết',
                    'message': f'Hạ gót xuống thấp hơn! (hiện tại: {ankle_angle:.0f}°, cần: <120°)',
                    'severity': 'medium'
                })
        else:
            self._clear_error_timer('not_lowered')

        return errors