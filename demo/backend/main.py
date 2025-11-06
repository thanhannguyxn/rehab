"""
AI Rehabilitation System V3 - Complete Backend
With Authentication, Database, Session Management
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import cv2
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

# Config
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
DB_PATH = Path("rehab_v3.db")

app = FastAPI(title="Rehab System V3")

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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('patient', 'doctor')),
            full_name TEXT,
            age INTEGER,
            gender TEXT,
            created_at TEXT NOT NULL,
            doctor_id INTEGER,
            FOREIGN KEY (doctor_id) REFERENCES users(id)
        )
    """)

    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            error_name TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            severity TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    conn.commit()

    # Create default users if not exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Default doctor
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, full_name, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, ('doctor1', hash_password('doctor123'), 'doctor', 'BS. Nguyễn Văn A', datetime.now().isoformat()))

        doctor_id = cursor.lastrowid

        # Default patients
        patients = [
            ('patient1', 'patient123', 'Trần Thị B', 65, 'Nữ'),
            ('patient2', 'patient123', 'Lê Văn C', 70, 'Nam'),
        ]

        for username, password, name, age, gender in patients:
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, full_name, age, gender, created_at, doctor_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (username, hash_password(password), 'patient', name, age, gender, datetime.now().isoformat(), doctor_id))

        conn.commit()

    conn.close()

init_db()


# ============= AUTH MODELS =============

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    role: str = 'patient'
    doctor_id: Optional[int] = None


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
        return {}


class RepetitionCounter:
    def __init__(self, exercise_type):
        self.exercise_type = exercise_type
        self.counter = 0
        self.state = "down"
        self.angle_history = []

        self.thresholds = {
            'squat': {'down': 100, 'up': 160},
            'arm_raise': {'down': 90, 'up': 150},
        }

    def count(self, angles):
        if self.exercise_type not in self.thresholds:
            return self.counter

        if self.exercise_type == "squat":
            primary_angle = angles.get('right_knee', 180)
        elif self.exercise_type == "arm_raise":
            left = angles.get('left_shoulder', 0)
            right = angles.get('right_shoulder', 0)
            primary_angle = (left + right) / 2
        else:
            return self.counter

        self.angle_history.append(primary_angle)
        if len(self.angle_history) > 3:
            self.angle_history.pop(0)

        smooth_angle = np.mean(self.angle_history)
        thresholds = self.thresholds[self.exercise_type]

        if smooth_angle < thresholds['down']:
            if self.state == "up":
                self.state = "down"

        if smooth_angle > thresholds['up']:
            if self.state == "down":
                self.counter += 1
                self.state = "up"

        return self.counter

    def reset(self):
        self.counter = 0
        self.state = "down"
        self.angle_history = []


class ErrorDetector:
    def __init__(self, exercise_type):
        self.exercise_type = exercise_type

    def detect_errors(self, landmarks, angles):
        if self.exercise_type == "squat":
            return self._check_squat_errors(landmarks, angles)
        elif self.exercise_type == "arm_raise":
            return self._check_arm_raise_errors(landmarks, angles)
        return []

    def _check_squat_errors(self, landmarks, angles):
        errors = []

        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]

        if left_knee.x > left_ankle.x + 0.05:
            errors.append({'name': 'knees_forward', 'message': 'Đầu gối vượt quá mũi chân', 'severity': 'high'})

        knee_angle = angles.get('right_knee', 180)
        if knee_angle > 130:
            errors.append({'name': 'not_deep', 'message': 'Chưa xuống đủ sâu', 'severity': 'low'})

        return errors

    def _check_arm_raise_errors(self, landmarks, angles):
        errors = []

        left_elbow = angles.get('left_elbow', 180)
        right_elbow = angles.get('right_elbow', 180)

        if left_elbow < 150 or right_elbow < 150:
            errors.append({'name': 'arms_bent', 'message': 'Duỗi thẳng tay!', 'severity': 'medium'})

        left_shoulder = angles.get('left_shoulder', 0)
        right_shoulder = angles.get('right_shoulder', 0)
        avg = (left_shoulder + right_shoulder) / 2

        if avg < 140:
            errors.append({'name': 'not_high', 'message': 'Nâng tay cao hơn!', 'severity': 'low'})

        return errors


# ============= SESSION MANAGER =============

