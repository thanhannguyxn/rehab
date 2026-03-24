# Face emotion detection service
import cv2
import mediapipe as mp
import numpy as np
from enum import Enum
import time
from typing import Optional, Dict, List, Tuple

# MediaPipe Face Mesh with optimized settings for performance
mp_face_mesh = mp.solutions.face_mesh

class PerformanceMode(Enum):
    HIGH_ACCURACY = "high_accuracy"
    BALANCED = "balanced"
    HIGH_SPEED = "high_speed"

class FaceMeshManager:
    def __init__(self):
        self.current_mode = PerformanceMode.BALANCED
        self.face_mesh_instances = {}
        self._create_instances()

    def _create_instances(self):
        """Create different FaceMesh instances for different performance modes"""
        # High accuracy: more detailed but slower
        self.face_mesh_instances[PerformanceMode.HIGH_ACCURACY] = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

        # Balanced: good balance between speed and accuracy
        self.face_mesh_instances[PerformanceMode.BALANCED] = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,  # Disable for speed
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

        # High speed: fastest but less accurate
        self.face_mesh_instances[PerformanceMode.HIGH_SPEED] = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.4,
            min_tracking_confidence=0.4
        )

    def set_performance_mode(self, mode: PerformanceMode):
        """Switch performance mode"""
        self.current_mode = mode
        print(f"Face tracking performance mode: {mode.value}")

    def get_current_instance(self):
        """Get current FaceMesh instance based on performance mode"""
        return self.face_mesh_instances[self.current_mode]

# Global face mesh manager
face_mesh_manager = FaceMeshManager()
# Default face mesh for backward compatibility
face_mesh = face_mesh_manager.get_current_instance()

