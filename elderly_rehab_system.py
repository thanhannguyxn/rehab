import cv2
import numpy as np
import time
import csv
import os
import json
import pickle
from datetime import datetime
import tensorflow as tf
import tensorflow_hub as hub
from ultralytics import YOLO

# Constants
FONT = cv2.FONT_HERSHEY_SIMPLEX
WHITE = (255, 255, 255)
YELLOW = (0, 255, 255)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
BLUE = (255, 0, 0)
BLACK = (0, 0, 0)
ORANGE = (0, 165, 255)
PURPLE = (128, 0, 128)

# Exercise parameters
EXERCISE_TIME = 30  # seconds per exercise
REST_TIME = 10  # seconds between exercises

# Custom pose parameters
CUSTOM_POSES_DIR = "custom_poses"
POSE_SIMILARITY_THRESHOLD = 0.75  # Threshold for pose matching

# MoveNet keypoint indices
NOSE = 0
LEFT_EYE = 1
RIGHT_EYE = 2
LEFT_EAR = 3
RIGHT_EAR = 4
LEFT_SHOULDER = 5
RIGHT_SHOULDER = 6
LEFT_ELBOW = 7
RIGHT_ELBOW = 8
LEFT_WRIST = 9
RIGHT_WRIST = 10
LEFT_HIP = 11
RIGHT_HIP = 12
LEFT_KNEE = 13
RIGHT_KNEE = 14
LEFT_ANKLE = 15
RIGHT_ANKLE = 16

