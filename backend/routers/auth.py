# Authentication router
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
import secrets
import asyncio
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from models import User, UserRole, Gender, MobilityLevel, get_db, hash_password, verify_password
from settings import (
    SECRET_KEY, REFRESH_SECRET_KEY, ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, COOKIE_SECURE,
    SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_NAME,
)
from limiter import limiter

router = APIRouter()
security = HTTPBearer()

_REFRESH_COOKIE = "refresh_token"


# ─── Token helpers ────────────────────────────────────────────────────────────

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


class CreatePatientRequest(BaseModel):
    full_name: str
    username: str
    email: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    injury_type: Optional[str] = None
    medical_conditions: Optional[str] = None
    mobility_level: Optional[str] = 'beginner'
    pain_level: Optional[int] = 0
    doctor_notes: Optional[str] = None


def _create_access_token(user_id: int, username: str, role: str) -> str:
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'type': 'access',
        'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _create_refresh_token(user_id: int) -> str:
    payload = {
        'user_id': user_id,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, REFRESH_SECRET_KEY, algorithm=ALGORITHM)


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth",  # cookie only sent to auth endpoints
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_REFRESH_COOKIE, path="/api/auth")


def _user_dict(user: User) -> dict:
    return {
        'id': user.id,
        'username': user.username,
        'role': user.role.value,
        'full_name': user.full_name,
        'age': user.age,
        'gender': user.gender.value if user.gender else None,
        'doctor_id': user.doctor_id,
        'password_changed': bool(user.password_changed),
    }


