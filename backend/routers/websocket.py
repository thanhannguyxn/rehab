# WebSocket router for real-time exercise analysis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import cv2
import base64
import json
import time
import numpy as np

from models import get_db
from services.pose_service import AngleCalculator, RepetitionCounter, pose
from services.pain_service import ErrorDetector
from services.session_runtime import update_live_session, buffer_frame

router = APIRouter()

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

    angle_calc = AngleCalculator()
    rep_counter = RepetitionCounter(exercise_type)
    error_detector = ErrorDetector(exercise_type)

    last_process_time = 0
    prev_rep_count = 0
    last_buffer_time = 0.0  # For post-session face pain sampling

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

                    # Sample one frame every 5 s for post-session pain analysis
                    # (before pose decode check — face analysis handles its own decoding)
                    if session_id is not None and current_time - last_buffer_time >= 5.0:
                        buffer_frame(session_id, img_data)
                        last_buffer_time = current_time
                        print(f"[websocket] Buffered frame for session {session_id}")

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
                            if exercise_type == "single_leg_stand":
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
                        if exercise_type == "single_leg_stand":
                            extra_data['hold_time_remaining'] = rep_counter.get_hold_time_remaining()
                            extra_data['current_side'] = rep_counter.get_current_side()
                        # Additional feedback for calf_raise
                        elif exercise_type == "calf_raise":
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