"""
Quick migration script to add base_exercise_type column
"""
from db.connection import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        # Add base_exercise_type column if not exists
        try:
            conn.execute(text('ALTER TABLE exercises ADD COLUMN base_exercise_type VARCHAR(50)'))
            conn.commit()
            print('[SUCCESS] Added base_exercise_type column')
        except Exception as e:
            if 'Duplicate column name' in str(e):
                print('[INFO] Column base_exercise_type already exists')
            else:
                print(f'[ERROR] Error adding column: {e}')
                return

        # Update default exercises to have base_exercise_type = id
        try:
            result = conn.execute(text("""
                UPDATE exercises
                SET base_exercise_type = id
                WHERE is_default = 1 AND base_exercise_type IS NULL
            """))
            conn.commit()
            print(f'[SUCCESS] Updated {result.rowcount} default exercises with base_exercise_type')
        except Exception as e:
            print(f'[ERROR] Error updating: {e}')

if __name__ == '__main__':
    migrate()
