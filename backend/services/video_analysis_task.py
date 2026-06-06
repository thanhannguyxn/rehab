"""
Video Analysis Background Task
Handles asynchronous video processing and AI recognition
"""
import json
import os
from datetime import datetime


def _upload_to_cloudinary_if_configured(local_video: str, local_thumbnail: str | None):
    """Upload video (and thumbnail if exists) to Cloudinary. Returns (video_url, thumb_url)."""
    try:
        from services.cloudinary_service import upload_video, upload_image, is_configured
        if not is_configured():
            return None, None
        video_url = upload_video(local_video)
        thumb_url = upload_image(local_thumbnail) if local_thumbnail and os.path.exists(local_thumbnail) else None
        return video_url, thumb_url
    except Exception as exc:
        print(f"[cloudinary] upload failed: {exc}")
        return None, None


def analyze_video_task(pending_id: int, video_path: str, db_session_factory):
    """
    Background task to analyze uploaded video

    This runs after video upload completes

    Args:
        pending_id: ID of PendingExercise record
        video_path: Path to uploaded video file
        db_session_factory: SQLAlchemy session factory (sessionmaker)
    """
    from models import PendingExercise
    from services.video_processor import VideoProcessor
    from services.exercise_recognizer import ExerciseRecognizer

    # Create a new database session for this background task
    db = db_session_factory()

    try:
        # 1. Get pending exercise
        pending = db.query(PendingExercise).filter(PendingExercise.id == pending_id).first()
        if not pending:
            print(f"PendingExercise {pending_id} not found")
            return

        pending.status = 'PROCESSING'
        db.commit()

        # 2. Get video info
        video_processor = VideoProcessor()
        video_info = video_processor.get_video_info(video_path)
        pending.video_duration_seconds = video_info['duration_seconds']

        # 3. Generate thumbnail
        doctor_id = pending.doctor_id
        video_filename = os.path.basename(video_path)
        thumbnail_filename = video_filename.replace('.mp4', '.jpg').replace('.avi', '.jpg').replace('.mov', '.jpg')
        thumbnail_path = f"uploads/thumbnails/{doctor_id}/{thumbnail_filename}"

        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)

        if video_processor.generate_thumbnail(video_path, thumbnail_path):
            pending.thumbnail_path = thumbnail_path

        # 4. Analyze with AI
        recognizer = ExerciseRecognizer()
        analysis_result = recognizer.analyze_video(video_path)

        # 5. Save results
        if 'error' in analysis_result and analysis_result.get('confidence', 0) == 0:
            pending.status = 'ERROR'
            pending.error_message = analysis_result.get('error', 'Unknown error')
        else:
            pending.detected_exercise_type = analysis_result.get('detected_type', 'unknown')
            pending.detected_thresholds = json.dumps(analysis_result.get('thresholds', {}))
            pending.movement_signature = json.dumps({
                'description': analysis_result.get('description', ''),
                'instructions': analysis_result.get('instructions', []),
                'warnings': analysis_result.get('warnings', []),
                'tracking_logic': analysis_result.get('tracking_logic', {}),
                'primary_joints': analysis_result.get('primary_joints', []),
                'video_duration': analysis_result.get('video_duration', 0)
            })
            pending.confidence_score = analysis_result.get('confidence', 0)
            pending.status = 'PENDING'  # Ready for doctor review

        pending.updated_at = datetime.utcnow()
        db.commit()

        # Upload to Cloudinary and replace local paths
        cloud_video, cloud_thumb = _upload_to_cloudinary_if_configured(
            video_path, pending.thumbnail_path
        )
        if cloud_video:
            pending.video_path = cloud_video
            if cloud_thumb:
                pending.thumbnail_path = cloud_thumb
            pending.updated_at = datetime.utcnow()
            db.commit()
            # Clean up local files after successful cloud upload
            try:
                os.remove(video_path)
                if pending.thumbnail_path and os.path.exists(str(pending.thumbnail_path)):
                    pass  # thumbnail_path now points to cloudinary URL
            except OSError:
                pass

        print(f"Video analysis completed for pending_id={pending_id}, type={pending.detected_exercise_type}")

    except Exception as e:
        # Handle errors
        print(f"Error analyzing video {pending_id}: {e}")
        try:
            pending = db.query(PendingExercise).filter(PendingExercise.id == pending_id).first()
            if pending:
                pending.status = 'ERROR'
                pending.error_message = str(e)
                pending.updated_at = datetime.utcnow()
                db.commit()
        except Exception as inner_e:
            print(f"Error updating pending status: {inner_e}")

    finally:
        db.close()
