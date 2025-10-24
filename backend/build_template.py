import cv2
import mediapipe as mp
import numpy as np
import json

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

def calculate_angle(a, b, c):
    """
    Calculates the angle between three points (A, B, C) where B is the vertex.
    The points are expected to be (x, y) coordinates or (x, y, z) coordinates.
    """
    # Convert points to numpy arrays
    a = np.array(a)  # First point
    b = np.array(b)  # Vertex
    c = np.array(c)  # End point

    # Calculate vectors
    ba = a - b
    bc = c - b

    # Calculate the dot product and magnitudes
    dot_product = np.dot(ba, bc)
    magnitude_ba = np.linalg.norm(ba)
    magnitude_bc = np.linalg.norm(bc)
    
    # Check for zero magnitude to avoid division by zero
    if magnitude_ba == 0 or magnitude_bc == 0:
        return None  # Return None if angle is undefined

    # Calculate the cosine of the angle
    cosine_angle = dot_product / (magnitude_ba * magnitude_bc)

    # Ensure the cosine value is within the valid range [-1, 1]
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)

    # Calculate the angle in radians
    angle_radians = np.arccos(cosine_angle)

    # Convert the angle to degrees
    angle_degrees = np.degrees(angle_radians)

    return angle_degrees

# --- Main Template Builder Logic ---

# ! IMPORTANT: Change this to the path of your downloaded "Sit to Stand" video
video_path = "D:\AI rehabilition system\Sit to Stand.mp4"

# This list will store all the angle data for each frame
golden_template_data = []

cap = cv2.VideoCapture(video_path)

# Check if video opened successfully
if not cap.isOpened():
    print(f"Error: Could not open video file {video_path}")
    exit()

frame_number = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        # End of video
        break

    # Recolor image to RGB for MediaPipe
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False

    # Make detection
    results = pose.process(image)

    # Recolor back to BGR (not needed for processing, but good practice)
    # image.flags.writeable = True
    # image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    frame_data = {"frame": frame_number, "angles": {}}

    try:
        landmarks = results.pose_landmarks.landmark

        # Get coordinates for angle calculation (using LEFT side)
        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
               landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                 landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

        # Calculate angles
        knee_angle = calculate_angle(hip, knee, ankle)
        hip_angle = calculate_angle(shoulder, hip, knee)

        # Store the calculated angles
        if knee_angle is not None:
            frame_data["angles"]["knee_angle"] = knee_angle
        if hip_angle is not None:
            frame_data["angles"]["hip_angle"] = hip_angle
        
        # You could add more angles here (e.g., right side, back)
        
    except Exception as e:
        # Person was not detected in this frame, store empty data
        print(f"Warning: No pose detected in frame {frame_number}. {e}")
        pass
    
    # Add the data for this frame to our main list
    golden_template_data.append(frame_data)
    frame_number += 1

# --- Save the Data ---
output_filename = "golden_template.json"
with open(output_filename, 'w') as f:
    json.dump(golden_template_data, f, indent=4)

# Release resources
cap.release()
pose.close()

print(f"Success! Processed {frame_number} frames.")
print(f"Golden standard template saved to: {output_filename}")