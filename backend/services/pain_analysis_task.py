"""
Post-session pain analysis background task.

Called after the patient ends a session. Receives the JPEG frames that were
sampled every 5 seconds during the WebSocket session and runs FaceMesh-based
pain/fatigue scoring on each one.

Results are written back to the Session row (avg_pain_level, avg_fatigue_level,
predominant_emotion, pain_incidents, fatigue_incidents) — all fields already
present in the DB schema, no migration required.
"""

import asyncio
from collections import Counter
from statistics import mean
from typing import List

import cv2
import numpy as np


async def analyze_session_pain(
    session_id: int,
    frames: List[bytes],
    db_session_factory,
) -> None:
    """
    Async background task — safe to schedule with FastAPI BackgroundTasks.

    Heavy FaceMesh processing is offloaded with asyncio.to_thread so the
    event loop is never blocked.

    Args:
        session_id:          DB id of the finished Session.
        frames:              List of raw JPEG bytes sampled during the session.
        db_session_factory:  SQLAlchemy SessionLocal factory.
    """
    from models import DBSession
    from services.face_service import FacePainAnalyzer

    print(f"[pain_analysis] Starting analysis for session {session_id} "
          f"({len(frames)} frames)")

    analyzer = FacePainAnalyzer()
    results = []

    for jpeg_bytes in frames:
        nparr = np.frombuffer(jpeg_bytes, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if bgr is None:
            continue

        # Run blocking FaceMesh call in a thread pool
        result = await asyncio.to_thread(analyzer.analyze_frame, bgr)
        if result is not None:
            results.append(result)

    if not results:
        print(f"[pain_analysis] Session {session_id}: no face detected in any frame. "
              "Pain fields left as NULL.")
        return

    avg_pain     = mean(r["pain_score"]    for r in results)
    avg_fatigue  = mean(r["fatigue_score"] for r in results)
    pain_inc     = sum(1 for r in results if r["pain_score"]    > 0.55)
    fatigue_inc  = sum(1 for r in results if r["fatigue_score"] > 0.50)
    predominant  = Counter(r["expression"] for r in results).most_common(1)[0][0]

    print(
        f"[pain_analysis] Session {session_id} result: "
        f"pain={avg_pain:.3f}, fatigue={avg_fatigue:.3f}, "
        f"expression={predominant}, pain_incidents={pain_inc}, "
        f"fatigue_incidents={fatigue_inc}"
    )

    # Write back to DB — open a fresh session (we're in a background thread context)
    db = db_session_factory()
    try:
        session = db.query(DBSession).filter(DBSession.id == session_id).first()
        if session:
            session.avg_pain_level    = round(avg_pain, 3)
            session.avg_fatigue_level = round(avg_fatigue, 3)
            session.predominant_emotion = predominant
            session.pain_incidents    = pain_inc
            session.fatigue_incidents = fatigue_inc
            db.commit()
            print(f"[pain_analysis] Session {session_id}: DB updated successfully.")
        else:
            print(f"[pain_analysis] Session {session_id}: record not found in DB.")
    except Exception as exc:
        db.rollback()
        print(f"[pain_analysis] Session {session_id}: DB write failed — {exc}")
    finally:
        db.close()
