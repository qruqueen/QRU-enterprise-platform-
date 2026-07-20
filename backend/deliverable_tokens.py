"""Signed, short-lived access tokens for PROTECTED deliverable files.

Each token is a JWT bound to the EXACT file, the authenticated user, the intended action
(preview | download) and an expiry (~10 min). A preview token cannot download; a download token
cannot access an unrelated file. Brand/marketing images are NOT protected and never require a token.
"""
import time
import jwt

from auth import get_jwt_secret

TTL_SECONDS = 600  # ~10 minutes
_ALG = "HS256"
_TYP = "dlv"


def mint(fid: str, user_id: str, action: str, ttl: int = TTL_SECONDS) -> str:
    if action not in ("preview", "download"):
        raise ValueError("action must be preview or download")
    now = int(time.time())
    payload = {"typ": _TYP, "fid": fid, "uid": user_id, "act": action,
               "iat": now, "exp": now + int(ttl)}
    return jwt.encode(payload, get_jwt_secret(), algorithm=_ALG)


class TokenExpired(Exception):
    pass


class TokenInvalid(Exception):
    pass


def verify(token: str, fid: str, action: str) -> dict:
    """Return the payload iff the token is valid AND scoped to this exact file + action.
    Raises TokenExpired / TokenInvalid otherwise."""
    if not token:
        raise TokenInvalid("missing token")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[_ALG])
    except jwt.ExpiredSignatureError:
        raise TokenExpired("token expired")
    except jwt.InvalidTokenError:
        raise TokenInvalid("invalid token")
    if payload.get("typ") != _TYP:
        raise TokenInvalid("wrong token type")
    if payload.get("fid") != fid:
        raise TokenInvalid("file scope mismatch")
    if payload.get("act") != action:
        raise TokenInvalid("action scope mismatch")
    return payload
