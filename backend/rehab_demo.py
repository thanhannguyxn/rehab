import cv2
import mediapipe as mp
import numpy as np
import json

# --- Helper Function: Load the Template ---
def load_template(filename="golden_template.json"):
    """Loads the golden template data from a JSON file."""
    print(f"Loading template from {filename}...")
    try:
        with open(filename, 'r') as f:
            template_data = json.load(f)
        valid_frames = [frame for frame in template_data if "angles" in frame and "knee_angle" in frame["angles"] and "hip_angle" in frame["angles"]]
        if not valid_frames:
            print("Error: Template file is empty or contains no valid angle data.")
            return None
        print(f"Template loaded successfully with {len(valid_frames)} valid frames.")
        return valid_frames
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        print("Please run Program 1 (build_template.py) first.")
        return None
    except Exception as e:
        print(f"Error loading template: {e}")
        return None

# --- Helper Function: Calculate Angle ---
def calculate_angle(a, b, c):
    """Calculates the angle between three points (A, B, C) where B is the vertex."""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
    return angle

# --- Helper Function: Find Closest Match ---
def find_closest_match(live_angles, template_data):
    """Finds the frame in the template that is the 'closest' match to the live pose."""
    live_knee = live_angles.get("knee_angle", 0)
    live_hip = live_angles.get("hip_angle", 0)
    
    min_distance = float('inf')
    best_match_frame = template_data[0] 

    for frame in template_data:
        template_knee = frame["angles"].get("knee_angle", 0)
        template_hip = frame["angles"].get("hip_angle", 0)
        
        distance = np.sqrt((live_knee - template_knee)**2 + (live_hip - template_hip)**2)
        
        if distance < min_distance:
            min_distance = distance
            best_match_frame = frame
            
    return best_match_frame, min_distance

# --- Main Application Logic ---

# 1. LOAD THE TEMPLATE FILE
golden_template = load_template("D:\AI rehabilition system\golden_template.json")
if golden_template is None:
    exit()

# 2. INITIALIZE MEDIAPIPE AND WEBCAM
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture("D:/AI rehabilition system/5be3e818-d252-474a-b03a-126b2602fa77.mp4") # Use 0 for webcam
# To use a test video file instead:
# cap = cv2.VideoCapture("path/to/your/test_video.mp4")

# 3. SET UP REP COUNTING AND FEEDBACK VARIABLES
rep_counter = 0
stage = "standing"  # Start in a standing position
feedback_text = "Start"
feedback_color = (255, 255, 255) # White

# Define the thresholds for the "sit" and "stand" states
# You can fine-tune these based on your template
SIT_KNEE_ANGLE = 100
STAND_KNEE_ANGLE = 160
ANGLE_TOLERANCE = 20  # Tolerance for form feedback

cv2.namedWindow('AI Rehabilitation System (Final)', cv2.WINDOW_NORMAL)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False
    results = pose.process(image)
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    live_knee_angle = 0
    live_hip_angle = 0
    correct_knee_angle = 0
    correct_hip_angle = 0

    try:
        landmarks = results.pose_landmarks.landmark

        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
               landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                 landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

        live_knee_angle = calculate_angle(hip, knee, ankle)
        live_hip_angle = calculate_angle(shoulder, hip, knee)
        
        current_live_angles = {
            "knee_angle": live_knee_angle,
            "hip_angle": live_hip_angle
        }

        # --- Repetition Counting Logic ---
        if live_knee_angle < SIT_KNEE_ANGLE:
            stage = "sitting"
        
        if live_knee_angle > STAND_KNEE_ANGLE and stage == 'sitting':
            stage = "standing"
            rep_counter += 1
            print(f"Repetition count: {rep_counter}")
            
        # --- Template Matching Logic for Feedback ---
        matched_frame, distance = find_closest_match(current_live_angles, golden_template)
        correct_knee_angle = matched_frame["angles"]["knee_angle"]
        correct_hip_angle = matched_frame["angles"]["hip_angle"]
        
        if distance < ANGLE_TOLERANCE:
            feedback_text = "Good!"
            feedback_color = (0, 255, 0) # Green
        else:
            feedback_text = "Fix Your Form!"
            feedback_color = (0, 0, 255) # Red

    except Exception as e:
        feedback_text = "No Pose Detected"
        feedback_color = (0, 0, 255) # Red
        pass

    # --- Display Information on Screen ---
    
    # Draw the main info box
    cv2.rectangle(image, (0, 0), (300, 160), (245, 117, 16), -1)

    # Display Rep Count
    cv2.putText(image, 'REPS', (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(image, str(rep_counter), (15, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Display Stage
    cv2.putText(image, 'STAGE', (150, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(image, stage, (150, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2, cv2.LINE_AA)

    # Display Feedback
    cv2.putText(image, feedback_text, (15, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 1, feedback_color, 2, cv2.LINE_AA)

    # Draw the pose landmarks
    mp_drawing.draw_landmarks(image, results.pose_landmarks,
                                mp_pose.POSE_CONNECTIONS,
                                mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
                                )

    cv2.imshow('AI Rehabilitation System (Final)', image)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pose.close()