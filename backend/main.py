"""
AI Rehabilitation System V3 - Complete Backend
With Authentication, Database, Session Management, AI Personalization
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import cv2
import mysql.connector
import mediapipe as mp
import numpy as np
import base64
import json
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import jwt
import hashlib
from pathlib import Path
from enum import Enum
from collections import deque
import time

# Import AI models
from ai_models import PersonalizationEngine, BiometricFeatures

# Config
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
DB_CONFIG = {
    "host": "localhost",
    "user": "root", # use your MySQL username
    "password": "123456", # use your MySQL password
    "database": "rehab_v3"
    }

# Initialize AI Personalization Engine
personalization_engine = PersonalizationEngine()

# Exercise name mapping (English to Vietnamese)
EXERCISE_NAMES = {
    "squat": "Bài Tập Squat",
    "arm_raise": "Bài Tập Giơ Tay",
    "calf_raise": "Bài Tập Nâng Bắp Chân",
    "single_leg_stand": "Bài Tập Đứng Một Chân"
}

# Error name mapping (English to Vietnamese) - for legacy data
ERROR_NAMES = {
    # Arm raise errors
    "not_high": "Góc vai chưa đủ",
    "arms_bent": "Tay không thẳng",
    "not_low": "Chưa hạ hết",
    
    # Squat errors
    "not_deep": "Gập gối chưa đủ",
    "knees_forward": "Gối đẩy ra trước",
    "not_straight": "Chưa đứng thẳng",
    
    # Calf raise errors
    "not_raised": "Chưa nâng đủ cao",
    "knees_bent": "Gập gối",
    "not_lowered": "Chưa hạ hết",
    
    # Single leg stand errors
    "knee_not_bent": "Gối chưa gập đủ sâu",
    "leg_not_behind": "Chân không ra sau"
}

def get_vietnamese_exercise_name(exercise_type: str) -> str:
    """Convert exercise type to Vietnamese name"""
    return EXERCISE_NAMES.get(exercise_type, exercise_type)

def get_vietnamese_error_name(error_name: str) -> str:
    """Convert error name to Vietnamese - handles legacy English error names"""
    return ERROR_NAMES.get(error_name, error_name)

app = FastAPI(title="Rehab System V3")

# Mount static files directory for music and assets
app.mount("/static", StaticFiles(directory="."), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=1
)


# ============= DATABASE =============
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Initialize database with complete schema"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(32) NOT NULL CHECK(role IN ('patient', 'doctor')),
            full_name VARCHAR(255),
            age INT,
            gender VARCHAR(16) CHECK(gender IN ('male', 'female', 'other')),
            height_cm REAL,
            weight_kg REAL,
            bmi REAL,
            medical_conditions TEXT,
            injury_type TEXT,
            mobility_level VARCHAR(32) CHECK(mobility_level IN ('beginner', 'intermediate', 'advanced')),
            pain_level INT CHECK(pain_level BETWEEN 0 AND 10),
            doctor_notes TEXT,
            contraindicated_exercises TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            doctor_id INT,
            FOREIGN KEY (doctor_id) REFERENCES users(id)
        )
    """)
    
    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            patient_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            total_reps INTEGER DEFAULT 0,
            correct_reps INTEGER DEFAULT 0,
            accuracy REAL DEFAULT 0,
            duration_seconds INTEGER DEFAULT 0,
            avg_heart_rate INTEGER,
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES users(id)
        )
    """)
    
    # Session frames table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_frames (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            session_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            rep_count INTEGER,
            angles TEXT,
            errors TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    
    # Errors table (aggregated)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_errors (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            session_id INTEGER NOT NULL,
            error_name TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            severity TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    
    # User exercise limits table (AI personalization)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_exercise_limits (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            user_id INTEGER NOT NULL,
            exercise_type TEXT NOT NULL,
            max_depth_angle REAL,
            min_raise_angle REAL,
            max_reps_per_set INTEGER,
            recommended_rest_seconds INTEGER,
            difficulty_score REAL,
            injury_risk_score REAL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    
    # Create default users if not exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Default doctor
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, full_name, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, ('doctor1', hash_password('doctor123'), 'doctor', 'BS. Nguyễn Văn A', datetime.now().isoformat()))
        
        doctor_id = cursor.lastrowid
        
        # Default patients
        patients = [
            ('patient1', 'patient123', 'Trần Thị B', 65, 'female'),
            ('patient2', 'patient123', 'Lê Văn C', 70, 'male'),
        ]
        
        for username, password, name, age, gender in patients:
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, full_name, age, gender, created_at, doctor_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (username, hash_password(password), 'patient', name, age, gender, datetime.now().isoformat(), doctor_id))
        
        conn.commit()
    
    conn.close()

init_db()


# ============= AUTH MODELS =============

class LoginRequest(BaseModel):
    username: str
    password: str
    role: str  # 'patient' or 'doctor'

class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    role: str = 'patient'
    doctor_id: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    medical_conditions: Optional[str] = None
    mobility_level: Optional[str] = 'beginner'
    pain_level: Optional[int] = 0

class UpdateProfileRequest(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    medical_conditions: Optional[str] = None
    mobility_level: Optional[str] = None
    pain_level: Optional[int] = None

class PersonalizedParamsRequest(BaseModel):
    exercise_type: str


# ============= AUTH FUNCTIONS =============



def create_token(user_id: int, username: str, role: str) -> str:
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(token_data = Depends(verify_token)):
    return token_data


# ============= POSE LOGIC (from V2) =============

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
    def __init__(self, exercise_type):
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
        
        # Thresholds
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
            self.hysteresis = 5
        elif exercise_type == "calf_raise":
            # Ngưỡng cho nâng gót chân - CHỈ CẦN NÂNG MỘT CHÚT
            self.down_threshold = 120  # Góc ankle khi gót chạm đất
            self.up_threshold = 140    # Góc ankle khi nâng gót lên cao
            self.hysteresis = 5
    
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



class ErrorDetector:
    def __init__(self, exercise_type):
        self.exercise_type = exercise_type
        # Track error timestamps: {error_name: first_detected_time}
        self.error_timers = {}
        self.error_threshold = 3  # seconds - only count error if persists for this long
        
    def detect_errors(self, landmarks, angles, state: ExerciseState, rep_counter: RepetitionCounter):
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
        
        left_shoulder = angles.get('left_shoulder', 0)
        right_shoulder = angles.get('right_shoulder', 0)
        left_elbow = angles.get('left_elbow', 180)
        right_elbow = angles.get('right_elbow', 180)
        
        # CHECK CẢ 2 TAY - tay thấp nhất phải đủ cao
        shoulder_angle = min(left_shoulder, right_shoulder)
        elbow_angle = min(left_elbow, right_elbow)
        
        # CHỈ CHECK LỖI Ở STATE UP (đã nâng xong)
        if state == ExerciseState.UP:
            # Error 1: Góc vai không đủ (CẢ 2 TAY phải cao)
            if shoulder_angle < 160:
                error_name = 'Góc vai chưa đủ'
                
                # Only record and show error if it persists for 1.5s
                if self._should_record_error(error_name, current_time):
                    rep_counter.add_error_to_current_rep(error_name)
                    # Show in real-time feedback only after 1.5s
                    errors.append({
                        'name': error_name,
                        'message': f' Nâng CẢ 2 TAY cao hơn! (thấp nhất: {shoulder_angle:.0f}°)',
                        'severity': 'high'
                    })
            else:
                self._clear_error_timer('Góc vai chưa đủ')
            
            # Error 2: Tay không thẳng (CẢ 2 TAY phải thẳng)
            if elbow_angle < 160:
                error_name = 'Tay không thẳng'
                
                # Only record and show error if it persists for 1.5s
                if self._should_record_error(error_name, current_time):
                    rep_counter.add_error_to_current_rep(error_name)
                    # Show in real-time feedback only after 1.5s
                    errors.append({
                        'name': error_name,
                        'message': ' Duỗi thẳng CẢ 2 TAY!',
                        'severity': 'medium'
                    })
            else:
                self._clear_error_timer('Tay không thẳng')
        else:
            # Not in UP state, clear UP state error timers
            self._clear_error_timer('Góc vai chưa đủ')
            self._clear_error_timer('Tay không thẳng')
        
        # CHECK Ở STATE DOWN (đã hạ xong)
        if state == ExerciseState.DOWN:
            # Error 3: Chưa hạ hết tay
            if shoulder_angle > 90:
                error_name = 'Chưa hạ hết'
                
                # Only record and show error if it persists for 1.5s
                if self._should_record_error(error_name, current_time):
                    rep_counter.add_error_to_current_rep(error_name)
                    # Show in real-time feedback only after 1.5s
                    errors.append({
                        'name': error_name,
                        'message': ' Hạ CẢ 2 TAY xuống hẳn!',
                        'severity': 'medium'
                    })
            else:
                self._clear_error_timer('Chưa hạ hết')
        else:
            # Not in DOWN state, clear DOWN state error timers
            self._clear_error_timer('Chưa hạ hết')
        
        return errors
    
    def _check_squat_errors(self, landmarks, angles, state, rep_counter, current_time):
        errors = []
        
        left_knee = angles.get('left_knee', 180)
        right_knee = angles.get('right_knee', 180)
        #  CHECK CẢ 2 CHÂN - chân cao nhất (góc lớn nhất) phải đủ thấp
        knee_angle = max(left_knee, right_knee)
        
        # Check ở state UP (gập gối xong)
        if state == ExerciseState.UP:
            if knee_angle > 90:
                error_name = 'Gập gối chưa đủ'
                
                # Only record and show error if it persists for 1.5s
                if self._should_record_error(error_name, current_time):
                    rep_counter.add_error_to_current_rep(error_name)
                    # Show in real-time feedback only after 1.5s
                    errors.append({
                        'name': error_name,
                        'message': f' Gập CẢ 2 CHÂN sâu hơn! (cao nhất: {knee_angle:.0f}°)',
                        'severity': 'high'
                    })
            else:
                self._clear_error_timer('Gập gối chưa đủ')
        else:
            # Not in UP state, clear UP state error timer
            self._clear_error_timer('Gập gối chưa đủ')
        
        # Check ở state DOWN (đã đứng thẳng)
        if state == ExerciseState.DOWN:
            if knee_angle < 160:
                error_name = 'Chưa đứng thẳng'
                
                # Only record and show error if it persists for 1.5s
                if self._should_record_error(error_name, current_time):
                    rep_counter.add_error_to_current_rep(error_name)
                    # Show in real-time feedback only after 1.5s
                    errors.append({
                        'name': error_name,
                        'message': ' Đứng thẳng CẢ 2 CHÂN!',
                        'severity': 'medium'
                    })
            else:
                self._clear_error_timer('Chưa đứng thẳng')
        else:
            # Not in DOWN state, clear DOWN state error timer
            self._clear_error_timer('Chưa đứng thẳng')
        
        return errors

    def _check_calf_raise_errors(self, landmarks, angles, state, rep_counter, current_time):
        errors = []
        
        left_ankle = angles.get('left_ankle', 90)
        right_ankle = angles.get('right_ankle', 90)
        left_knee = angles.get('left_knee', 180)
        right_knee = angles.get('right_knee', 180)
        
        # CHECK CẢ 2 CHÂN - chân thấp nhất phải đủ cao
        ankle_angle = min(left_ankle, right_ankle)
        knee_angle = min(left_knee, right_knee)
        
        # Check ở state UP (đã nâng gót lên)
        if state == ExerciseState.UP:
            # Error 1: Chưa nâng đủ cao (CẢ 2 CHÂN)
            if ankle_angle < 140:
                error_name = 'Chưa nâng đủ cao'
                
                # Only record and show error if it persists for 1.5s
                if self._should_record_error(error_name, current_time):
                    rep_counter.add_error_to_current_rep(error_name)
                    # Show in real-time feedback only after 1.5s
                    errors.append({
                        'name': error_name,
                        'message': f' Nâng CẢ 2 GÓT cao hơn! (thấp nhất: {ankle_angle:.0f}°)',
                        'severity': 'high'
                    })
            else:
                self._clear_error_timer('Chưa nâng đủ cao')
            
            # Error 2: Gập gối (CẢ 2 CHÂN phải thẳng)
            if knee_angle < 160:
                error_name = 'Gập gối'
                
                # Only record and show error if it persists for 1.5s
                if self._should_record_error(error_name, current_time):
                    rep_counter.add_error_to_current_rep(error_name)
                    # Show in real-time feedback only after 1.5s
                    errors.append({
                        'name': error_name,
                        'message': ' Giữ CẢ 2 CHÂN thẳng!',
                        'severity': 'medium'
                    })
            else:
                self._clear_error_timer('Gập gối')
        else:
            # Not in UP state, clear UP state error timers
            self._clear_error_timer('Chưa nâng đủ cao')
            self._clear_error_timer('Gập gối')
        
        # Check ở state DOWN (đã hạ gót xuống)
        if state == ExerciseState.DOWN:
            # Error 3: Chưa hạ hết
            if ankle_angle > 105:
                error_name = 'Chưa hạ hết'
                
                # Only record and show error if it persists for 1.5s
                if self._should_record_error(error_name, current_time):
                    rep_counter.add_error_to_current_rep(error_name)
                    # Show in real-time feedback only after 1.5s
                    errors.append({
                        'name': error_name,
                        'message': ' Hạ CẢ 2 GÓT xuống hẳn!',
                        'severity': 'medium'
                    })
            else:
                self._clear_error_timer('Chưa hạ hết')
        else:
            # Not in DOWN state, clear DOWN state error timer
            self._clear_error_timer('Chưa hạ hết')
        
        return errors
    
    # Xóa các methods không còn dùng
    # _should_report_error và _cleanup_timers không còn cần thiết
# ============= SESSION MANAGER =============

class SessionManager:
    def __init__(self):
        self.current_session = None
        self.frame_data = []
        self.active_rep_counter: Optional[RepetitionCounter] = None  # Reference to active rep counter
    
    def start_session(self, patient_id: int, exercise_name: str):
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (patient_id, exercise_name, start_time)
            VALUES (%s, %s, %s)
        """, (patient_id, exercise_name, datetime.now().isoformat()))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.current_session = {
            'id': session_id,
            'patient_id': patient_id,
            'exercise_name': exercise_name
        }
        self.frame_data = []
        
        return session_id
    
    def log_frame(self, rep_count: int, angles: dict, errors: list):
        if not self.current_session:
            return
        
        self.frame_data.append({
            'timestamp': datetime.now().isoformat(),
            'rep_count': rep_count,
            'angles': angles,
            'errors': errors
        })
    
    def end_session(self):
        if not self.current_session:
            return None
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get session start time
        cursor.execute("SELECT start_time FROM sessions WHERE id = %s", (self.current_session['id'],))
        start_time_str = cursor.fetchone()[0]
        start_time = datetime.fromisoformat(start_time_str)
        
        end_time = datetime.now()
        duration = (end_time - start_time).seconds
        
        # GET ERROR SUMMARY FROM REP COUNTER (instead of counting frames)
        error_counts = {}
        if self.active_rep_counter:
            error_summary = self.active_rep_counter.get_error_summary()
            # Convert to format expected by database
            for error_name, count in error_summary.items():
                error_counts[error_name] = {
                    'count': count,
                    'severity': 'high'  # Default severity
                }
        
        # Calculate stats
        total_reps = self.active_rep_counter.rep_count if self.active_rep_counter else 0
        
        # Calculate accuracy: Count reps with NO errors (empty error list)
        correct_reps = 0
        if self.active_rep_counter and self.active_rep_counter.all_rep_errors:
            # A rep is correct if its error list is EMPTY
            correct_reps = sum(1 for rep_errors in self.active_rep_counter.all_rep_errors if len(rep_errors) == 0)
            
            # Debug log
            print(f"\n SESSION SUMMARY:")
            print(f"   Total reps: {total_reps}")
            print(f"   All rep errors: {self.active_rep_counter.all_rep_errors}")
            print(f"   Correct reps (no errors): {correct_reps}")
            for i, rep_errors in enumerate(self.active_rep_counter.all_rep_errors, 1):
                if len(rep_errors) == 0:
                    print(f"   Rep {i}: CORRECT (no errors)")
                else:
                    print(f"   Rep {i}: ERRORS: {rep_errors}")
        
        accuracy = (correct_reps / total_reps * 100) if total_reps > 0 else 0
        
        # Update session
        cursor.execute("""
            UPDATE sessions
            SET end_time = %s, total_reps = %s, correct_reps = %s, accuracy = %s, duration_seconds = %s
            WHERE id = %s
        """, (end_time.isoformat(), total_reps, correct_reps, accuracy, duration, self.current_session['id']))
        
        # Save error stats (now per-rep counts, not per-frame!)
        for error_name, info in error_counts.items():
            cursor.execute("""
                INSERT INTO session_errors (session_id, error_name, count, severity)
                VALUES (%s, %s, %s, %s)
            """, (self.current_session['id'], error_name, info['count'], info['severity']))
        
        conn.commit()
        conn.close()
        
        result = {
            'session_id': self.current_session['id'],
            'total_reps': total_reps,
            'correct_reps': correct_reps,
            'accuracy': round(accuracy, 2),
            'duration_seconds': duration,
            'common_errors': error_counts
        }
        
        self.current_session = None
        self.frame_data = []
        self.active_rep_counter = None  # Clear reference
        
        return result


