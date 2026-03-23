# WebSocket router for real-time exercise analysis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import cv2
import base64
import json
import time
import numpy as np

from models import get_db, Exercise
from services.pose_service import AngleCalculator, RepetitionCounter, pose
from services.face_service import face_service, PerformanceMode
from services.pain_service import ErrorDetector
from services.session_runtime import update_live_session, update_live_session_emotion

router = APIRouter()
SUPPORTED_BASE_TYPES = {"squat", "arm_raise", "calf_raise", "single_leg_stand"}

@router.websocket("/{exercise_type}")
async def websocket_endpoint(websocket: WebSocket, exercise_type: str, db: Session = Depends(get_db)):
    await websocket.accept()

    session_id = None
    session_id_param = websocket.query_params.get('session_id')
    if session_id_param:
        try:
            session_id = int(session_id_param)
        except ValueError:
            print(f"Invalid session_id in websocket query: {session_id_param}")

    # Load exercise thresholds from database
    custom_thresholds = None
    base_exercise_type = exercise_type  # Default: use the exercise_type directly
    exercise = db.query(Exercise).filter(Exercise.id == exercise_type).first()
    if exercise:
        custom_thresholds = {
            'down_threshold': exercise.down_threshold,
            'up_threshold': exercise.up_threshold,
            'hysteresis': exercise.hysteresis or 5.0
        }
        # Use base_exercise_type for tracking if available (for custom exercises)
        if exercise.base_exercise_type in SUPPORTED_BASE_TYPES:
            base_exercise_type = exercise.base_exercise_type
            print(f"Custom exercise '{exercise_type}' uses base type '{base_exercise_type}' for tracking")
        elif exercise_type not in SUPPORTED_BASE_TYPES:
            # Keep realtime angle rendering available for legacy custom records without valid base type.
            base_exercise_type = "squat"
            print(f"Custom exercise '{exercise_type}' has unsupported base type, fallback to '{base_exercise_type}'")
        print(f"Loaded exercise '{exercise_type}' thresholds from database: {custom_thresholds}")
    elif exercise_type not in SUPPORTED_BASE_TYPES:
        base_exercise_type = "squat"

    angle_calc = AngleCalculator()
    # Use base_exercise_type for tracking (angle calculation and state machine)
    rep_counter = RepetitionCounter(base_exercise_type, custom_thresholds)
    error_detector = ErrorDetector(base_exercise_type)

    last_process_time = 0
    prev_rep_count = 0  # Track previous rep count to detect new reps

    # Emotion tracking variables
    enable_emotion_tracking = True  # Default: enabled
    last_emotion_time = 0
    frame_counter = 0  # Counter for skipping frames
    emotion_process_interval = 5  # Process emotion every 5 frames (reduce load)
    last_emotion_data = None  # Cache last emotion data
    emotion_history = []  # Store recent emotion data for analysis
    pain_warning_count = 0
    fatigue_warning_count = 0
    last_pain_warning = 0  # Timestamp of last pain warning to avoid spam
    last_fatigue_warning = 0  # Timestamp of last fatigue warning
    warning_cooldown = 3.0  # Seconds between warnings

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle custom thresholds
            if message['type'] == 'set_thresholds':
                thresholds = message.get('thresholds', {})
                print(f" Received custom thresholds: {thresholds}")

                # Apply custom thresholds to rep_counter
                if 'down_angle' in thresholds and thresholds['down_angle']:
                    if base_exercise_type == 'squat':
                        rep_counter.down_threshold = thresholds['down_angle']
                        print(f"   Squat down_threshold: {rep_counter.down_threshold}°")
                    elif base_exercise_type == 'arm_raise':
                        rep_counter.down_threshold = thresholds['down_angle']
                        print(f"   Arm raise down_threshold: {rep_counter.down_threshold}°")

                if 'up_angle' in thresholds and thresholds['up_angle']:
                    if base_exercise_type == 'squat':
                        rep_counter.up_threshold = thresholds['up_angle']
                        print(f"   Squat up_threshold: {rep_counter.up_threshold}°")
                    elif base_exercise_type == 'arm_raise':
                        rep_counter.up_threshold = thresholds['up_angle']
                        print(f"   Arm raise up_threshold: {rep_counter.up_threshold}°")

                continue

            # Handle emotion tracking toggle
            if message['type'] == 'toggle_emotion_tracking':
                enable_emotion_tracking = message.get('enabled', True)
                print(f"Emotion tracking: {'enabled' if enable_emotion_tracking else 'disabled'}")
                await websocket.send_json({
                    'type': 'emotion_tracking_status',
                    'enabled': enable_emotion_tracking
                })
                continue

            # Handle performance mode change
            if message['type'] == 'set_performance_mode':
                mode_str = message.get('mode', 'balanced')
                try:
                    if mode_str == 'high_accuracy':
                        mode = PerformanceMode.HIGH_ACCURACY
                        emotion_process_interval = 8  # Slower processing for accuracy
                    elif mode_str == 'high_speed':
                        mode = PerformanceMode.HIGH_SPEED
                        emotion_process_interval = 3  # Faster processing
                    else:
                        mode = PerformanceMode.BALANCED
                        emotion_process_interval = 5  # Default

                    face_service.set_performance_mode(mode)
                    print(f"Performance mode set to: {mode.value}, interval: {emotion_process_interval}")

                    await websocket.send_json({
                        'type': 'performance_mode_status',
                        'mode': mode.value,
                        'interval': emotion_process_interval
                    })
                except Exception as e:
                    print(f"Error setting performance mode: {e}")
                continue

            if message['type'] == 'frame':
                current_time = time.time()
                if current_time - last_process_time < 0.04:
                    continue
                last_process_time = current_time
                frame_counter += 1  # Increment frame counter

                try:
                    img_data = base64.b64decode(message['data'].split(',')[1])
                    nparr = np.frombuffer(img_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    if frame is None:
                        continue

                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = pose.process(rgb_frame)

                    # Process face emotions (only if enabled and at intervals)
                    emotion_data = last_emotion_data  # Reuse cached data by default
                    current_warnings = []

                    # Only process face every N frames to reduce CPU load
                    if enable_emotion_tracking and (frame_counter % emotion_process_interval == 0):
                        # Resize frame for faster face processing (smaller = faster)
                        small_frame = cv2.resize(frame, (320, 240))

                        face_result = face_service.process_frame(small_frame)
                        if face_result:
                            emotion_data = face_result['emotion_data']
                            last_emotion_data = emotion_data  # Cache for next frames

                            # Store emotion history for analysis
                            emotion_history.append({
                                'timestamp': current_time,
                                'emotion': emotion_data['emotion'],
                                'pain_level': emotion_data['pain_level'],
                                'fatigue_level': emotion_data['fatigue_level'],
                                'confidence': emotion_data['confidence']
                            })

                            # Keep only last 100 emotion records (about 4 seconds of history)
                            if len(emotion_history) > 100:
                                emotion_history.pop(0)

                            # Check for pain/fatigue warnings
                            # Pain warning (high pain level or pain emotion with high confidence)
                            if (emotion_data['pain_level'] > 0.6 or
                                (emotion_data['emotion'] == 'pain' and emotion_data['confidence'] > 0.7)):
                                if current_time - last_pain_warning > warning_cooldown:
                                    pain_warning_count += 1
                                    last_pain_warning = current_time
                                    current_warnings.append({
                                        'type': 'pain',
                                        'message': 'Phát hiện biểu hiện đau đớn. Bạn có muốn dừng lại nghỉ?',
                                        'severity': 'high' if emotion_data['pain_level'] > 0.8 else 'medium'
                                    })

                            # Fatigue warning
                            if (emotion_data['fatigue_level'] > 0.7 or
                                (emotion_data['emotion'] == 'tired' and emotion_data['confidence'] > 0.7)):
                                if current_time - last_fatigue_warning > warning_cooldown:
                                    fatigue_warning_count += 1
                                    last_fatigue_warning = current_time
                                    current_warnings.append({
                                        'type': 'fatigue',
                                        'message': 'Bạn có vẻ mệt. Hãy nghỉ ngơi nếu cần thiết.',
                                        'severity': 'medium'
                                    })

                    response = {
                        'type': 'analysis',
                        'pose_detected': False,
                        'emotion': emotion_data,
                        'emotion_warnings': current_warnings,
                        'emotion_tracking_enabled': enable_emotion_tracking,
                        'pain_warning_count': pain_warning_count,
                        'fatigue_warning_count': fatigue_warning_count
                    }

                    if results.pose_landmarks:
                        landmarks = results.pose_landmarks.landmark
                        # Use base_exercise_type for angle calculation
                        angles = angle_calc.get_angles(landmarks, base_exercise_type)

                        # Update rep counter
                        rep_count = rep_counter.update(angles)

                        # Reset error timers when new rep starts
                        if rep_count > prev_rep_count:
                            error_detector.reset_timers()
                            prev_rep_count = rep_count

                        # Get current state
                        current_state = rep_counter.get_state()

                        # Detect errors
                        errors = error_detector.detect_errors(landmarks, angles, current_state, rep_counter)

                        # Keep live session summary in memory for reliable end-session stats.
                        if session_id is not None:
                            update_live_session(session_id, rep_counter)
                            # Update emotion data if available
                            if emotion_data:
                                update_live_session_emotion(session_id, emotion_data)

                        # Log frame data (this would be done in a session manager)
                        # session_manager.log_frame(rep_count, angles, errors)

                        pose_landmarks = [
                            {'x': lm.x, 'y': lm.y, 'z': lm.z, 'visibility': lm.visibility}
                            for lm in landmarks
                        ]

                        # Feedback based on exercise type and state
                        if errors:
                            feedback_msg = errors[0]['message']
                        else:
                            if base_exercise_type == "single_leg_stand":
                                # Special feedback for single leg stand
                                if current_state.value == "ready":
                                    side_text = "trái" if rep_counter.get_current_side() == "left" else "phải"
                                    feedback_msg = f' Sẵn sàng - Co chân {side_text} lên'
                                elif current_state.value == "lifting":
                                    feedback_msg = ' Đang co chân lên...'
                                elif current_state.value == "holding":
                                    remaining = rep_counter.get_hold_time_remaining()
                                    if remaining:
                                        feedback_msg = f' Giữ vững! Còn {int(remaining)}s'
                                    else:
                                        feedback_msg = ' Giữ vững!'
                                elif current_state.value == "lowering":
                                    feedback_msg = ' Hạ chân từ từ...'
                                elif current_state.value == "switch_side":
                                    feedback_msg = ' Tốt lắm! Đổi bên'
                                elif current_state.value == "complete":
                                    feedback_msg = ' Hoàn thành 1 rep!'
                                else:
                                    feedback_msg = ' Tư thế tốt!'
                            else:
                                # Existing feedback for other exercises
                                if current_state.value == "raising":
                                    feedback_msg = ' Đang nâng...'
                                elif current_state.value == "up":
                                    feedback_msg = ' Giữ vững!'
                                elif current_state.value == "lowering":
                                    feedback_msg = ' Đang hạ...'
                                elif current_state.value == "down":
                                    feedback_msg = ' Sẵn sàng!'
                                else:
                                    feedback_msg = ' Tư thế tốt!'

                        # Additional data for single_leg_stand
                        extra_data = {}
                        if base_exercise_type == "single_leg_stand":
                            extra_data['hold_time_remaining'] = rep_counter.get_hold_time_remaining()
                            extra_data['current_side'] = rep_counter.get_current_side()
                        # Additional feedback for calf_raise
                        elif base_exercise_type == "calf_raise":
                            if current_state.value == "down":
                                feedback_msg = ' Sẵn sàng - Nâng gót lên!'
                            elif current_state.value == "raising":
                                feedback_msg = ' Đang nâng gót...'
                            elif current_state.value == "up":
                                feedback_msg = ' Giữ vững ở trên!'
                            elif current_state.value == "lowering":
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
                            # Add emotion data
                            'emotion': emotion_data,
                            'emotion_warnings': current_warnings,
                            'emotion_tracking_enabled': enable_emotion_tracking,
                            'pain_warning_count': pain_warning_count,
                            'fatigue_warning_count': fatigue_warning_count,
                            **extra_data
                        }

                    await websocket.send_json(response)

                except Exception as e:
                    print(f"Frame error: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

            elif message['type'] == 'reset':
                rep_counter.reset()
                await websocket.send_json({'type': 'reset_confirmed'})

    except WebSocketDisconnect:
        if session_id is not None:
            update_live_session(session_id, rep_counter)
        print("Client disconnected")