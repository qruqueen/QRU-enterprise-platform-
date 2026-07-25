"""Signed, expiring access tokens for a PAID QRU order.

A token is a JWT bound to the order's random access id (NOT the Stripe session id) and the
purchased book id, scoped to the "download" action, with an expiry that matches the order's
delivery window. The customer-facing URL therefore never exposes the Stripe session id or any
storage path. Server-side verification of payment + window + download cap still happens on every
hit (this token only proves the link is authentic and unexpired).
"""
import time
import jwt

from auth import get_jwt_secret

TTL_SECONDS = 72 * 3600  # matches the 72h delivery window
_ALG = "HS256"
_TYP = "ord"


def mint(access_id: str, book_id: str, ttl: int = TTL_SECONDS) -> str:
    now = int(time.time())
    payload = {"typ": _TYP, "aid": access_id, "bid": book_id, "act": "download",
               "iat": now, "exp": now + int(ttl)}
    return jwt.encode(payload, get_jwt_secret(), algorithm=_ALG)


class TokenExpired(Exception):
    pass


class TokenInvalid(Exception):
    pass


def verify(token: str) -> dict:
    """Return the payload iff the token is authentic, unexpired and scoped to a download.
    Raises TokenExpired / TokenInvalid otherwise. Never trusts the token for payment state —
    the caller must re-check the order in the database."""
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
    if payload.get("act") != "download":
        raise TokenInvalid("action scope mismatch")
    if not payload.get("aid") or not payload.get("bid"):
        raise TokenInvalid("incomplete token")
    return payload