session_manager = SessionManager()


# ============= API ROUTES =============

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, role, full_name, age, gender, doctor_id
        FROM users WHERE username = %s AND password_hash = %s
    """, (request.username, hash_password(request.password)))
    
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_id, username, role, full_name, age, gender, doctor_id = user

     # Validate role matches the expected role
    if role != request.role:
        raise HTTPException(
            status_code=403, 
            detail=f"Tài khoản này là tài khoản {'bác sĩ' if role == 'doctor' else 'bệnh nhân'}. Vui lòng chọn đúng loại tài khoản."
        )
    
    # Validate role matches the expected role
    if role != request.role:
        raise HTTPException(
            status_code=403, 
            detail=f"Tài khoản này là tài khoản {'bác sĩ' if role == 'doctor' else 'bệnh nhân'}. Vui lòng chọn đúng loại tài khoản."
        )
    
    token = create_token(user_id, username, role)
    
    return {
        'token': token,
        'user': {
            'id': user_id,
            'username': username,
            'role': role,
            'full_name': full_name,
            'age': age,
            'gender': gender,
            'doctor_id': doctor_id
        }
    }


@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, full_name, age, gender, created_at, doctor_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.username,
            hash_password(request.password),
            request.role,
            request.full_name,
            request.age,
            request.gender,
            datetime.now().isoformat(),
            request.doctor_id
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        token = create_token(user_id, request.username, request.role)
        
        return {
            'token': token,
            'user': {
                'id': user_id,
                'username': request.username,
                'role': request.role,
                'full_name': request.full_name
            }
        }
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()


@app.get("/api/exercises")
async def get_exercises(current_user = Depends(get_current_user)):
    return {
        "exercises": [
            {"id": "squat", "name": "Squat (Gập gối)", "description": "Bài tập tăng cường cơ chân", "target_reps": 16, "duration_seconds": 600},
            {"id": "arm_raise", "name": "Nâng Tay", "description": "Bài tập vai và tay", "target_reps": 12, "duration_seconds": 300},
            {"id": "single_leg_stand", "name": "Đứng 1 Chân", "description": "Bài tập cân bằng và cơ chân", "target_reps": 10, "duration_seconds": 300},
            {"id": "calf_raise", "name": "Nâng Gót Chân", "description": "Bài tập tăng cường cơ bắp chân", "target_reps": 12, "duration_seconds": 300}
        ]
    }


@app.post("/api/sessions/start")
async def start_session(exercise_name: str, current_user = Depends(get_current_user)):
    session_id = session_manager.start_session(current_user['user_id'], exercise_name)
    return {'session_id': session_id}


@app.post("/api/sessions/{session_id}/end")
async def end_session(session_id: int, current_user = Depends(get_current_user)):
    result = session_manager.end_session()
    return result


@app.get("/api/sessions/my-history")
async def get_my_history(limit: int = 20, current_user = Depends(get_current_user)):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, exercise_name, start_time, total_reps, correct_reps, accuracy, duration_seconds
        FROM sessions
        WHERE patient_id = %s
        ORDER BY start_time DESC
        LIMIT %s
    """, (current_user['user_id'], limit))

    sessions = []
    for row in cursor.fetchall():
        # Get errors for this session
        cursor.execute("""
            SELECT error_name, count, severity
            FROM session_errors
            WHERE session_id = %s
        """, (row[0],))

        errors = [{'name': get_vietnamese_error_name(e[0]), 'count': e[1], 'severity': e[2]} for e in cursor.fetchall()]

        sessions.append({
            'id': row[0],
            'exercise_name': get_vietnamese_exercise_name(row[1]),
            'start_time': row[2],
            'total_reps': row[3],
            'correct_reps': row[4],
            'accuracy': row[5],
            'duration_seconds': row[6],
            'errors': errors
        })

    conn.close()
    return {'sessions': sessions}


