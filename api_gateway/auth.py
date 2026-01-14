from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt, os, hashlib

from .db import db   # ✅ SHARED DB

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGORITHM = "HS256"

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

def hash_password(password: str) -> str:
    sha = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(sha)

def verify_password(password: str, hashed: str) -> bool:
    sha = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.verify(sha, hashed)

def create_token(user_id: str):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=7),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

@router.post("/signup")
def signup(data: SignupRequest):
    if db.users.find_one({"email": data.email}):
        raise HTTPException(400, "User already exists")

    res = db.users.insert_one({
        "email": data.email,
        "password_hash": hash_password(data.password),
        "created_at": datetime.utcnow(),
    })

    return {
        "status": "success",
        "token": create_token(str(res.inserted_id)),
    }

@router.post("/login")
def login(data: LoginRequest):
    user = db.users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")

    return {
        "status": "success",
        "token": create_token(str(user["_id"])),
    }