class ElderlyRehabSystem:
    def __init__(self):
        self.cap = None
        self.exercise_list = [
            {"name": "Arm Raises", "reps": 0, "stage": None},
            {"name": "Knee Bends", "reps": 0, "stage": None},
            {"name": "Shoulder Rotations", "reps": 0, "stage": None}
        ]
        self.current_exercise = 0
        self.mode = "menu"  # menu, exercise, rest, report, custom_pose, video_processing
        self.start_time = 0
        self.performance_data = []
        self.feedback_message = ""
        self.feedback_color = WHITE

        # Load MoveNet model - using Thunder for better accuracy
        print("Loading MoveNet model...")
        # Use Thunder model instead of Lightning for better accuracy
        self.model = hub.load('https://tfhub.dev/google/movenet/singlepose/thunder/4')
        self.movenet = self.model.signatures['serving_default']
        print("MoveNet Thunder model loaded successfully!")

        # Initialize YOLO model for improved pose detection
        try:
            self.yolo_model = YOLO("yolov8n-pose.pt")
            self.use_yolo = True
            print("YOLO model loaded successfully")
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            self.use_yolo = False

        # Pose tracking variables
        self.keypoints = None
        self.keypoint_scores = None
        self.prev_angles = {}
        self.angle_history = {
            "right_shoulder": [],
            "left_shoulder": [],
            "right_knee": [],
            "left_knee": [],
            "right_elbow": [],
            "left_elbow": []
        }
        self.angle_history_size = 8  # Increased for smoother tracking
        self.angle_thresholds = {
            "Arm Raises": {"angle_name": "right_shoulder", "up": 100, "down": 40},
            "Knee Bends": {"angle_name": "right_knee", "up": 160, "down": 140},
            "Shoulder Rotations": {"angle_name": "right_elbow", "up": 90, "down": 50}
        }

        # Pose validation variables
        self.min_keypoint_score = 0.5  # Higher threshold for better accuracy
        self.valid_pose_counter = 0
        self.required_valid_frames = 3  # Number of consecutive valid frames needed

        # Custom pose variables
        self.custom_poses = {}
        self.current_custom_pose = None
        self.recording_pose = False
        self.pose_frames = []
        self.video_path = None
        self.video_cap = None
        self.video_frame_count = 0
        self.video_current_frame = 0

        # Create custom poses directory if it doesn't exist
        if not os.path.exists(CUSTOM_POSES_DIR):
            os.makedirs(CUSTOM_POSES_DIR)

        # Load existing custom poses
        self.load_custom_poses()

    def detect_pose(self, frame):
        """
        Detect human pose in the frame using YOLOv8 Pose if available, else MoveNet Thunder
        """
        if hasattr(self, "use_yolo") and self.use_yolo:
            yolo_out = self.detect_pose_yolo(frame)
            if yolo_out is not None:
                self.keypoints, scores = yolo_out
                self.keypoint_scores = np.array(scores)
                is_valid_pose = self.validate_pose()
                return self.draw_pose(frame, is_valid_pose)
        # Resize and convert the image to tensor
        img = frame.copy()
        img = tf.image.resize_with_pad(np.expand_dims(img, axis=0), 256, 256)  # Larger input size for Thunder
        img = tf.cast(img, dtype=tf.int32)

        # Detection
        results = self.movenet(img)
        keypoints = results['output_0'].numpy()[0][0]

        # Extract keypoints and scores
        self.keypoints = keypoints[:, :2]  # First two values are y, x coordinates
        self.keypoint_scores = keypoints[:, 2]  # Third value is the confidence score

        # Validate pose
        is_valid_pose = self.validate_pose()

        # Draw the pose on the frame
        return self.draw_pose(frame, is_valid_pose)

    def detect_pose_yolo(self, frame):
        """Detect pose using YOLO and return normalized keypoints and scores"""
        if not hasattr(self, "use_yolo") or not self.use_yolo:
            return None
        h, w = frame.shape[:2]
        try:
            results = self.yolo_model.predict(frame, verbose=False)
        except Exception:
            return None
        if len(results) == 0 or results[0].keypoints is None or len(results[0].keypoints) == 0:
            return None
        kps = results[0].keypoints.data[0].cpu().numpy()  # expected shape [17, 3] (x, y, conf)
        # Convert to normalized (y, x) consistent with MoveNet
        xs = kps[:, 0]
        ys = kps[:, 1]
        confs = kps[:, 2] if kps.shape[1] >= 3 else np.ones_like(xs) * 0.5
        norm_keypoints = np.stack([ys / h, xs / w], axis=1)
        return norm_keypoints, confs

    def validate_pose(self):
        """
        Validate if the detected pose is reliable
        """
        # Check if key points are detected with sufficient confidence
        key_points = [
            RIGHT_SHOULDER, LEFT_SHOULDER,
            RIGHT_ELBOW, LEFT_ELBOW,
            RIGHT_HIP, LEFT_HIP,
            RIGHT_KNEE, LEFT_KNEE
        ]

        valid_count = sum(1 for kp in key_points if self.keypoint_scores[kp] > self.min_keypoint_score)
        is_valid = valid_count >= 6  # At least 6 key points must be valid

        # Track consecutive valid frames
        if is_valid:
            self.valid_pose_counter += 1
        else:
            self.valid_pose_counter = 0

        return self.valid_pose_counter >= self.required_valid_frames

    def draw_pose(self, frame, is_valid_pose):
        """
        Draw the detected pose on the frame
        """
        h, w, _ = frame.shape

        # Draw keypoints with color based on confidence
        for i, (y, x) in enumerate(self.keypoints):
            confidence = self.keypoint_scores[i]
            if confidence > 0.3:  # Show lower confidence points but with different colors
                # Convert normalized coordinates to pixel values
                kp_x = int(x * w)
                kp_y = int(y * h)

                # Color based on confidence
                if confidence > self.min_keypoint_score:
                    color = GREEN
                    radius = 6
                else:
                    color = YELLOW
                    radius = 4

                # Draw circle at keypoint
                cv2.circle(frame, (kp_x, kp_y), radius, color, -1)

        # Draw connections between keypoints
        connections = [
            (LEFT_SHOULDER, RIGHT_SHOULDER),
            (LEFT_SHOULDER, LEFT_ELBOW),
            (LEFT_ELBOW, LEFT_WRIST),
            (RIGHT_SHOULDER, RIGHT_ELBOW),
            (RIGHT_ELBOW, RIGHT_WRIST),
            (LEFT_SHOULDER, LEFT_HIP),
            (RIGHT_SHOULDER, RIGHT_HIP),
            (LEFT_HIP, RIGHT_HIP),
            (LEFT_HIP, LEFT_KNEE),
            (LEFT_KNEE, LEFT_ANKLE),
            (RIGHT_HIP, RIGHT_KNEE),
            (RIGHT_KNEE, RIGHT_ANKLE)
        ]

        for connection in connections:
            if (self.keypoint_scores[connection[0]] > 0.3 and
                self.keypoint_scores[connection[1]] > 0.3):

                start_x = int(self.keypoints[connection[0]][1] * w)
                start_y = int(self.keypoints[connection[0]][0] * h)
                end_x = int(self.keypoints[connection[1]][1] * w)
                end_y = int(self.keypoints[connection[1]][0] * h)

                # Line thickness based on confidence
                thickness = 2
                if (self.keypoint_scores[connection[0]] > self.min_keypoint_score and
                    self.keypoint_scores[connection[1]] > self.min_keypoint_score):
                    thickness = 3

                cv2.line(frame, (start_x, start_y), (end_x, end_y), BLUE, thickness)

        # Draw pose validity indicator
        if not is_valid_pose:
            cv2.putText(frame, "Pose Not Detected", (10, 60),
                       FONT, 0.7, RED, 2, cv2.LINE_AA)

        return frame

    def calculate_angle(self, a, b, c):
        """
        Calculate the angle between three points
        """
        if (self.keypoint_scores[a] < 0.4 or
            self.keypoint_scores[b] < 0.4 or
            self.keypoint_scores[c] < 0.4):
            return None

        a_pos = (self.keypoints[a][1], self.keypoints[a][0])  # x, y
        b_pos = (self.keypoints[b][1], self.keypoints[b][0])
        c_pos = (self.keypoints[c][1], self.keypoints[c][0])

        # Calculate vectors
        ba = np.array([a_pos[0] - b_pos[0], a_pos[1] - b_pos[1]])
        bc = np.array([c_pos[0] - b_pos[0], c_pos[1] - b_pos[1]])

        # Calculate dot product and magnitudes
        dot_product = np.dot(ba, bc)
        magnitude_ba = np.linalg.norm(ba)
        magnitude_bc = np.linalg.norm(bc)

        # Calculate angle in degrees
        if magnitude_ba * magnitude_bc == 0:
            return None

        cosine_angle = dot_product / (magnitude_ba * magnitude_bc)
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        angle_degrees = np.degrees(angle)

        return angle_degrees

    def get_joint_angles(self):
        """
        Calculate relevant joint angles for exercises and apply smoothing
        """
        angles = {}

        # Right shoulder angle (for arm raises)
        angles["right_shoulder"] = self.calculate_angle(
            RIGHT_ELBOW, RIGHT_SHOULDER, RIGHT_HIP)

        # Left shoulder angle
        angles["left_shoulder"] = self.calculate_angle(
            LEFT_ELBOW, LEFT_SHOULDER, LEFT_HIP)

        # Right elbow angle (for shoulder rotations)
        angles["right_elbow"] = self.calculate_angle(
            RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST)

        # Left elbow angle
        angles["left_elbow"] = self.calculate_angle(
            LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST)

        # Right knee angle (for knee bends)
        angles["right_knee"] = self.calculate_angle(
            RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE)

        # Left knee angle
        angles["left_knee"] = self.calculate_angle(
            LEFT_HIP, LEFT_KNEE, LEFT_ANKLE)

        # Apply smoothing to all angles
        for angle_name, angle_value in angles.items():
            if angle_value is not None:
                # Add current angle to history
                if len(self.angle_history[angle_name]) >= self.angle_history_size:
                    self.angle_history[angle_name].pop(0)
                self.angle_history[angle_name].append(angle_value)

                # Calculate smoothed angle (average of recent values)
                if len(self.angle_history[angle_name]) > 0:
                    # Use weighted average - recent values have more weight
                    weights = np.linspace(0.5, 1.0, len(self.angle_history[angle_name]))
                    weighted_sum = sum(w * a for w, a in zip(weights, self.angle_history[angle_name]))
                    angles[angle_name] = weighted_sum / sum(weights)

        return angles

    def draw_angle_visualization(self, image, angle_name, current_angle, threshold_data):
        """Draw visual representation of the current angle and thresholds"""
        h, w, _ = image.shape

        # Draw angle gauge in bottom right corner
        gauge_width = 200
        gauge_height = 30
        x_start = w - gauge_width - 20
        y_start = h - 200

        # Draw background
        cv2.rectangle(image, (x_start, y_start),
                     (x_start + gauge_width, y_start + gauge_height),
                     (50, 50, 50), -1)

        # Draw threshold markers
        up_x = x_start + int((threshold_data["up"] / 180) * gauge_width)
        down_x = x_start + int((threshold_data["down"] / 180) * gauge_width)

        cv2.line(image, (up_x, y_start), (up_x, y_start + gauge_height), GREEN, 2)
        cv2.line(image, (down_x, y_start), (down_x, y_start + gauge_height), RED, 2)

        # Draw current angle marker
        current_x = x_start + int((current_angle / 180) * gauge_width)
        current_x = max(x_start, min(x_start + gauge_width, current_x))  # Clamp to gauge width

        cv2.circle(image, (current_x, y_start + gauge_height // 2), 8, YELLOW, -1)

        # Draw labels
        cv2.putText(image, f"Angle Gauge: {angle_name}", (x_start, y_start - 10),
                   FONT, 0.6, WHITE, 1, cv2.LINE_AA)
        cv2.putText(image, "0°", (x_start, y_start + gauge_height + 20),
                   FONT, 0.5, WHITE, 1, cv2.LINE_AA)
        cv2.putText(image, "180°", (x_start + gauge_width - 30, y_start + gauge_height + 20),
                   FONT, 0.5, WHITE, 1, cv2.LINE_AA)

    def draw_menu(self, image):
        """Draw the main menu interface"""
        h, w, _ = image.shape

        # Draw semi-transparent overlay
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)

        # Title
        cv2.putText(image, "AI Home Rehabilitation System", (int(w/2) - 300, 80),
                    FONT, 1.2, WHITE, 2, cv2.LINE_AA)

        # Exercise list
        cv2.putText(image, "Available Exercises:", (int(w/2) - 250, 150),
                    FONT, 1, WHITE, 2, cv2.LINE_AA)

        for i, exercise in enumerate(self.exercise_list):
            cv2.putText(image, f"{i+1}. {exercise['name']}", (int(w/2) - 200, 200 + i*50),
                        FONT, 0.8, WHITE, 2, cv2.LINE_AA)

        # Custom pose info
        if self.custom_poses:
            cv2.putText(image, f"Custom Poses Available: {len(self.custom_poses)}",
                       (int(w/2) - 250, h - 200), FONT, 0.8, YELLOW, 2, cv2.LINE_AA)

        # Instructions
        cv2.putText(image, "Press 'S' to Start Rehabilitation Session", (int(w/2) - 250, h - 150),
                    FONT, 0.8, GREEN, 2, cv2.LINE_AA)
        cv2.putText(image, "Press 'C' to Access Custom Poses", (int(w/2) - 250, h - 120),
                    FONT, 0.8, ORANGE, 2, cv2.LINE_AA)
        cv2.putText(image, "Press 'Q' to Quit", (int(w/2) - 250, h - 90),
                    FONT, 0.8, RED, 2, cv2.LINE_AA)

    def draw_exercise_ui(self, image):
        """Draw the exercise interface with real-time feedback"""
        h, w, _ = image.shape
        exercise = self.exercise_list[self.current_exercise]

        # Calculate remaining time
        elapsed_time = time.time() - self.start_time
        remaining_time = max(0, EXERCISE_TIME - elapsed_time)

        # Get joint angles
        angles = self.get_joint_angles()

        # Process exercise-specific logic
        threshold_data = self.angle_thresholds[exercise["name"]]
        angle_name = threshold_data["angle_name"]

        if angle_name in angles and angles[angle_name] is not None:
            current_angle = angles[angle_name]

            # Display the current angle for debugging
            cv2.putText(image, f"{angle_name}: {int(current_angle)}", (w - 200, 60),
                       FONT, 0.6, WHITE, 1, cv2.LINE_AA)

            # Draw angle visualization
            self.draw_angle_visualization(image, angle_name, current_angle, threshold_data)

            # Check for rep completion based on angle thresholds
            if exercise["stage"] is None:
                exercise["stage"] = "down"  # Initialize stage

            if exercise["stage"] == "down" and current_angle > threshold_data["up"]:
                exercise["stage"] = "up"
                self.feedback_message = "Good! Now lower slowly..."
                self.feedback_color = GREEN

            elif exercise["stage"] == "up" and current_angle < threshold_data["down"]:
                exercise["stage"] = "down"
                exercise["reps"] += 1
                self.feedback_message = "Great job! Keep going!"
                self.feedback_color = GREEN
        else:
            self.feedback_message = "Please position yourself correctly"
            self.feedback_color = YELLOW

        # Draw status box
        cv2.rectangle(image, (0, 0), (w, 80), BLUE, -1)

        # Exercise name and timer
        cv2.putText(image, f"{exercise['name']}", (10, 30),
                    FONT, 0.8, WHITE, 2, cv2.LINE_AA)
        cv2.putText(image, f"Time: {int(remaining_time)}s", (w - 150, 30),
                    FONT, 0.8, WHITE, 2, cv2.LINE_AA)

        # Rep counter
        cv2.rectangle(image, (0, h - 80), (150, h), ORANGE, -1)
        cv2.putText(image, "REPS", (10, h - 50),
                    FONT, 0.6, BLACK, 1, cv2.LINE_AA)
        cv2.putText(image, str(exercise["reps"]), (10, h - 15),
                    FONT, 1.2, WHITE, 2, cv2.LINE_AA)

        # Stage indicator
        cv2.rectangle(image, (160, h - 80), (300, h), ORANGE, -1)
        cv2.putText(image, "STAGE", (170, h - 50),
                    FONT, 0.6, BLACK, 1, cv2.LINE_AA)
        cv2.putText(image, exercise["stage"] if exercise["stage"] else "",
                    (170, h - 15), FONT, 1.2, WHITE, 2, cv2.LINE_AA)

        # Feedback message
        cv2.rectangle(image, (0, h - 140), (w, h - 90), (0, 0, 0), -1)
        cv2.putText(image, self.feedback_message, (10, h - 110),
                    FONT, 0.8, self.feedback_color, 2, cv2.LINE_AA)

        # Check if exercise time is up
        if remaining_time <= 0:
            self.mode = "rest"
            self.start_time = time.time()

            # Save exercise data
            self.performance_data.append({
                "exercise": exercise["name"],
                "reps": exercise["reps"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    def draw_rest_ui(self, image):
        """Draw the rest period interface"""
        h, w, _ = image.shape

        # Calculate remaining rest time
        elapsed_time = time.time() - self.start_time
        remaining_time = max(0, REST_TIME - elapsed_time)

        # Draw semi-transparent overlay
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)

        # Rest message
        cv2.putText(image, "REST TIME", (int(w/2) - 150, int(h/2) - 50),
                    FONT, 1.5, WHITE, 2, cv2.LINE_AA)
        cv2.putText(image, f"{int(remaining_time)} seconds", (int(w/2) - 120, int(h/2) + 20),
                    FONT, 1.2, WHITE, 2, cv2.LINE_AA)

        # Next exercise info
        next_exercise = (self.current_exercise + 1) % len(self.exercise_list)
        cv2.putText(image, f"Next: {self.exercise_list[next_exercise]['name']}",
                    (int(w/2) - 200, int(h/2) + 100), FONT, 1, WHITE, 2, cv2.LINE_AA)

        # Check if rest time is up
        if remaining_time <= 0:
            self.current_exercise = (self.current_exercise + 1) % len(self.exercise_list)

            # If we've gone through all exercises, show report
            if self.current_exercise == 0:
                self.mode = "report"
            else:
                self.mode = "exercise"
                self.start_time = time.time()

    def draw_report_ui(self, image):
        """Draw the performance report interface"""
        h, w, _ = image.shape

        # Draw semi-transparent overlay
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)

        # Title
        cv2.putText(image, "Rehabilitation Session Report", (int(w/2) - 250, 80),
                    FONT, 1.2, WHITE, 2, cv2.LINE_AA)

        # Performance data
        cv2.putText(image, "Exercise Performance:", (int(w/2) - 200, 150),
                    FONT, 1, WHITE, 2, cv2.LINE_AA)

        total_reps = 0
        for i, data in enumerate(self.performance_data):
            cv2.putText(image, f"{data['exercise']}: {data['reps']} repetitions",
                        (int(w/2) - 180, 200 + i*50), FONT, 0.8, WHITE, 2, cv2.LINE_AA)
            total_reps += data['reps']

        # Summary
        cv2.putText(image, f"Total Repetitions: {total_reps}", (int(w/2) - 180, h - 200),
                    FONT, 1, GREEN, 2, cv2.LINE_AA)

        # Save data message
        cv2.putText(image, "Performance data saved to 'rehab_report.csv'",
                    (int(w/2) - 250, h - 150), FONT, 0.8, WHITE, 2, cv2.LINE_AA)

        # Instructions
        cv2.putText(image, "Press 'R' to Return to Menu", (int(w/2) - 200, h - 100),
                    FONT, 0.8, BLUE, 2, cv2.LINE_AA)
        cv2.putText(image, "Press 'Q' to Quit", (int(w/2) - 200, h - 50),
                    FONT, 0.8, RED, 2, cv2.LINE_AA)

        # Save report to CSV
        self.save_report()

    def draw_custom_pose_ui(self, image):
        """Draw the custom pose interface"""
        h, w, _ = image.shape

        # Draw semi-transparent overlay for instructions
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (300, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)

        # Title
        cv2.putText(image, "Custom Pose Mode", (10, 30),
                    FONT, 0.8, WHITE, 2, cv2.LINE_AA)

        # Instructions
        if self.recording_pose:
            # Show recording status
            cv2.putText(image, "Recording Pose...", (10, 70),
                        FONT, 0.7, RED, 2, cv2.LINE_AA)
            cv2.putText(image, f"Frames: {len(self.pose_frames)}/30", (10, 100),
                        FONT, 0.7, WHITE, 1, cv2.LINE_AA)
        else:
            # Show available options
            cv2.putText(image, "Press 'R' to record a new pose", (10, 70),
                        FONT, 0.7, WHITE, 1, cv2.LINE_AA)
            cv2.putText(image, "Press 'V' to process a video file", (10, 100),
                        FONT, 0.7, WHITE, 1, cv2.LINE_AA)

            # Show saved poses
            y_pos = 150
            cv2.putText(image, "Saved Poses:", (10, y_pos),
                        FONT, 0.7, YELLOW, 1, cv2.LINE_AA)
            y_pos += 30

            if self.custom_poses:
                for i, pose_name in enumerate(self.custom_poses.keys()):
                    cv2.putText(image, f"{i+1}. {pose_name}", (20, y_pos),
                                FONT, 0.6, WHITE, 1, cv2.LINE_AA)
                    y_pos += 25
            else:
                cv2.putText(image, "No custom poses saved", (20, y_pos),
                            FONT, 0.6, WHITE, 1, cv2.LINE_AA)

        # Draw return to menu instruction
        cv2.putText(image, "Press 'M' to return to menu", (10, h - 20),
                    FONT, 0.7, WHITE, 1, cv2.LINE_AA)

    def draw_video_processing_ui(self, image):
        """Draw the video processing interface"""
        h, w, _ = image.shape

        # Draw semi-transparent overlay
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (w, 80), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)

        # Title and progress
        progress = int((self.video_current_frame / self.video_frame_count) * 100)
        cv2.putText(image, f"Video Processing: {progress}%", (10, 30),
                    FONT, 0.8, WHITE, 2, cv2.LINE_AA)
        cv2.putText(image, f"Frame: {self.video_current_frame}/{self.video_frame_count}",
                   (10, 60), FONT, 0.7, WHITE, 1, cv2.LINE_AA)

        # Draw valid poses found
        valid_count = sum(1 for f in self.pose_frames if f.get("valid", False))
        cv2.putText(image, f"Valid poses detected: {valid_count}",
                   (w - 300, 30), FONT, 0.7, GREEN if valid_count > 0 else RED, 1, cv2.LINE_AA)

        # Draw progress bar
        bar_width = w - 40
        bar_height = 20
        bar_x = 20
        bar_y = h - 40
        filled_width = int(bar_width * (self.video_current_frame / self.video_frame_count))

        # Draw background bar
        cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
        # Draw filled portion
        cv2.rectangle(image, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), GREEN, -1)

    def save_report(self):
        """Save the performance data to a CSV file"""
        with open('rehab_report.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Exercise", "Repetitions", "Timestamp"])

            for data in self.performance_data:
                writer.writerow([data["exercise"], data["reps"], data["timestamp"]])

    def save_custom_pose(self, pose_name):
        """Save a custom pose to disk"""
        # Ensure directory exists
        os.makedirs(CUSTOM_POSES_DIR, exist_ok=True)

        # Filter valid frames
        valid_frames = [f for f in self.pose_frames if f.get("valid", False)]

        if not valid_frames:
            print("No valid poses detected in the recording")
            return False

        # Calculate average pose from valid frames
        avg_keypoints = np.zeros((17, 2))
        avg_scores = np.zeros(17)
        frame_count = len(valid_frames)

        for frame in valid_frames:
            avg_keypoints += frame["keypoints"]
            avg_scores += frame["scores"]

        avg_keypoints /= frame_count
        avg_scores /= frame_count

        # Calculate joint angles for the pose
        angles = self.calculate_pose_angles(avg_keypoints)

        # Create pose data
        pose_data = {
            "name": pose_name,
            "keypoints": avg_keypoints.tolist(),
            "scores": avg_scores.tolist(),
            "angles": angles,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Save to disk
        file_path = os.path.join(CUSTOM_POSES_DIR, f"{pose_name}.json")
        with open(file_path, 'w') as f:
            json.dump(pose_data, f, indent=2)

        # Add to loaded poses
        self.custom_poses[pose_name] = pose_data

        print(f"Custom pose '{pose_name}' saved successfully")
        return True

    def load_custom_poses(self):
        """Load all custom poses from disk"""
        # Ensure directory exists
        os.makedirs(CUSTOM_POSES_DIR, exist_ok=True)

        poses = {}

        # List all JSON files in the directory
        try:
            files = [f for f in os.listdir(CUSTOM_POSES_DIR) if f.endswith('.json')]

            for file in files:
                file_path = os.path.join(CUSTOM_POSES_DIR, file)
                try:
                    with open(file_path, 'r') as f:
                        pose_data = json.load(f)
                        pose_name = pose_data.get("name", file.replace(".json", ""))
                        poses[pose_name] = pose_data
                        print(f"Loaded custom pose: {pose_name}")
                except Exception as e:
                    print(f"Error loading pose from {file}: {e}")
        except Exception as e:
            print(f"Error loading custom poses: {e}")

        return poses

    def calculate_pose_angles(self, keypoints):
        """Calculate joint angles for a pose"""
        angles = {}

        # Right arm angle (shoulder-elbow-wrist)
        right_shoulder = keypoints[RIGHT_SHOULDER]
        right_elbow = keypoints[RIGHT_ELBOW]
        right_wrist = keypoints[RIGHT_WRIST]
        angles["right_arm"] = self.calculate_angle(right_shoulder, right_elbow, right_wrist)

        # Left arm angle (shoulder-elbow-wrist)
        left_shoulder = keypoints[LEFT_SHOULDER]
        left_elbow = keypoints[LEFT_ELBOW]
        left_wrist = keypoints[LEFT_WRIST]
        angles["left_arm"] = self.calculate_angle(left_shoulder, left_elbow, left_wrist)

        # Right leg angle (hip-knee-ankle)
        right_hip = keypoints[RIGHT_HIP]
        right_knee = keypoints[RIGHT_KNEE]
        right_ankle = keypoints[RIGHT_ANKLE]
        angles["right_leg"] = self.calculate_angle(right_hip, right_knee, right_ankle)

        # Left leg angle (hip-knee-ankle)
        left_hip = keypoints[LEFT_HIP]
        left_knee = keypoints[LEFT_KNEE]
        left_ankle = keypoints[LEFT_ANKLE]
        angles["left_leg"] = self.calculate_angle(left_hip, left_knee, left_ankle)

        # Torso angle (shoulder-hip-knee)
        mid_shoulder = (keypoints[RIGHT_SHOULDER] + keypoints[LEFT_SHOULDER]) / 2
        mid_hip = (keypoints[RIGHT_HIP] + keypoints[LEFT_HIP]) / 2
        mid_knee = (keypoints[RIGHT_KNEE] + keypoints[LEFT_KNEE]) / 2
        angles["torso"] = self.calculate_angle(mid_shoulder, mid_hip, mid_knee)

        return angles

    def compare_pose(self, keypoints, scores):
        """Compare current pose with saved custom poses"""
        if not self.custom_poses:
            return None, 0.0

        # Calculate angles for current pose
        current_angles = self.calculate_pose_angles(keypoints)

        best_match = None
        best_similarity = 0.0

        # Compare with each saved pose
        for pose_name, pose_data in self.custom_poses.items():
            # Get saved angles
            saved_angles = pose_data.get("angles", {})

            # Calculate similarity score based on angle differences
            similarity = self.calculate_pose_similarity(current_angles, saved_angles)

            # Update best match if this is better
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = pose_name

        return best_match, best_similarity

    def calculate_pose_similarity(self, angles1, angles2):
        """Calculate similarity between two sets of pose angles"""
        if not angles1 or not angles2:
            return 0.0

        # Common angle keys
        common_keys = set(angles1.keys()).intersection(set(angles2.keys()))
        if not common_keys:
            return 0.0

        # Calculate normalized similarity (0.0 to 1.0)
        total_similarity = 0.0

        for key in common_keys:
            # Calculate angle difference (0 to 180 degrees)
            angle_diff = abs(angles1[key] - angles2[key])
            # Normalize to 0.0-1.0 range (0 = identical, 1 = completely different)
            normalized_diff = min(angle_diff / 180.0, 1.0)
            # Convert to similarity (1.0 = identical, 0.0 = completely different)
            similarity = 1.0 - normalized_diff
            total_similarity += similarity

        # Average similarity across all angles
        return total_similarity / len(common_keys)

    def validate_pose(self):
        """Validate if the current pose is valid for recording"""
        # Check if we have enough confident keypoints
        key_points = [RIGHT_SHOULDER, LEFT_SHOULDER, RIGHT_ELBOW, LEFT_ELBOW,
                     RIGHT_HIP, LEFT_HIP, RIGHT_KNEE, LEFT_KNEE]

        valid_count = sum(1 for kp in key_points if self.keypoint_scores[kp] > self.min_keypoint_score)

        # Require at least 6 key points to be detected with confidence
        return valid_count >= 6

    def process_video_file(self, video_path):
        """Process a video file to extract poses"""
        if not os.path.exists(video_path):
            print(f"Video file not found: {video_path}")
            return False

        # Open video file
        self.video_cap = cv2.VideoCapture(video_path)
        if not self.video_cap.isOpened():
            print(f"Failed to open video file: {video_path}")
            return False

        # Get video properties
        self.video_frame_count = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_current_frame = 0
        self.video_path = video_path
        self.pose_frames = []

        # Switch to video processing mode
        self.mode = "video_processing"

        print(f"Processing video: {video_path} ({self.video_frame_count} frames)")
        return True

        # Get video properties
        self.video_frame_count = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_current_frame = 0
        self.video_path = video_path
        self.pose_frames = []

        # Switch to video processing mode
        self.mode = "video_processing"

        print(f"Processing video: {video_path} ({self.video_frame_count} frames)")
        return True

    def process_video_frame(self):
        """Process a single frame from the video file"""
        if self.video_cap is None or self.video_current_frame >= self.video_frame_count:
            return None

        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, self.video_current_frame)
        ret, frame = self.video_cap.read()
        self.video_current_frame += 1

        if not ret:
            return None

        # Resize frame
        frame = cv2.resize(frame, (1280, 720))

        # Detect pose (prefer YOLO if available)
        detected_keypoints = None
        detected_scores = None
        if hasattr(self, "use_yolo") and self.use_yolo:
            yolo_out = self.detect_pose_yolo(frame)
            if yolo_out is not None:
                kp_norm, scores = yolo_out
                detected_keypoints = kp_norm
                detected_scores = np.array(scores)
        if detected_keypoints is None:
            img = frame.copy()
            img = tf.image.resize_with_pad(np.expand_dims(img, axis=0), 256, 256)
            img = tf.cast(img, dtype=tf.int32)

            # Detection
            results = self.movenet(img)
            keypoints = results['output_0'].numpy()[0][0]

            # Extract keypoints and scores
            detected_keypoints = keypoints[:, :2]
            detected_scores = keypoints[:, 2]

        # Check if pose is valid
        key_points = [RIGHT_SHOULDER, LEFT_SHOULDER, RIGHT_ELBOW, LEFT_ELBOW,
                     RIGHT_HIP, LEFT_HIP, RIGHT_KNEE, LEFT_KNEE]
        valid_count = sum(1 for kp in key_points if detected_scores[kp] > self.min_keypoint_score)
        is_valid = valid_count >= 6

        # Store frame data
        self.pose_frames.append({
            "frame_idx": self.video_current_frame - 1,
            "keypoints": detected_keypoints,
            "scores": detected_scores,
            "valid": is_valid
        })

        # Draw pose on frame
        for i, (y, x) in enumerate(detected_keypoints):
            confidence = detected_scores[i]
            if confidence > 0.3:
                kp_x = int(x * frame.shape[1])
                kp_y = int(y * frame.shape[0])

                color = GREEN if confidence > self.min_keypoint_score else YELLOW
                radius = 6 if confidence > self.min_keypoint_score else 4

                cv2.circle(frame, (kp_x, kp_y), radius, color, -1)

        return frame

    def run(self):
        """Main application loop"""
        self.cap = cv2.VideoCapture(0)

        while True:
            # Handle different modes
            if self.mode == "exercise" or self.mode == "custom_pose":
                ret, frame = self.cap.read()
                if not ret:
                    break

                # Resize frame for better display
                frame = cv2.resize(frame, (1280, 720))

                # Detect pose
                processed_frame = self.detect_pose(frame)

                if self.mode == "exercise":
                    # Draw exercise UI with feedback
                    self.draw_exercise_ui(processed_frame)
                    image = processed_frame
                else:  # custom_pose mode
                    # Record pose frames if recording
                    if self.recording_pose:
                        if len(self.pose_frames) < 30:  # Record 30 frames
                            # Store frame data
                            is_valid = self.validate_pose()
                            self.pose_frames.append({
                                "keypoints": np.copy(self.keypoints),
                                "scores": np.copy(self.keypoint_scores),
                                "valid": is_valid
                            })
                        else:
                            # Finished recording
                            self.recording_pose = False
                            # Prompt for pose name
                            pose_name = f"Custom_Pose_{len(self.custom_poses) + 1}"
                            self.save_custom_pose(pose_name)

                    # Compare with existing poses
                    if not self.recording_pose and self.custom_poses:
                        pose_name, similarity = self.compare_pose(self.keypoints, self.keypoint_scores)
                        if similarity > POSE_SIMILARITY_THRESHOLD:
                            # Draw pose match
                            cv2.putText(processed_frame, f"Detected: {pose_name}", (50, 50),
                                       FONT, 1.2, GREEN, 2, cv2.LINE_AA)
                            cv2.putText(processed_frame, f"Match: {int(similarity * 100)}%", (50, 100),
                                       FONT, 1, GREEN, 2, cv2.LINE_AA)

                    # Draw custom pose UI
                    self.draw_custom_pose_ui(processed_frame)
                    image = processed_frame

            elif self.mode == "menu":
                ret, frame = self.cap.read()
                if not ret:
                    break
                frame = cv2.resize(frame, (1280, 720))
                self.draw_menu(frame)
                image = frame

            elif self.mode == "rest":
                ret, frame = self.cap.read()
                if not ret:
                    break
                frame = cv2.resize(frame, (1280, 720))
                self.draw_rest_ui(frame)
                image = frame

            elif self.mode == "report":
                ret, frame = self.cap.read()
                if not ret:
                    break
                frame = cv2.resize(frame, (1280, 720))
                self.draw_report_ui(frame)
                image = frame

            elif self.mode == "video_processing":
                # Process video file
                frame = self.process_video_frame()

                if frame is None:
                    # Video processing complete
                    if self.video_cap:
                        self.video_cap.release()
                        self.video_cap = None

                    # Extract poses from video
                    if len(self.pose_frames) > 0:
                        # Find frames with valid poses
                        valid_frames = [f for f in self.pose_frames if f["valid"]]
                        if valid_frames:
                            # Save as custom pose
                            pose_name = f"Video_Pose_{len(self.custom_poses) + 1}"
                            self.save_custom_pose(pose_name)

                    # Return to custom pose mode
                    self.mode = "custom_pose"
                    continue

                # Draw video processing UI
                self.draw_video_processing_ui(frame)
                image = frame

            else:
                # Invalid mode
                break

            # Display the frame
            cv2.imshow('Elderly Rehabilitation System', image)

            # Handle key presses
            key = cv2.waitKey(10) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s') and self.mode == "menu":
                self.mode = "exercise"
                self.start_time = time.time()
                # Reset exercise data
                for exercise in self.exercise_list:
                    exercise["reps"] = 0
                    exercise["stage"] = None
                self.performance_data = []
            elif key == ord('r') and self.mode == "report":
                self.mode = "menu"
            elif key == ord('c') and self.mode == "menu":
                # Switch to custom pose mode
                self.mode = "custom_pose"
                self.pose_frames = []
                self.recording_pose = False
            elif key == ord('r') and self.mode == "custom_pose" and not self.recording_pose:
                # Start recording custom pose
                self.pose_frames = []
                self.recording_pose = True
            elif key == ord('v') and self.mode == "custom_pose" and not self.recording_pose:
                # Process video file (would need file dialog in real app)
                video_path = input("Enter path to video file: ")
                self.process_video_file(video_path)
            elif key == ord('m'):
                # Return to main menu from any mode
                self.mode = "menu"

        # Release resources
        if self.cap and self.cap.isOpened():
            self.cap.release()
        if self.video_cap and self.video_cap.isOpened():
            self.video_cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = ElderlyRehabSystem()
    app.run()