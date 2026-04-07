"""
AI Rehabilitation System V3 - Complete Backend
With Authentication, Database, Session Management, AI Personalization
"""

import asyncio
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from limiter import limiter
import os

if sys.platform == "win32":
    # Avoid noisy Proactor transport connection-reset tracebacks on Windows.
    policy_factory = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
    if policy_factory is not None:
        asyncio.set_event_loop_policy(policy_factory())

# Import routers
from routers import auth, sessions, doctor, websocket, profile, general, agent

# Import database initialization
from db.connection import init_db

# Initialize database
init_db()

# Seed default exercises (ensures they exist)
from seed_exercises import seed_exercises
seed_exercises()

app = FastAPI(title="Rehab System V3")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if not os.path.exists('uploads'):
    os.makedirs('uploads')

# Mount static files directory for music and assets
app.mount("/static", StaticFiles(directory="."), name="static")

# Mount uploads directory for exercise videos and thumbnails
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(general.router, prefix="/api", tags=["general"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(doctor.router, prefix="/api/doctor", tags=["doctor"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])
app.include_router(websocket.router, prefix="/ws/exercise", tags=["websocket"])

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Rehab System V3 - Full Features")
    print("=" * 60)
    print("Server: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("\nDefault Accounts:")
    print("   Doctor: doctor1 / doctor123")
    print("   Patient: patient1 / patient123")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