# ─── Reusable dependencies ────────────────────────────────────────────────────

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate access token from Authorization: Bearer header."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get('type') != 'access':
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(token_data=Depends(verify_token)):
    return token_data


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    login_req: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == login_req.username).first()

    if not user or not verify_password(login_req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.role.value != login_req.role:
        label = 'bác sĩ' if user.role.value == 'doctor' else 'bệnh nhân'
        raise HTTPException(
            status_code=403,
            detail=f"Tài khoản này là tài khoản {label}. Vui lòng chọn đúng loại tài khoản.",
        )

    _set_refresh_cookie(response, _create_refresh_token(user.id))
    return {
        'access_token': _create_access_token(user.id, user.username, user.role.value),
        'user': _user_dict(user),
    }


@router.post("/register")
@limiter.limit("5/minute")
async def register(
    request: Request,
    response: Response,
    reg_req: RegisterRequest,
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.username == reg_req.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    try:
        new_user = User(
            username=reg_req.username,
            password_hash=hash_password(reg_req.password),
            role=UserRole.patient,
            full_name=reg_req.full_name,
            age=reg_req.age,
            gender=Gender(reg_req.gender) if reg_req.gender else None,
            height_cm=reg_req.height_cm,
            weight_kg=reg_req.weight_kg,
            medical_conditions=reg_req.medical_conditions,
            mobility_level=MobilityLevel(reg_req.mobility_level) if reg_req.mobility_level else None,
            pain_level=reg_req.pain_level,
            doctor_id=reg_req.doctor_id,
            created_at=datetime.utcnow(),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        _set_refresh_cookie(response, _create_refresh_token(new_user.id))
        return {
            'access_token': _create_access_token(new_user.id, new_user.username, new_user.role.value),
            'user': _user_dict(new_user),
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Issue a new access token using the HttpOnly refresh token cookie.
    Also rotates the refresh token (old cookie is replaced).
    """
    token = request.cookies.get(_REFRESH_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")

    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get('type') != 'refresh':
            raise HTTPException(status_code=401, detail="Invalid token type")
    except jwt.ExpiredSignatureError:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == payload['user_id']).first()
    if not user:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="User not found")

    # Rotate refresh token on every use
    _set_refresh_cookie(response, _create_refresh_token(user.id))
    return {
        'access_token': _create_access_token(user.id, user.username, user.role.value),
        'user': _user_dict(user),
    }


@router.post("/logout")
async def logout(response: Response):
    _clear_refresh_cookie(response)
    return {'ok': True}


def _send_credentials_email_sync(to_email: str, full_name: str, username: str, password: str) -> bool:
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Tài khoản Rehab AI của bạn"
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USERNAME}>"
    msg["To"] = to_email
    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#f9fafb;">
      <div style="background:white;border-radius:12px;padding:32px;box-shadow:0 2px 8px rgba(0,0,0,.1);">
        <h1 style="color:#0284c7;margin:0 0 4px;">Rehab AI</h1>
        <p style="color:#6b7280;margin:0 0 24px;">Hệ Thống Phục Hồi Chức Năng</p>
        <h2 style="color:#111827;">Xin chào {full_name},</h2>
        <p style="color:#374151;">Bác sĩ của bạn đã tạo tài khoản <strong>Rehab AI</strong> cho bạn. Thông tin đăng nhập:</p>
        <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:20px;margin:20px 0;">
          <p style="margin:0 0 12px;color:#374151;"><strong>Tên đăng nhập:</strong>
            <span style="font-family:monospace;background:#dbeafe;padding:2px 8px;border-radius:4px;color:#1d4ed8;">{username}</span>
          </p>
          <p style="margin:0;color:#374151;"><strong>Mật khẩu:</strong>
            <span style="font-family:monospace;background:#dbeafe;padding:2px 8px;border-radius:4px;color:#1d4ed8;">{password}</span>
          </p>
        </div>
        <p style="color:#6b7280;font-size:14px;">Vui lòng đổi mật khẩu sau khi đăng nhập lần đầu.</p>
        <p style="color:#9ca3af;font-size:12px;text-align:center;margin-top:24px;">Email này được gửi tự động từ hệ thống Rehab AI.</p>
      </div>
    </body></html>
    """
    msg.attach(MIMEText(html, "html"))
    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, to_email, msg.as_string())
    return True


async def _send_credentials_email(to_email: str, full_name: str, username: str, password: str) -> bool:
    try:
        return await asyncio.to_thread(_send_credentials_email_sync, to_email, full_name, username, password)
    except Exception:
        return False


@router.post("/create-patient")
@limiter.limit("10/minute")
async def create_patient(
    request: Request,
    patient_req: CreatePatientRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Doctor creates a patient account that is automatically assigned to them."""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Doctor access required")

    if db.query(User).filter(User.username == patient_req.username).first():
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")

    plain_password = secrets.token_urlsafe(10)

    bmi = None
    if patient_req.height_cm and patient_req.weight_kg and patient_req.height_cm > 0:
        bmi = round(patient_req.weight_kg / ((patient_req.height_cm / 100) ** 2), 1)

    try:
        new_patient = User(
            username=patient_req.username,
            password_hash=hash_password(plain_password),
            email=patient_req.email,
            role=UserRole.patient,
            password_changed=False,
            full_name=patient_req.full_name,
            age=patient_req.age,
            gender=Gender(patient_req.gender) if patient_req.gender else None,
            height_cm=patient_req.height_cm,
            weight_kg=patient_req.weight_kg,
            bmi=bmi,
            injury_type=patient_req.injury_type,
            medical_conditions=patient_req.medical_conditions,
            mobility_level=MobilityLevel(patient_req.mobility_level) if patient_req.mobility_level else None,
            pain_level=patient_req.pain_level,
            doctor_notes=patient_req.doctor_notes,
            doctor_id=current_user['user_id'],
            created_at=datetime.utcnow(),
        )
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)

        email_sent = False
        if patient_req.email:
            email_sent = await _send_credentials_email(
                patient_req.email, patient_req.full_name, patient_req.username, plain_password
            )

        return {
            'user': _user_dict(new_patient),
            'plain_password': plain_password,
            'email_sent': email_sent,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


class ChangePasswordRequest(BaseModel):
    new_password: str


@router.post("/change-password")
@limiter.limit("10/minute")
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Đổi mật khẩu lần đầu đăng nhập. Xoá cờ must_change_password."""
    import re
    pw = body.new_password
    if len(pw) < 8:
        raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 8 ký tự")
    if not re.search(r'[A-Z]', pw):
        raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 1 chữ in hoa")
    if not re.search(r'[0-9]', pw):
        raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 1 chữ số")
    if not re.search(r'[^a-zA-Z0-9]', pw):
        raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 1 ký tự đặc biệt")

    user = db.query(User).filter(User.id == current_user['user_id']).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    user.password_hash = hash_password(body.new_password)
    user.password_changed = True
    db.commit()

    return {'ok': True, 'message': 'Đổi mật khẩu thành công'}
