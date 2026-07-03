import os
import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional

from database import db
from models import gen_id, now_iso, clean, ROLES

JWT_ALGORITHM = "HS256"

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "access",
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


async def get_current_user(request: Request) -> dict:
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"id": payload["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    user = clean(user)
    user.pop("password_hash", None)
    return user


def require_roles(*roles):
    async def dep(user: dict = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dep


def require_super_admin(user: dict = Depends(get_current_user)):
    if user.get("role") not in ("Founder & CEO", "Administrator"):
        raise HTTPException(status_code=403, detail="Super administrator access required")
    return user


class RegisterInput(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: Optional[str] = "Customer"


class LoginInput(BaseModel):
    email: EmailStr
    password: str


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "avatar": user.get("avatar"),
        "created_at": user.get("created_at"),
    }


@auth_router.post("/register")
async def register(data: RegisterInput):
    email = data.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    role = data.role if data.role in ROLES else "Customer"
    user = {
        "id": gen_id(),
        "email": email,
        "password_hash": hash_password(data.password),
        "name": data.name,
        "role": role,
        "avatar": None,
        "created_at": now_iso(),
    }
    await db.users.insert_one(user)
    token = create_access_token(user["id"], email)
    return {"access_token": token, "token_type": "bearer", "user": public_user(user)}


@auth_router.post("/login")
async def login(data: LoginInput):
    email = data.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["id"], email)
    return {"access_token": token, "token_type": "bearer", "user": public_user(user)}


@auth_router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return user


@auth_router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    return {"message": "Logged out"}


# ---------- Founder secure first-time setup (no seeded password) ----------
class FounderSetupInput(BaseModel):
    email: EmailStr
    password: str


def _validate_password(pw: str):
    if len(pw) < 10:
        raise HTTPException(status_code=400, detail="Password must be at least 10 characters.")
    if not any(c.isalpha() for c in pw) or not any(c.isdigit() for c in pw):
        raise HTTPException(status_code=400, detail="Password must include both letters and numbers.")


@auth_router.get("/setup-status")
async def setup_status():
    """Public — tells the login screen the Founder account state. The Founder always
    has a working (temporary) password; setup_required signals a permanent one is not yet set."""
    founder = await db.users.find_one({"is_founder": True})
    if not founder:
        return {"founder_exists": False, "setup_required": False}
    return {
        "founder_exists": True,
        "founder_email": founder["email"],
        "founder_name": founder.get("name"),
        "using_temporary_password": bool(founder.get("temp_password")),
        "setup_required": bool(founder.get("setup_required") or founder.get("temp_password")),
    }


@auth_router.post("/setup-founder")
async def setup_founder(data: FounderSetupInput):
    """One-time claim for a passwordless Founder account (legacy path). If the Founder
    already has a password, use /change-password instead."""
    founder = await db.users.find_one({"is_founder": True})
    if not founder:
        raise HTTPException(status_code=404, detail="No Founder account found.")
    if founder["email"].lower() != data.email.lower():
        raise HTTPException(status_code=400, detail="Email does not match the Founder account.")
    if founder.get("password_hash") and not founder.get("temp_password"):
        raise HTTPException(status_code=409, detail="Founder account is already configured. Use login instead.")
    _validate_password(data.password)
    await db.users.update_one(
        {"id": founder["id"]},
        {"$set": {"password_hash": hash_password(data.password), "setup_required": False,
                  "temp_password": False, "updated_at": now_iso()}})
    token = create_access_token(founder["id"], founder["email"])
    return {"access_token": token, "token_type": "bearer", "user": public_user(founder)}


class ChangePasswordInput(BaseModel):
    current_password: str
    new_password: str


@auth_router.post("/change-password")
async def change_password(data: ChangePasswordInput, user: dict = Depends(get_current_user)):
    """Authenticated permanent-password creation/change. Clears the temporary flag."""
    full = await db.users.find_one({"id": user["id"]})
    if not full or not full.get("password_hash") or not verify_password(data.current_password, full["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    _validate_password(data.new_password)
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"password_hash": hash_password(data.new_password), "temp_password": False,
                  "setup_required": False, "updated_at": now_iso()}})
    return {"message": "Password updated successfully."}