class SessionManager:
    def __init__(self):
        self.current_session = None
        self.frame_data = []

    def start_session(self, patient_id: int, exercise_name: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sessions (patient_id, exercise_name, start_time)
            VALUES (?, ?, ?)
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

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get session start time
        cursor.execute("SELECT start_time FROM sessions WHERE id = ?", (self.current_session['id'],))
        start_time_str = cursor.fetchone()[0]
        start_time = datetime.fromisoformat(start_time_str)

        end_time = datetime.now()
        duration = (end_time - start_time).seconds

        # Calculate stats
        total_reps = max([f['rep_count'] for f in self.frame_data], default=0)
        frames_without_errors = sum(1 for f in self.frame_data if not f['errors'])
        accuracy = (frames_without_errors / len(self.frame_data) * 100) if self.frame_data else 0
        correct_reps = int(total_reps * accuracy / 100)

        # Update session
        cursor.execute("""
            UPDATE sessions
            SET end_time = ?, total_reps = ?, correct_reps = ?, accuracy = ?, duration_seconds = ?
            WHERE id = ?
        """, (end_time.isoformat(), total_reps, correct_reps, accuracy, duration, self.current_session['id']))

        # Save error stats
        error_counts = {}
        for frame in self.frame_data:
            for error in frame['errors']:
                key = error['name']
                if key not in error_counts:
                    error_counts[key] = {'count': 0, 'severity': error['severity']}
                error_counts[key]['count'] += 1

        for error_name, info in error_counts.items():
            cursor.execute("""
                INSERT INTO session_errors (session_id, error_name, count, severity)
                VALUES (?, ?, ?, ?)
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

        return result


session_manager = SessionManager()


# ============= API ROUTES =============

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, role, full_name, age, gender, doctor_id
        FROM users WHERE username = ? AND password_hash = ?
    """, (request.username, hash_password(request.password)))

    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id, username, role, full_name, age, gender, doctor_id = user

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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, full_name, age, gender, created_at, doctor_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()


@app.get("/api/exercises")
async def get_exercises(current_user = Depends(get_current_user)):
    return {
        "exercises": [
            {"id": "squat", "name": "Squat (Gập gối)", "description": "Bài tập tăng cường cơ chân", "target_reps": 10},
            {"id": "arm_raise", "name": "Nâng Tay", "description": "Bài tập vai và tay", "target_reps": 15}
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, exercise_name, start_time, total_reps, correct_reps, accuracy, duration_seconds
        FROM sessions
        WHERE patient_id = ?
        ORDER BY start_time DESC
        LIMIT ?
    """, (current_user['user_id'], limit))

    sessions = []
    for row in cursor.fetchall():
        sessions.append({
            'id': row[0],
            'exercise_name': row[1],
            'start_time': row[2],
            'total_reps': row[3],
            'correct_reps': row[4],
            'accuracy': row[5],
            'duration_seconds': row[6]
        })

    conn.close()
    return {'sessions': sessions}


@app.get("/api/doctor/patients")
async def get_my_patients(current_user = Depends(get_current_user)):
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Doctors only")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, full_name, age, gender, created_at
        FROM users
        WHERE role = 'patient' AND doctor_id = ?
        ORDER BY full_name
    """, (current_user['user_id'],))

    patients = []
    for row in cursor.fetchall():
        # Get latest session
        cursor.execute("""
            SELECT start_time, exercise_name, accuracy
            FROM sessions
            WHERE patient_id = ?
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

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, exercise_name, start_time, total_reps, correct_reps, accuracy, duration_seconds
        FROM sessions
        WHERE patient_id = ?
        ORDER BY start_time DESC
        LIMIT ?
    """, (patient_id, limit))

    sessions = []
    for row in cursor.fetchall():
        # Get errors
        cursor.execute("""
            SELECT error_name, count, severity
            FROM session_errors
            WHERE session_id = ?
        """, (row[0],))

        errors = [{'name': e[0], 'count': e[1], 'severity': e[2]} for e in cursor.fetchall()]

        sessions.append({
            'id': row[0],
            'exercise_name': row[1],
            'start_time': row[2],
            'total_reps': row[3],
            'correct_reps': row[4],
            'accuracy': row[5],
            'duration_seconds': row[6],
            'errors': errors
        })

    conn.close()
    return {'sessions': sessions}


@app.websocket("/ws/exercise/{exercise_type}")
async def websocket_endpoint(websocket: WebSocket, exercise_type: str):
    await websocket.accept()

    angle_calc = AngleCalculator()
    rep_counter = RepetitionCounter(exercise_type)
    error_detector = ErrorDetector(exercise_type)

    last_process_time = 0

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

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
                        rep_count = rep_counter.count(angles)
                        errors = error_detector.detect_errors(landmarks, angles)

                        session_manager.log_frame(rep_count, angles, errors)

                        pose_landmarks = [
                            {'x': lm.x, 'y': lm.y, 'z': lm.z, 'visibility': lm.visibility}
                            for lm in landmarks
                        ]

                        response = {
                            'type': 'analysis',
                            'pose_detected': True,
                            'landmarks': pose_landmarks,
                            'angles': {k: round(v, 1) for k, v in angles.items()},
                            'rep_count': rep_count,
                            'errors': errors,
                            'feedback': errors[0]['message'] if errors else '✓ Tư thế tốt!'
                        }

                    await websocket.send_json(response)

                except Exception as e:
                    print(f"Frame error: {e}")
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
