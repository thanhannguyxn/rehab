"""
Exercise Recognizer Service
Uses OpenAI API to analyze exercise videos and classify movement patterns
"""
from typing import Dict, List
import numpy as np
import cv2
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

# MediaPipe imports
try:
    import mediapipe as mp
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1
    )
except ImportError:
    mp_pose = None
    pose = None

# OpenAI import
try:
    import openai
except ImportError:
    openai = None


class ExerciseRecognizer:
    """AI để nhận diện động tác từ video using OpenAI-compatible API"""

    def __init__(self):
        self.openai_client = None
        if not openai:
            return

        # Use the same LLM settings as other agents (Cerebras / any OpenAI-compatible API)
        from settings import LLM_API_KEY, LLM_API_BASE_URL, LLM_MODEL
        self._llm_model = LLM_MODEL

        api_key = LLM_API_KEY or os.getenv('OPENAI_API_KEY') or os.getenv('APP_OPENAI_API_KEY')
        base_url = LLM_API_BASE_URL or None

        if not api_key:
            return

        try:
            self.openai_client = openai.OpenAI(api_key=api_key, base_url=base_url)
        except Exception as e:
            print(f"LLM client init error: {e}")
            self.openai_client = None

    def analyze_video(self, video_path: str) -> Dict:
        """
        Main analysis pipeline:
        1. Extract frames from video
        2. MediaPipe Pose detection
        3. Calculate angle timeseries
        4. OpenAI classification & threshold suggestion
        5. Return structured results
        """
        from services.video_processor import VideoProcessor

        # 1. Extract frames
        frames = VideoProcessor.extract_frames(video_path, fps=5)

        if len(frames) < 10:
            return {
                'detected_type': 'unknown',
                'confidence': 0.0,
                'error': 'Video quá ngắn (cần ít nhất 2 giây)'
            }

        # 2. Process with MediaPipe
        if not pose:
            return {
                'detected_type': 'unknown',
                'confidence': 0.0,
                'error': 'MediaPipe không khả dụng'
            }

        landmarks_sequence = []
        for frame in frames:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_frame)

            if results.pose_landmarks:
                landmarks_sequence.append(results.pose_landmarks.landmark)

        if len(landmarks_sequence) < len(frames) * 0.5:
            return {
                'detected_type': 'unknown',
                'confidence': 0.0,
                'error': 'Không phát hiện được người trong video'
            }

        # 3. Calculate angle timeseries
        angle_timeseries = self._calculate_angle_timeseries(landmarks_sequence)

        # 4. Analyze with OpenAI
        if not self.openai_client:
            # Fallback to simple rule-based if OpenAI not available
            return self._fallback_analysis(angle_timeseries, len(frames))

        try:
            analysis_result = self._analyze_with_openai(angle_timeseries)
            return {
                'detected_type': analysis_result.get('exercise_type', 'unknown'),
                'confidence': analysis_result.get('confidence', 0.0),
                'thresholds': analysis_result.get('thresholds', {}),
                'tracking_logic': analysis_result.get('tracking_logic', {}),
                'primary_joints': analysis_result.get('primary_joints', []),
                'description': analysis_result.get('description', ''),
                'instructions': analysis_result.get('instructions', []),
                'warnings': analysis_result.get('warnings', []),
                'video_duration': len(frames) / 5
            }
        except Exception as e:
            print(f"OpenAI analysis error: {e}")
            return self._fallback_analysis(angle_timeseries, len(frames))

    def _calculate_angle(self, a, b, c) -> float:
        """Calculate angle between three points"""
        a = np.array([a.x, a.y])
        b = np.array([b.x, b.y])
        c = np.array([c.x, c.y])

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)

        if angle > 180.0:
            angle = 360 - angle

        return angle

    def _calculate_angle_timeseries(self, landmarks_sequence: List) -> Dict[str, List[float]]:
        """
        Calculate all angles across frames

        Returns:
            {
                'left_knee': [180, 179, 175, ...],
                'right_knee': [180, 178, 174, ...],
                'left_shoulder': [90, 95, 100, ...],
                ...
            }
        """
        angle_timeseries = {
            'left_knee': [],
            'right_knee': [],
            'left_shoulder': [],
            'right_shoulder': [],
            'left_ankle': [],
            'right_ankle': [],
        }

        for landmarks in landmarks_sequence:
            try:
                # Knee angles
                left_knee = self._calculate_angle(
                    landmarks[mp_pose.PoseLandmark.LEFT_HIP],
                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE],
                    landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
                )
                right_knee = self._calculate_angle(
                    landmarks[mp_pose.PoseLandmark.RIGHT_HIP],
                    landmarks[mp_pose.PoseLandmark.RIGHT_KNEE],
                    landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
                )

                # Shoulder angles
                left_shoulder = self._calculate_angle(
                    landmarks[mp_pose.PoseLandmark.LEFT_HIP],
                    landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER],
                    landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
                )
                right_shoulder = self._calculate_angle(
                    landmarks[mp_pose.PoseLandmark.RIGHT_HIP],
                    landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER],
                    landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW]
                )

                # Ankle angles
                left_ankle = self._calculate_angle(
                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE],
                    landmarks[mp_pose.PoseLandmark.LEFT_ANKLE],
                    landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX]
                )
                right_ankle = self._calculate_angle(
                    landmarks[mp_pose.PoseLandmark.RIGHT_KNEE],
                    landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE],
                    landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX]
                )

                # Store
                angle_timeseries['left_knee'].append(left_knee)
                angle_timeseries['right_knee'].append(right_knee)
                angle_timeseries['left_shoulder'].append(left_shoulder)
                angle_timeseries['right_shoulder'].append(right_shoulder)
                angle_timeseries['left_ankle'].append(left_ankle)
                angle_timeseries['right_ankle'].append(right_ankle)

            except Exception:
                continue

        return angle_timeseries

    def _analyze_with_openai(self, angle_timeseries: Dict[str, List[float]]) -> Dict:
        """
        Use OpenAI GPT-4o to analyze movement patterns and classify exercise
        """
        # Prepare angle statistics for OpenAI
        angle_stats = {}
        for angle_name, values in angle_timeseries.items():
            if len(values) > 0:
                angle_stats[angle_name] = {
                    'min': round(float(np.min(values)), 1),
                    'max': round(float(np.max(values)), 1),
                    'mean': round(float(np.mean(values)), 1),
                    'std': round(float(np.std(values)), 1),
                    'range': round(float(np.ptp(values)), 1)
                }

        # Known exercise types for reference
        known_exercises = [
            {
                'id': 'squat',
                'name': 'Squat (Gập gối)',
                'pattern': 'Deep knee flexion (90-180°), both legs move symmetrically, hip hinge movement'
            },
            {
                'id': 'arm_raise',
                'name': 'Nâng Tay',
                'pattern': 'Shoulder flexion (90-180°), arms lifting overhead, minimal knee movement'
            },
            {
                'id': 'calf_raise',
                'name': 'Nâng Gót Chân',
                'pattern': 'Ankle plantar flexion (120-140°), heels rising, knees remain straight'
            },
            {
                'id': 'single_leg_stand',
                'name': 'Đứng 1 Chân',
                'pattern': 'Single leg balance, one knee flexed with leg behind, asymmetric knee movement'
            }
        ]

        # Construct prompt
        prompt = f"""You are a physical therapy expert analyzing exercise movements from pose tracking data.

**Angle Statistics (in degrees):**
{json.dumps(angle_stats, indent=2)}

**Known Exercise Types in System:**
{json.dumps(known_exercises, indent=2)}

**Analysis Instructions:**
1. **Classify** the exercise:
   - Match to known exercise types if movement pattern is similar
   - If it's a new/custom exercise, suggest a descriptive ID (e.g., "hip_abduction", "leg_extension")
   - Provide confidence score (0-1) based on how clear the movement pattern is

2. **Calculate Thresholds** based on angle ranges:
   - down_threshold: Starting position angle (e.g., standing position for squat ~170°)
   - up_threshold: Maximum movement angle (e.g., deep squat position ~90°)
   - These thresholds are used to detect when a repetition starts/ends
   - Use the min/max from angle statistics to determine appropriate values

3. **Build Tracking Logic** for backend realtime counter:
     - `base_exercise_type` MUST be one of: `squat`, `arm_raise`, `calf_raise`, `single_leg_stand`
     - `primary_angles` is the key list used for counting reps (e.g., ["left_knee", "right_knee"])
     - `state_sequence` is the ordered state machine (e.g., ["down", "raising", "up", "lowering"])
     - `rep_completion_rule` is a short machine-readable string describing when 1 rep is counted
     - `angle_rules` is an array of constraints for error detection. Each item:
         - `angle_name`
         - `min_angle` (nullable)
         - `max_angle` (nullable)
         - `error_message`
         - `error_severity` in `low|medium|high`

3. **Generate Content** in Vietnamese:
   - description: 1-2 sentence description of the exercise
   - instructions: 3-5 step-by-step instructions
   - warnings: Safety warnings if applicable (knee issues, balance, etc.)

**Response Format (JSON only, no markdown):**
{{
  "exercise_type": "squat",
  "confidence": 0.85,
  "thresholds": {{
    "down_threshold": 165.0,
    "up_threshold": 95.0,
    "hysteresis": 5.0
  }},
    "tracking_logic": {{
        "base_exercise_type": "squat",
        "primary_angles": ["left_knee", "right_knee"],
        "state_sequence": ["down", "raising", "up", "lowering"],
        "rep_completion_rule": "count_rep_when_state_transitions_from_up_to_down",
        "angle_rules": [
            {{
                "angle_name": "left_knee",
                "min_angle": 85,
                "max_angle": 175,
                "error_message": "Goc goi trai vuot nguong an toan",
                "error_severity": "medium"
            }}
        ]
    }},
  "description": "Bài tập gập gối để tăng cường cơ đùi và mông",
  "instructions": [
    "Đứng thẳng, hai chân rộng bằng vai",
    "Từ từ hạ người xuống như ngồi xuống ghế",
    "Giữ lưng thẳng, gối không vượt qua mũi chân",
    "Đứng lên về vị trí ban đầu"
  ],
  "warnings": [
    "Không gập gối quá sâu nếu có vấn đề về khớp gối"
  ],
  "primary_joints": ["knee", "hip"]
}}

Analyze and respond with JSON only."""

        # Call LLM API — try with json_object format first, fall back without it
        try:
            response = self.openai_client.chat.completions.create(
                model=self._llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a physical therapy expert. Analyze exercise movement data and respond with structured JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
        except Exception:
            response = self.openai_client.chat.completions.create(
                model=self._llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a physical therapy expert. Analyze exercise movement data and respond with structured JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
            )

        # Parse response — strip markdown code fences if present
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        return result

    def _fallback_analysis(self, angle_timeseries: Dict[str, List[float]], frame_count: int) -> Dict:
        """
        Fallback rule-based analysis if OpenAI is not available
        """
        if not angle_timeseries or all(len(v) == 0 for v in angle_timeseries.values()):
            return {
                'detected_type': 'unknown',
                'confidence': 0.0,
                'thresholds': {},
                'description': 'Không thể phân tích',
                'instructions': [],
                'warnings': [],
                'video_duration': frame_count / 5
            }

        # Calculate variance for each angle
        variances = {}
        for angle_name, values in angle_timeseries.items():
            if len(values) > 0:
                variances[angle_name] = float(np.std(values))

        # Get max movements per joint type
        knee_movement = max(
            variances.get('left_knee', 0),
            variances.get('right_knee', 0)
        )
        shoulder_movement = max(
            variances.get('left_shoulder', 0),
            variances.get('right_shoulder', 0)
        )

        # Simple classification
        if shoulder_movement > 20 and knee_movement < 15:
            exercise_type = 'arm_raise'
            confidence = min(shoulder_movement / 40, 1.0)
        elif knee_movement > 30:
            exercise_type = 'squat'
            confidence = min(knee_movement / 50, 1.0)
        else:
            exercise_type = 'unknown'
            confidence = 0.3

        # Calculate basic thresholds
        thresholds = {}
        if exercise_type == 'squat':
            knee_values = angle_timeseries.get('left_knee', []) + angle_timeseries.get('right_knee', [])
            if knee_values:
                thresholds = {
                    'down_threshold': round(float(np.percentile(knee_values, 95)) - 10, 1),
                    'up_threshold': round(float(np.percentile(knee_values, 5)) + 10, 1),
                    'hysteresis': 5.0
                }
        elif exercise_type == 'arm_raise':
            shoulder_values = angle_timeseries.get('left_shoulder', []) + angle_timeseries.get('right_shoulder', [])
            if shoulder_values:
                thresholds = {
                    'down_threshold': round(float(np.percentile(shoulder_values, 5)) + 10, 1),
                    'up_threshold': round(float(np.percentile(shoulder_values, 95)) - 10, 1),
                    'hysteresis': 5.0
                }

        tracking_logic = {
            'base_exercise_type': exercise_type if exercise_type in {'squat', 'arm_raise', 'calf_raise', 'single_leg_stand'} else 'squat',
            'primary_angles': ['left_knee', 'right_knee'] if exercise_type == 'squat' else ['left_shoulder', 'right_shoulder'],
            'state_sequence': ['down', 'raising', 'up', 'lowering'],
            'rep_completion_rule': 'count_rep_when_state_transitions_from_up_to_down',
            'angle_rules': []
        }

        return {
            'detected_type': exercise_type,
            'confidence': confidence,
            'thresholds': thresholds,
            'tracking_logic': tracking_logic,
            'description': f'Bài tập {exercise_type}',
            'instructions': [],
            'warnings': ['Phân tích bằng rule-based (OpenAI không khả dụng)'],
            'video_duration': frame_count / 5
        }
