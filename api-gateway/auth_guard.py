from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt, os
from bson import ObjectId

from .db import db   # ✅ SAME DB

security = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGORITHM = "HS256"

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
        user = db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise Exception()
        return user
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
