import bcrypt
import json
import os
import time
import urllib.request
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from jose import JWTError, jwk, jwt

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_JWT_AUD = os.getenv("SUPABASE_JWT_AUD", "authenticated")
SUPABASE_JWT_ISSUER = os.getenv("SUPABASE_JWT_ISSUER")

if SUPABASE_URL and not SUPABASE_JWT_ISSUER:
    SUPABASE_JWT_ISSUER = f"{SUPABASE_URL}/auth/v1"

_JWKS_CACHE = {
    "keys": None,
    "expires_at": 0.0,
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str) -> str:
    """Hash de contraseña"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verificar token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def _get_supabase_jwks():
    if not SUPABASE_URL:
        return None

    now = time.time()
    cached_keys = _JWKS_CACHE.get("keys")
    if cached_keys and _JWKS_CACHE.get("expires_at", 0) > now:
        return cached_keys

    try:
        with urllib.request.urlopen(f"{SUPABASE_URL}/auth/v1/certs") as response:
            data = json.load(response)
    except Exception:
        return cached_keys

    keys = data.get("keys") if isinstance(data, dict) else None
    if not keys:
        return cached_keys

    _JWKS_CACHE["keys"] = keys
    _JWKS_CACHE["expires_at"] = now + 3600
    return keys


def verify_supabase_token(token: str):
    """Verificar JWT emitido por Supabase."""
    jwks = _get_supabase_jwks()
    if not jwks:
        return None

    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        return None

    kid = header.get("kid")
    key_data = next((key for key in jwks if key.get("kid") == kid), None)
    if not key_data:
        return None

    try:
        public_key = jwk.construct(key_data)
        payload = jwt.decode(
            token,
            public_key.to_pem().decode("utf-8"),
            algorithms=["RS256"],
            audience=SUPABASE_JWT_AUD,
            issuer=SUPABASE_JWT_ISSUER,
        )
        return payload
    except JWTError:
        return None