@app.get("/api/sessions/error-analytics")
async def get_error_analytics(current_user = Depends(get_current_user)):
    """Get error analytics grouped by exercise type"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Get error statistics grouped by exercise type
    cursor.execute("""
        SELECT 
            s.exercise_name,
            se.error_name,
            SUM(se.count) as total_count,
            COUNT(DISTINCT s.id) as session_count
        FROM session_errors se
        JOIN sessions s ON se.session_id = s.id
        WHERE s.patient_id = %s
        GROUP BY s.exercise_name, se.error_name
        ORDER BY s.exercise_name, total_count DESC
    """, (current_user['user_id'],))
    
    # Organize by exercise type and merge duplicate errors after Vietnamese translation
    analytics = {}
    for row in cursor.fetchall():
        exercise_name = row[0]
        error_name = row[1]
        total_count = row[2]
        session_count = row[3]
        
        # Convert to Vietnamese names
        vietnamese_exercise = get_vietnamese_exercise_name(exercise_name)
        vietnamese_error = get_vietnamese_error_name(error_name)
        
        if vietnamese_exercise not in analytics:
            analytics[vietnamese_exercise] = {
                'exercise_name': vietnamese_exercise,
                'errors': {}  # Use dict to merge duplicates
            }
        
        # Merge errors with same Vietnamese name
        if vietnamese_error not in analytics[vietnamese_exercise]['errors']:
            analytics[vietnamese_exercise]['errors'][vietnamese_error] = {
                'error_name': vietnamese_error,
                'total_count': 0,
                'session_count': 0
            }
        
        analytics[vietnamese_exercise]['errors'][vietnamese_error]['total_count'] += total_count
        analytics[vietnamese_exercise]['errors'][vietnamese_error]['session_count'] += session_count
    
    # Convert errors dict to list and calculate averages
    result = []
    for exercise in analytics.values():
        errors_list = []
        for error in exercise['errors'].values():
            errors_list.append({
                'error_name': error['error_name'],
                'total_count': error['total_count'],
                'session_count': error['session_count'],
                'avg_per_session': round(error['total_count'] / error['session_count'], 1) if error['session_count'] > 0 else 0
            })
        result.append({
            'exercise_name': exercise['exercise_name'],
            'errors': sorted(errors_list, key=lambda x: x['total_count'], reverse=True)
        })
    
    conn.close()
    return {'analytics': result}


@app.get("/api/doctor/patients")
async def get_my_patients(current_user = Depends(get_current_user)):
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Doctors only")
    
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, full_name, age, gender, created_at
        FROM users
        WHERE role = 'patient' AND doctor_id = %s
        ORDER BY full_name
    """, (current_user['user_id'],))
    
    patients = []
    for row in cursor.fetchall():
        # Get latest session
        cursor.execute("""
            SELECT start_time, exercise_name, accuracy
            FROM sessions
            WHERE patient_id = %s
            ORDER BY start_time DESC
            LIMIT 1
        """, (row[0],))
        
        last_session = cursor.fetchone()
        
        patients.append({
            'id': row[0],
            'username': row[1],
            'full_name': row[2],
            'age': row[3],
            'gender': row[4],
            'created_at': row[5],
            'last_session': {
                'date': last_session[0] if last_session else None,
                'exercise': last_session[1] if last_session else None,
                'accuracy': last_session[2] if last_session else None
            } if last_session else None
        })
    
    conn.close()
    return {'patients': patients}


