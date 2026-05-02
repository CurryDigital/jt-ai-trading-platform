"""Lightweight single-user auth for the JTCML platform.

Uses HMAC-SHA256 token signing (same scheme as JWT HS256) with stdlib only —
no pyjwt/python-jose dependency required.

Environment variables:
  JTCML_USER     — login username  (default: admin)
  JTCML_PASSWORD — login password  (default: changeme)
  JTCML_SECRET   — HMAC key        (auto-generated per process if unset)

Token format: base64(header).base64(payload).base64(signature)
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Optional

from fastapi import Depends, HTTPException, Request

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
JTCML_USER = os.environ.get("JTCML_USER", "admin")
JTCML_PASSWORD = os.environ.get("JTCML_PASSWORD", "changeme")
JTCML_SECRET = os.environ.get("JTCML_SECRET", secrets.token_hex(32))
TOKEN_TTL = int(os.environ.get("JTCML_TOKEN_TTL", "86400"))  # 24h default

# Paths that don't require auth
PUBLIC_PATHS = frozenset({
    "/api/auth/login",
    "/api/auth/refresh",
    "/api/system/health",
    "/docs",
    "/openapi.json",
    "/ws/events",
})

# Prefixes that skip auth (frontend assets, Vite HMR, etc.)
PUBLIC_PREFIXES = ("/assets/", "/_vite/", "/favicon", "/index.html", "/")


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64d(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * pad)


def create_token(sub: str, ttl: int = TOKEN_TTL) -> str:
    header = _b64e(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64e(json.dumps({
        "sub": sub,
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl,
    }).encode())
    sig = _b64e(hmac.new(JTCML_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}"


def verify_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        expected_sig = _b64e(hmac.new(
            JTCML_SECRET.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256,
        ).digest())
        if not hmac.compare_digest(sig_b64, expected_sig):
            return None
        payload = json.loads(_b64d(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def get_current_user(request: Request) -> dict:
    """FastAPI dependency — extracts and verifies the bearer token."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    payload = verify_token(auth[7:])
    if not payload:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    return payload


# ---------------------------------------------------------------------------
# Auth-check middleware helper (called from main.py)
# ---------------------------------------------------------------------------
AUTH_ENABLED = os.environ.get("JTCML_AUTH", "0") == "1"


def is_public_path(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    if path.startswith("/api/"):
        return False
    if path.startswith("/ws/"):
        return True
    return True  # non-API paths = frontend assets, always public
