# Authentication router
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
from typing import Optional

from models import User, UserRole, Gender, MobilityLevel, get_db, hash_password, verify_password
from settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_DAYS
from limiter import limiter

router = APIRouter()
security = HTTPBearer()

class LoginRequest(BaseModel):
    username: str
    password: str
    role: str  # 'patient' or 'doctor'

class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    role: str = 'patient'
    doctor_id: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    medical_conditions: Optional[str] = None
    mobility_level: Optional[str] = 'beginner'
    pain_level: Optional[int] = 0

def create_token(user_id: int, username: str, role: str) -> str:
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(token_data = Depends(verify_token)):
    return token_data

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, login_req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.username == login_req.username
    ).first()

    if not user or not verify_password(login_req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Validate role matches the expected role
    if user.role.value != login_req.role:
        raise HTTPException(
            status_code=403,
            detail=f"Tài khoản này là tài khoản {'bác sĩ' if user.role.value == 'doctor' else 'bệnh nhân'}. Vui lòng chọn đúng loại tài khoản."
        )

    token = create_token(user.id, user.username, user.role.value)

    return {
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role.value,
            'full_name': user.full_name,
            'age': user.age,
            'gender': user.gender.value if user.gender else None,
            'doctor_id': user.doctor_id
        }
    }

@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, reg_req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == reg_req.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        # Create new user
        new_user = User(
            username=reg_req.username,
            password_hash=hash_password(reg_req.password),
            role=UserRole.patient if reg_req.role == 'patient' else UserRole.doctor,
            full_name=reg_req.full_name,
            age=reg_req.age,
            gender=Gender(reg_req.gender) if reg_req.gender else None,
            height_cm=reg_req.height_cm,
            weight_kg=reg_req.weight_kg,
            medical_conditions=reg_req.medical_conditions,
            mobility_level=MobilityLevel(reg_req.mobility_level) if reg_req.mobility_level else None,
            pain_level=reg_req.pain_level,
            doctor_id=reg_req.doctor_id,
            created_at=datetime.utcnow()
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = create_token(new_user.id, new_user.username, new_user.role.value)

        return {
            'token': token,
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'role': new_user.role.value,
                'full_name': new_user.full_name
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))