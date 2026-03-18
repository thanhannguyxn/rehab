from sqlalchemy import create_engine, text

from settings import DATABASE_URL

engine = create_engine(DATABASE_URL)
with engine.begin() as conn:
    conn.execute(text("UPDATE alembic_version SET version_num='307582ad0355'"))
print('stamped to 307582ad0355')