@app.get("/api/doctor/patient/{patient_id}/history")
async def get_patient_history(patient_id: int, limit: int = 20, current_user = Depends(get_current_user)):
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Doctors only")
    
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, exercise_name, start_time, total_reps, correct_reps, accuracy, duration_seconds
        FROM sessions
        WHERE patient_id = %s
        ORDER BY start_time DESC
        LIMIT %s
    """, (patient_id, limit))
    
    sessions = []
    for row in cursor.fetchall():
        # Get errors
        cursor.execute("""
            SELECT error_name, count, severity
            FROM session_errors
            WHERE session_id = %s
        """, (row[0],))
        
        errors = [{'name': get_vietnamese_error_name(e[0]), 'count': e[1], 'severity': e[2]} for e in cursor.fetchall()]
        
        sessions.append({
            'id': row[0],
            'exercise_name': get_vietnamese_exercise_name(row[1]),
            'start_time': row[2],
            'total_reps': row[3],
            'correct_reps': row[4],
            'accuracy': row[5],
            'duration_seconds': row[6],
            'errors': errors
        })
    
    conn.close()
    return {'sessions': sessions}


@app.get("/api/doctor/patient/{patient_id}/error-analytics")
async def get_patient_error_analytics(patient_id: int, current_user = Depends(get_current_user)):
    """Get error analytics for a specific patient grouped by exercise type"""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Doctors only")
    
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Get error statistics grouped by exercise type
    cursor.execute("""
        SELECT 
            s.exercise_name,
            se.error_name,
            SUM(se.count) as total_count,
            COUNT(DISTINCT s.id) as session_count
        FROM session_errors se
        JOIN sessions s ON se.session_id = s.id
        WHERE s.patient_id = %s
        GROUP BY s.exercise_name, se.error_name
        ORDER BY s.exercise_name, total_count DESC
    """, (patient_id,))
    
    # Organize by exercise type and merge duplicate errors after Vietnamese translation
    analytics = {}
    for row in cursor.fetchall():
        exercise_name = row[0]
        error_name = row[1]
        total_count = row[2]
        session_count = row[3]
        
        # Convert to Vietnamese names
        vietnamese_exercise = get_vietnamese_exercise_name(exercise_name)
        vietnamese_error = get_vietnamese_error_name(error_name)
        
        if vietnamese_exercise not in analytics:
            analytics[vietnamese_exercise] = {
                'exercise_name': vietnamese_exercise,
                'errors': {}  # Use dict to merge duplicates
            }
        
        # Merge errors with same Vietnamese name
        if vietnamese_error not in analytics[vietnamese_exercise]['errors']:
            analytics[vietnamese_exercise]['errors'][vietnamese_error] = {
                'error_name': vietnamese_error,
                'total_count': 0,
                'session_count': 0
            }
        
        analytics[vietnamese_exercise]['errors'][vietnamese_error]['total_count'] += total_count
        analytics[vietnamese_exercise]['errors'][vietnamese_error]['session_count'] += session_count
    
    # Convert errors dict to list and calculate averages
    result = []
    for exercise in analytics.values():
        errors_list = []
        for error in exercise['errors'].values():
            errors_list.append({
                'error_name': error['error_name'],
                'total_count': error['total_count'],
                'session_count': error['session_count'],
                'avg_per_session': round(error['total_count'] / error['session_count'], 1) if error['session_count'] > 0 else 0
            })
        result.append({
            'exercise_name': exercise['exercise_name'],
            'errors': sorted(errors_list, key=lambda x: x['total_count'], reverse=True)
        })
    
    conn.close()
    return {'analytics': result}


# ============= AI PERSONALIZATION ENDPOINTS =============

@app.post("/api/profile/update")
async def update_profile(
    request: UpdateProfileRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update user profile with biometric and medical data"""
    token_data = verify_token(credentials)
    user_id = token_data['user_id']
    
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Calculate BMI if height and weight provided
    bmi = None
    if request.height_cm and request.weight_kg:
        bmi = request.weight_kg / ((request.height_cm / 100) ** 2)
    
    # Update user profile
    update_fields = []
    update_values = []
    
    if request.age is not None:
        update_fields.append("age = %s")
        update_values.append(request.age)
    
    if request.gender:
        update_fields.append("gender = %s")
        update_values.append(request.gender)
    
    if request.height_cm is not None:
        update_fields.append("height_cm = %s")
        update_values.append(request.height_cm)
    
    if request.weight_kg is not None:
        update_fields.append("weight_kg = %s")
        update_values.append(request.weight_kg)
    
    if bmi is not None:
        update_fields.append("bmi = %s")
        update_values.append(bmi)
    
    if request.medical_conditions is not None:
        update_fields.append("medical_conditions = %s")
        update_values.append(request.medical_conditions)
    
    if request.mobility_level:
        update_fields.append("mobility_level = %s")
        update_values.append(request.mobility_level)
    
    if request.pain_level is not None:
        update_fields.append("pain_level = %s")
        update_values.append(request.pain_level)
    
    if update_fields:
        update_values.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, update_values)
        conn.commit()
    
    conn.close()
    
    return {
        'success': True,
        'message': 'Profile updated successfully',
        'bmi': round(bmi, 1) if bmi else None
    }


