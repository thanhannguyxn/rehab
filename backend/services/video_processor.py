"""
Video Processor Service
Handles video frame extraction and thumbnail generation
"""
import cv2
import os
from typing import List
import numpy as np


class VideoProcessor:
    """Service to process uploaded videos"""

    @staticmethod
    def extract_frames(video_path: str, fps: int = 5) -> List[np.ndarray]:
        """
        Extract frames from video at specified FPS

        Args:
            video_path: Path to video file
            fps: Frames per second to extract (default 5 for efficiency)

        Returns:
            List of frames as numpy arrays (BGR format)
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []

        original_fps = cap.get(cv2.CAP_PROP_FPS)
        if original_fps <= 0:
            original_fps = 30  # Default fallback

        frame_interval = max(1, int(original_fps / fps))

        frames = []
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                frames.append(frame)

            frame_count += 1

        cap.release()
        return frames

    @staticmethod
    def get_video_info(video_path: str) -> dict:
        """Get video metadata"""
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return {
                'fps': 0,
                'frame_count': 0,
                'width': 0,
                'height': 0,
                'duration_seconds': 0
            }

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        info = {
            'fps': fps if fps > 0 else 30,
            'frame_count': frame_count,
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'duration_seconds': int(frame_count / fps) if fps > 0 else 0
        }

        cap.release()
        return info

    @staticmethod
    def generate_thumbnail(video_path: str, output_path: str, timestamp_percent: float = 0.5) -> bool:
        """
        Generate thumbnail from video at specified position

        Args:
            video_path: Path to video file
            output_path: Path to save thumbnail
            timestamp_percent: Position in video (0-1)

        Returns:
            True if successful, False otherwise
        """
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return False

        # Jump to middle of video
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        target_frame = int(total_frames * timestamp_percent)
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

        ret, frame = cap.read()
        if ret:
            # Resize to thumbnail
            height = 180
            aspect_ratio = frame.shape[1] / frame.shape[0]
            width = int(height * aspect_ratio)
            thumbnail = cv2.resize(frame, (width, height))

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            cv2.imwrite(output_path, thumbnail)
            cap.release()
            return True

        cap.release()
        return False
