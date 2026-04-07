"""
Seed default exercises into database
Run this script to ensure default exercises exist
"""
from datetime import datetime
from db.connection import SessionLocal
from models import Exercise

DEFAULT_EXERCISES = [
    {
        'id': 'squat',
        'name': 'Squat (Gập gối)',
        'description': 'Bài tập tăng cường cơ chân và khớp gối',
        'target_reps': 16,
        'duration_seconds': 600,
        'base_exercise_type': 'squat',
        'down_threshold': 160.0,
        'up_threshold': 90.0,
        'hysteresis': 5.0,
        'difficulty_level': 'medium',
        'primary_muscle_group': 'legs',
        'video_path': '/squat.mp4',
        'is_default': True,
        'is_active': True
    },
    {
        'id': 'arm_raise',
        'name': 'Nâng Tay',
        'description': 'Bài tập tăng cường cơ vai và tay',
        'target_reps': 12,
        'duration_seconds': 300,
        'base_exercise_type': 'arm_raise',
        'down_threshold': 90.0,
        'up_threshold': 160.0,
        'hysteresis': 5.0,
        'difficulty_level': 'easy',
        'primary_muscle_group': 'shoulders',
        'video_path': '/arm_raise.mp4',
        'is_default': True,
        'is_active': True
    },
    {
        'id': 'calf_raise',
        'name': 'Nâng Gót Chân',
        'description': 'Bài tập tăng cường cơ bắp chân',
        'target_reps': 12,
        'duration_seconds': 300,
        'base_exercise_type': 'calf_raise',
        'down_threshold': 120.0,
        'up_threshold': 140.0,
        'hysteresis': 5.0,
        'difficulty_level': 'easy',
        'primary_muscle_group': 'calves',
        'video_path': '/calf_raise.mp4',
        'is_default': True,
        'is_active': True
    },
    {
        'id': 'single_leg_stand',
        'name': 'Đứng 1 Chân',
        'description': 'Bài tập cân bằng và tăng cường cơ chân',
        'target_reps': 10,
        'duration_seconds': 300,
        'base_exercise_type': 'single_leg_stand',
        'down_threshold': 160.0,
        'up_threshold': 50.0,
        'hysteresis': 5.0,
        'difficulty_level': 'medium',
        'primary_muscle_group': 'legs',
        'video_path': '/single_leg_stand.mp4',
        'is_default': True,
        'is_active': True
    }
]


def seed_exercises():
    """Seed default exercises if they don't exist"""
    db = SessionLocal()

    try:
        added = 0
        updated = 0

        for ex_data in DEFAULT_EXERCISES:
            existing = db.query(Exercise).filter(Exercise.id == ex_data['id']).first()

            if existing:
                # Update base_exercise_type if missing
                if not existing.base_exercise_type:
                    existing.base_exercise_type = ex_data['base_exercise_type']
                    existing.updated_at = datetime.utcnow()
                    updated += 1
                    print(f"Updated {ex_data['id']}: added base_exercise_type")
            else:
                # Create new
                exercise = Exercise(
                    id=ex_data['id'],
                    name=ex_data['name'],
                    description=ex_data['description'],
                    target_reps=ex_data['target_reps'],
                    duration_seconds=ex_data['duration_seconds'],
                    base_exercise_type=ex_data['base_exercise_type'],
                    down_threshold=ex_data['down_threshold'],
                    up_threshold=ex_data['up_threshold'],
                    hysteresis=ex_data['hysteresis'],
                    difficulty_level=ex_data['difficulty_level'],
                    primary_muscle_group=ex_data['primary_muscle_group'],
                    video_path=ex_data['video_path'],
                    is_default=ex_data['is_default'],
                    is_active=ex_data['is_active'],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(exercise)
                added += 1
                print(f"Added {ex_data['id']}: {ex_data['name']}")

        db.commit()
        print(f"\nDone! Added: {added}, Updated: {updated}")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == '__main__':
    seed_exercises()