@app.get("/api/profile/me")
async def get_my_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user's profile"""
    token_data = verify_token(credentials)
    user_id = token_data['user_id']
    
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT id, username, full_name, age, gender, height_cm, weight_kg, bmi,
               medical_conditions, injury_type, mobility_level, pain_level, 
               doctor_notes, contraindicated_exercises, role
        FROM users
        WHERE id = %s
    """, (user_id,))
    
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return dict(user)


@app.post("/api/personalized-params")
async def get_personalized_params(
    request: PersonalizedParamsRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get personalized exercise parameters based on user profile
    
    Returns customized angles, reps, rest time, warnings, and recommendations
    """
    token_data = verify_token(credentials)
    user_id = token_data['user_id']
    
    # Get user data
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT age, gender, height_cm, weight_kg, bmi, medical_conditions,
               injury_type, mobility_level, pain_level
        FROM users
        WHERE id = %s
    """, (user_id,))
    
    user_row = cursor.fetchone()
    
    if not user_row:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = dict(user_row)
    
    # Calculate personalized parameters using AI engine
    params = personalization_engine.calculate_personalized_params(
        user_data,
        request.exercise_type
    )
    
    # Save to database
    cursor.execute("""
        INSERT INTO user_exercise_limits
        (user_id, exercise_type, max_depth_angle, min_raise_angle,
         max_reps_per_set, recommended_rest_seconds, difficulty_score,
         injury_risk_score, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        max_depth_angle = VALUES(max_depth_angle),
        min_raise_angle = VALUES(min_raise_angle),
        max_reps_per_set = VALUES(max_reps_per_set),
        recommended_rest_seconds = VALUES(recommended_rest_seconds),
        difficulty_score = VALUES(difficulty_score),
        injury_risk_score = VALUES(injury_risk_score),
        updated_at = VALUES(updated_at)
    """, (
        user_id,
        request.exercise_type,
        params.get('down_angle'),
        params.get('up_angle'),
        params.get('max_reps'),
        params.get('rest_seconds'),
        params.get('difficulty_score'),
        0.0,  # injury_risk_score - will implement later
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()
    
    return params


@app.websocket("/ws/exercise/{exercise_type}")
async def websocket_endpoint(websocket: WebSocket, exercise_type: str):
    await websocket.accept()
    
    angle_calc = AngleCalculator()
    rep_counter = RepetitionCounter(exercise_type)
    error_detector = ErrorDetector(exercise_type)
    
    # Store rep_counter reference in session_manager
    session_manager.active_rep_counter = rep_counter
    
    last_process_time = 0
    prev_rep_count = 0  # Track previous rep count to detect new reps
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # NEW: Handle custom thresholds
            if message['type'] == 'set_thresholds':
                thresholds = message.get('thresholds', {})
                print(f" Received custom thresholds: {thresholds}")
                
                # Apply custom thresholds to rep_counter
                if 'down_angle' in thresholds and thresholds['down_angle']:
                    if exercise_type == 'squat':
                        rep_counter.down_threshold = thresholds['down_angle']
                        print(f"   Squat down_threshold: {rep_counter.down_threshold}°")
                    elif exercise_type == 'arm_raise':
                        rep_counter.down_threshold = thresholds['down_angle']
                        print(f"   Arm raise down_threshold: {rep_counter.down_threshold}°")
                
                if 'up_angle' in thresholds and thresholds['up_angle']:
                    if exercise_type == 'squat':
                        rep_counter.up_threshold = thresholds['up_angle']
                        print(f"   Squat up_threshold: {rep_counter.up_threshold}°")
                    elif exercise_type == 'arm_raise':
                        rep_counter.up_threshold = thresholds['up_angle']
                        print(f"   Arm raise up_threshold: {rep_counter.up_threshold}°")
                
                continue
            
            if message['type'] == 'frame':
                current_time = time.time()
                if current_time - last_process_time < 0.04:
                    continue
                last_process_time = current_time
                
                try:
                    img_data = base64.b64decode(message['data'].split(',')[1])
                    nparr = np.frombuffer(img_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is None:
                        continue
                    
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = pose.process(rgb_frame)
                    
                    response = {'type': 'analysis', 'pose_detected': False}
                    
                    if results.pose_landmarks:
                        landmarks = results.pose_landmarks.landmark
                        angles = angle_calc.get_angles(landmarks, exercise_type)
                        
                        # GỌI update() thay vì count()
                        rep_count = rep_counter.update(angles)
                        
                        # Reset error timers when new rep starts
                        if rep_count > prev_rep_count:
                            error_detector.reset_timers()
                            prev_rep_count = rep_count
                        
                        # Get current state
                        current_state = rep_counter.get_state()
                        
                        # Detect errors with state and rep_counter
                        errors = error_detector.detect_errors(landmarks, angles, current_state, rep_counter)
                        
                        session_manager.log_frame(rep_count, angles, errors)
                        
                        pose_landmarks = [
                            {'x': lm.x, 'y': lm.y, 'z': lm.z, 'visibility': lm.visibility}
                            for lm in landmarks
                        ]
                        
                        # Feedback based on exercise type and state
                        if errors:
                            feedback_msg = errors[0]['message']
                        else:
                            if exercise_type == "single_leg_stand":
                                # Special feedback for single leg stand
                                if current_state == ExerciseState.READY:
                                    side_text = "trái" if rep_counter.get_current_side() == "left" else "phải"
                                    feedback_msg = f' Sẵn sàng - Co chân {side_text} lên'
                                elif current_state == ExerciseState.LIFTING:
                                    feedback_msg = ' Đang co chân lên...'
                                elif current_state == ExerciseState.HOLDING:
                                    remaining = rep_counter.get_hold_time_remaining()
                                    if remaining:
                                        feedback_msg = f' Giữ vững! Còn {int(remaining)}s'
                                    else:
                                        feedback_msg = ' Giữ vững!'
                                elif current_state == ExerciseState.LOWERING:
                                    feedback_msg = ' Hạ chân từ từ...'
                                elif current_state == ExerciseState.SWITCH_SIDE:
                                    feedback_msg = ' Tốt lắm! Đổi bên'
                                elif current_state == ExerciseState.COMPLETE:
                                    feedback_msg = ' Hoàn thành 1 rep!'
                                else:
                                    feedback_msg = ' Tư thế tốt!'
                            else:
                                # Existing feedback for other exercises
                                if current_state == ExerciseState.RAISING:
                                    feedback_msg = ' Đang nâng...'
                                elif current_state == ExerciseState.UP:
                                    feedback_msg = ' Giữ vững!'
                                elif current_state == ExerciseState.LOWERING:
                                    feedback_msg = ' Đang hạ...'
                                elif current_state == ExerciseState.DOWN:
                                    feedback_msg = ' Sẵn sàng!'
                                else:
                                    feedback_msg = ' Tư thế tốt!'
                        
                        # Additional data for single_leg_stand
                        extra_data = {}
                        if exercise_type == "single_leg_stand":
                            extra_data['hold_time_remaining'] = rep_counter.get_hold_time_remaining()
                            extra_data['current_side'] = rep_counter.get_current_side()
                        # THÊM MỚI
                        elif exercise_type == "calf_raise":
                            if current_state == ExerciseState.DOWN:
                                feedback_msg = ' Sẵn sàng - Nâng gót lên!'
                            elif current_state == ExerciseState.RAISING:
                                feedback_msg = ' Đang nâng gót...'
                            elif current_state == ExerciseState.UP:
                                feedback_msg = ' Giữ vững ở trên!'
                            elif current_state == ExerciseState.LOWERING:
                                feedback_msg = ' Hạ từ từ...'
                            else:
                                feedback_msg = ' Tư thế tốt!'
                        response = {
                            'type': 'analysis',
                            'pose_detected': True,
                            'landmarks': pose_landmarks,
                            'angles': {k: round(v, 1) if isinstance(v, (int, float)) else v for k, v in angles.items()},
                            'rep_count': rep_count,
                            'errors': errors,
                            'feedback': feedback_msg,
                            'state': current_state.value,
                            **extra_data
                        }
                    
                    await websocket.send_json(response)
                    
                except Exception as e:
                    print(f"Frame error: {e}")
                    import traceback
                    traceback.print_exc()  # In full traceback để debug
                    continue
            
            elif message['type'] == 'reset':
                rep_counter.reset()
                await websocket.send_json({'type': 'reset_confirmed'})
    
    except WebSocketDisconnect:
        print("Client disconnected")


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Rehab System V3 - Full Features")
    print("=" * 60)
    print("Server: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("\nDefault Accounts:")
    print("   Doctor: doctor1 / doctor123")
    print("   Patient: patient1 / patient123")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