class EmotionState(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    STRUGGLING = "struggling"
    PAIN = "pain"
    TIRED = "tired"
    FOCUSED = "focused"

class EmotionDetector:
    def __init__(self):
        # Key facial landmarks for emotion detection
        self.EYEBROW_LEFT = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
        self.EYEBROW_RIGHT = [296, 334, 293, 300, 276, 283, 282, 295, 285, 336]
        self.EYE_LEFT = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.EYE_RIGHT = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        self.MOUTH_OUTER = [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318]
        self.MOUTH_INNER = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415]
        self.JAW = [172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323]

        # Baseline measurements (will be calibrated during first few frames)
        self.baseline_eye_ratio = None
        self.baseline_mouth_ratio = None
        self.baseline_eyebrow_height = None
        self.calibration_frames = 0
        self.calibration_target = 30  # 30 frames for calibration

    def _get_landmark_coords(self, landmarks, indices: List[int], frame_width: int, frame_height: int) -> List[Tuple[float, float]]:
        """Extract coordinates for specific landmark indices"""
        coords = []
        for idx in indices:
            if idx < len(landmarks.landmark):
                x = landmarks.landmark[idx].x * frame_width
                y = landmarks.landmark[idx].y * frame_height
                coords.append((x, y))
        return coords

    def _calculate_distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def _calculate_eye_aspect_ratio(self, eye_coords: List[Tuple[float, float]]) -> float:
        """Calculate Eye Aspect Ratio (EAR) to detect eye squinting/closing"""
        if len(eye_coords) < 6:
            return 1.0

        # Vertical distances
        v1 = self._calculate_distance(eye_coords[1], eye_coords[5])
        v2 = self._calculate_distance(eye_coords[2], eye_coords[4])

        # Horizontal distance
        h1 = self._calculate_distance(eye_coords[0], eye_coords[3])

        # EAR formula
        ear = (v1 + v2) / (2.0 * h1)
        return ear

    def _calculate_mouth_aspect_ratio(self, mouth_coords: List[Tuple[float, float]]) -> float:
        """Calculate Mouth Aspect Ratio to detect mouth expressions"""
        if len(mouth_coords) < 4:
            return 1.0

        # Vertical distance (mouth opening)
        v1 = self._calculate_distance(mouth_coords[1], mouth_coords[7])
        v2 = self._calculate_distance(mouth_coords[2], mouth_coords[6])

        # Horizontal distance (mouth width)
        h1 = self._calculate_distance(mouth_coords[0], mouth_coords[4])

        # MAR formula
        mar = (v1 + v2) / (2.0 * h1)
        return mar

    def _calculate_eyebrow_height(self, eyebrow_coords: List[Tuple[float, float]], eye_coords: List[Tuple[float, float]]) -> float:
        """Calculate average distance from eyebrow to eye (higher = raised eyebrows)"""
        if len(eyebrow_coords) == 0 or len(eye_coords) == 0:
            return 0.0

        # Average Y position of eyebrow and eye
        eyebrow_y = np.mean([coord[1] for coord in eyebrow_coords])
        eye_y = np.mean([coord[1] for coord in eye_coords])

        # Return distance (higher values = raised eyebrows)
        return abs(eyebrow_y - eye_y)

    def _detect_mouth_corners(self, face_landmarks, frame_width: int, frame_height: int) -> float:
        """Detect if mouth corners are turned up (smile) or down (frown)"""
        # Mouth corner landmarks
        left_corner = (face_landmarks.landmark[61].x * frame_width, face_landmarks.landmark[61].y * frame_height)
        right_corner = (face_landmarks.landmark[291].x * frame_width, face_landmarks.landmark[291].y * frame_height)

        # Center of mouth
        mouth_center = (face_landmarks.landmark[13].x * frame_width, face_landmarks.landmark[13].y * frame_height)

        # Calculate if corners are above or below center line
        left_relative = left_corner[1] - mouth_center[1]  # Negative = raised (smile)
        right_relative = right_corner[1] - mouth_center[1]  # Negative = raised (smile)

        # Average corner position (negative = smile, positive = frown)
        corner_position = (left_relative + right_relative) / 2
        return -corner_position  # Invert so positive = smile, negative = frown

    def calibrate(self, face_landmarks, frame_width: int, frame_height: int):
        """Calibrate baseline measurements from first few frames"""
        if self.calibration_frames >= self.calibration_target:
            return

        # Get coordinates for analysis
        left_eye_coords = self._get_landmark_coords(face_landmarks, self.EYE_LEFT[:6], frame_width, frame_height)
        right_eye_coords = self._get_landmark_coords(face_landmarks, self.EYE_RIGHT[:6], frame_width, frame_height)
        mouth_coords = self._get_landmark_coords(face_landmarks, self.MOUTH_OUTER[:8], frame_width, frame_height)
        left_eyebrow_coords = self._get_landmark_coords(face_landmarks, self.EYEBROW_LEFT[:5], frame_width, frame_height)

        # Calculate current measurements
        left_ear = self._calculate_eye_aspect_ratio(left_eye_coords)
        right_ear = self._calculate_eye_aspect_ratio(right_eye_coords)
        current_eye_ratio = (left_ear + right_ear) / 2

        current_mouth_ratio = self._calculate_mouth_aspect_ratio(mouth_coords)
        current_eyebrow_height = self._calculate_eyebrow_height(left_eyebrow_coords, left_eye_coords)

        # Update running averages
        if self.baseline_eye_ratio is None:
            self.baseline_eye_ratio = current_eye_ratio
            self.baseline_mouth_ratio = current_mouth_ratio
            self.baseline_eyebrow_height = current_eyebrow_height
        else:
            alpha = 0.1  # Smoothing factor
            self.baseline_eye_ratio = (1-alpha) * self.baseline_eye_ratio + alpha * current_eye_ratio
            self.baseline_mouth_ratio = (1-alpha) * self.baseline_mouth_ratio + alpha * current_mouth_ratio
            self.baseline_eyebrow_height = (1-alpha) * self.baseline_eyebrow_height + alpha * current_eyebrow_height

        self.calibration_frames += 1

    def analyze_emotion(self, face_landmarks, frame_width: int, frame_height: int) -> Dict:
        """Analyze facial expression and return emotion state"""
        if self.calibration_frames < self.calibration_target:
            self.calibrate(face_landmarks, frame_width, frame_height)
            return {
                'emotion': EmotionState.NEUTRAL.value,
                'confidence': 0.0,
                'pain_level': 0.0,
                'fatigue_level': 0.0,
                'calibrating': True,
                'calibration_progress': self.calibration_frames / self.calibration_target
            }

        # Get landmark coordinates
        left_eye_coords = self._get_landmark_coords(face_landmarks, self.EYE_LEFT[:6], frame_width, frame_height)
        right_eye_coords = self._get_landmark_coords(face_landmarks, self.EYE_RIGHT[:6], frame_width, frame_height)
        mouth_coords = self._get_landmark_coords(face_landmarks, self.MOUTH_OUTER[:8], frame_width, frame_height)
        left_eyebrow_coords = self._get_landmark_coords(face_landmarks, self.EYEBROW_LEFT[:5], frame_width, frame_height)
        right_eyebrow_coords = self._get_landmark_coords(face_landmarks, self.EYEBROW_RIGHT[:5], frame_width, frame_height)

        # Calculate current measurements
        left_ear = self._calculate_eye_aspect_ratio(left_eye_coords)
        right_ear = self._calculate_eye_aspect_ratio(right_eye_coords)
        current_eye_ratio = (left_ear + right_ear) / 2

        current_mouth_ratio = self._calculate_mouth_aspect_ratio(mouth_coords)

        left_eyebrow_height = self._calculate_eyebrow_height(left_eyebrow_coords, left_eye_coords)
        right_eyebrow_height = self._calculate_eyebrow_height(right_eyebrow_coords, right_eye_coords)
        current_eyebrow_height = (left_eyebrow_height + right_eyebrow_height) / 2

        mouth_corner_position = self._detect_mouth_corners(face_landmarks, frame_width, frame_height)

        # Calculate relative changes from baseline
        eye_ratio_change = (current_eye_ratio - self.baseline_eye_ratio) / self.baseline_eye_ratio if self.baseline_eye_ratio > 0 else 0
        mouth_ratio_change = (current_mouth_ratio - self.baseline_mouth_ratio) / self.baseline_mouth_ratio if self.baseline_mouth_ratio > 0 else 0
        eyebrow_height_change = (current_eyebrow_height - self.baseline_eyebrow_height) / self.baseline_eyebrow_height if self.baseline_eyebrow_height > 0 else 0

        # Emotion detection logic
        emotion = EmotionState.NEUTRAL
        confidence = 0.5
        pain_level = 0.0
        fatigue_level = 0.0

        # Pain detection: squinted eyes + furrowed brows + downturned mouth
        if eye_ratio_change < -0.15 and eyebrow_height_change < -0.1 and mouth_corner_position < -3:
            emotion = EmotionState.PAIN
            confidence = min(1.0, abs(eye_ratio_change) + abs(eyebrow_height_change) + abs(mouth_corner_position/10))
            pain_level = min(1.0, (abs(eye_ratio_change) + abs(eyebrow_height_change)) * 2)

        # Struggling: slightly squinted eyes + raised eyebrows + neutral/tense mouth
        elif eye_ratio_change < -0.1 and eyebrow_height_change > 0.05 and abs(mouth_corner_position) < 2:
            emotion = EmotionState.STRUGGLING
            confidence = min(1.0, abs(eye_ratio_change) + eyebrow_height_change)
            pain_level = min(0.7, abs(eye_ratio_change) * 2)

        # Tired: droopy eyes + lowered eyebrows + neutral mouth
        elif eye_ratio_change < -0.2 and eyebrow_height_change < -0.05 and abs(mouth_corner_position) < 2:
            emotion = EmotionState.TIRED
            confidence = min(1.0, abs(eye_ratio_change) + abs(eyebrow_height_change))
            fatigue_level = min(1.0, abs(eye_ratio_change) * 2)

        # Happy: wide eyes + raised mouth corners
        elif eye_ratio_change > 0.05 and mouth_corner_position > 3:
            emotion = EmotionState.HAPPY
            confidence = min(1.0, eye_ratio_change + mouth_corner_position/10)

        # Focused: slightly raised eyebrows + neutral eyes and mouth
        elif eyebrow_height_change > 0.1 and abs(eye_ratio_change) < 0.05 and abs(mouth_corner_position) < 2:
            emotion = EmotionState.FOCUSED
            confidence = min(1.0, eyebrow_height_change)

        return {
            'emotion': emotion.value,
            'confidence': round(confidence, 3),
            'pain_level': round(pain_level, 3),
            'fatigue_level': round(fatigue_level, 3),
            'calibrating': False,
            'metrics': {
                'eye_ratio_change': round(eye_ratio_change, 3),
                'mouth_ratio_change': round(mouth_ratio_change, 3),
                'eyebrow_height_change': round(eyebrow_height_change, 3),
                'mouth_corner_position': round(mouth_corner_position, 3)
            }
        }

class FaceService:
    def __init__(self):
        self.emotion_detector = EmotionDetector()
        self.performance_mode = PerformanceMode.BALANCED

    def set_performance_mode(self, mode: PerformanceMode):
        """Set performance mode for face detection"""
        self.performance_mode = mode
        face_mesh_manager.set_performance_mode(mode)

    def process_frame(self, frame) -> Optional[Dict]:
        """Process a single frame and return face landmarks and emotion data"""
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Process frame with current performance mode
            current_face_mesh = face_mesh_manager.get_current_instance()
            results = current_face_mesh.process(rgb_frame)

            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                frame_height, frame_width = frame.shape[:2]

                # Analyze emotion
                emotion_data = self.emotion_detector.analyze_emotion(face_landmarks, frame_width, frame_height)

                # Convert landmarks to list format for JSON serialization
                landmarks_list = []
                for landmark in face_landmarks.landmark:
                    landmarks_list.append({
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z
                    })

                return {
                    'face_landmarks': landmarks_list,
                    'emotion_data': emotion_data,
                    'timestamp': time.time(),
                    'performance_mode': self.performance_mode.value
                }

            return None

        except Exception as e:
            print(f"Face processing error: {e}")
            return None

# Global face service instance
face_service = FaceService()