from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import bcrypt as _bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
import psycopg2
import psycopg2.extras
import os

router = APIRouter(prefix="/lms/auth", tags=["LMS Auth"])
security = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET", "f8g_s3cr3t_k3y_2026_ch4ng3_m3!")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 72

DB_URL = os.getenv("FLEMING_DB_URL", "dbname=fleming_db user=fleming_user password=fl3m1ng_db_2026! host=localhost")


def get_conn():
    return psycopg2.connect(DB_URL)


def create_token(user_id: int, email: str, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"id": int(payload["sub"]), "email": payload["email"], "role": payload["role"]}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


class RegisterModel(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "student"


class LoginModel(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdate(BaseModel):
    name: str = None
    phone: str = None
    org: str = None
    state: str = None
    qualifications: str = None
    role: str = None


@router.post("/register")
async def register(req: RegisterModel):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id FROM lms_users WHERE email = %s", (req.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed = _bcrypt.hashpw(req.password.encode(), _bcrypt.gensalt()).decode()
        # Teachers start as 'student' until superadmin approves
        role = "student" if req.role == "teacher" else req.role
        if role not in ("student", "teacher", "superadmin"):
            role = "student"
        cur.execute(
            "INSERT INTO lms_users (email, password_hash, name, role) VALUES (%s, %s, %s, %s) RETURNING id, email, name, role",
            (req.email, hashed, req.name, role)
        )
        user = cur.fetchone()
        conn.commit()
        token = create_token(user["id"], user["email"], user["role"])
        return {"token": token, "user": user}
    finally:
        conn.close()


@router.post("/login")
async def login(req: LoginModel):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, email, name, role, password_hash FROM lms_users WHERE email = %s", (req.email,))
        user = cur.fetchone()
        if not user or not _bcrypt.checkpw(req.password.encode(), user["password_hash"].encode()):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token = create_token(user["id"], user["email"], user["role"])
        del user["password_hash"]
        return {"token": token, "user": user}
    finally:
        conn.close()


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, email, name, role, phone, org, state, qualifications, avatar_url, created_at FROM lms_users WHERE id = %s",
            (user["id"],)
        )
        profile = cur.fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")
        return profile
    finally:
        conn.close()


@router.put("/me")
async def update_me(req: ProfileUpdate, user=Depends(get_current_user)):
    conn = get_conn()
    try:
        cur = conn.cursor()
        fields = []
        values = []
        for k, v in req.dict(exclude_none=True).items():
            if k == "role":
                continue  # can't self-promote
            fields.append(f"{k} = %s")
            values.append(v)
        if not fields:
            return {"status": "no changes"}
        values.append(user["id"])
        cur.execute(f"UPDATE lms_users SET {', '.join(fields)} WHERE id = %s", values)
        conn.commit()
        return {"status": "updated"}
    finally:
        conn.close()
