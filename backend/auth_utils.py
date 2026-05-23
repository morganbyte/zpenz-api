import bcrypt
import json
import os
import time
import urllib.request
from urllib.parse import urlparse

from dotenv import load_dotenv
from jose import JWTError, jwk, jwt
from backend.logging_config import get_logger

logger = get_logger(__name__)

load_dotenv()

_raw_supabase_url = (os.getenv("SUPABASE_URL") or "").strip().strip('"').rstrip("/")
if _raw_supabase_url.endswith("/auth/v1"):
    _raw_supabase_url = _raw_supabase_url[: -len("/auth/v1")]
parsed = urlparse(_raw_supabase_url)
if parsed.scheme and parsed.netloc:
    SUPABASE_URL = f"{parsed.scheme}://{parsed.netloc}"
else:
    SUPABASE_URL = _raw_supabase_url
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_JWT_AUD = os.getenv("SUPABASE_JWT_AUD", "authenticated")
SUPABASE_JWT_ISSUER = os.getenv("SUPABASE_JWT_ISSUER")

if SUPABASE_URL and not SUPABASE_JWT_ISSUER:
    SUPABASE_JWT_ISSUER = f"{SUPABASE_URL}/auth/v1"

_JWKS_CACHE = {
    "keys": None,
    "expires_at": 0.0,
}

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def _get_supabase_jwks():
    if not SUPABASE_URL:
        return None

    now = time.time()
    cached_keys = _JWKS_CACHE.get("keys")
    if cached_keys and _JWKS_CACHE.get("expires_at", 0) > now:
        return cached_keys

    try:
        url = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        headers = {}
        if SUPABASE_ANON_KEY:
            headers["apikey"] = SUPABASE_ANON_KEY
            headers["Authorization"] = f"Bearer {SUPABASE_ANON_KEY}"
        request = urllib.request.Request(url, headers=headers) if headers else url
        with urllib.request.urlopen(request) as response:
            data = json.load(response)
    except Exception as exc:
        logger.error(f"Supabase JWKS fetch failed: {exc}")
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
        logger.warning("Supabase JWKS unavailable")
        return None

    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        logger.error(f"Supabase token header decode failed: {exc}")
        return None

    kid = header.get("kid")
    alg = header.get("alg")
    if not kid or not alg:
        logger.warning("Supabase token missing kid/alg")
        return None

    if alg not in {"RS256", "ES256"}:
        logger.warning(f"Supabase token unsupported alg: {alg}")
        return None

    key_data = next((key for key in jwks if key.get("kid") == kid), None)
    if not key_data:
        logger.warning(f"Supabase JWKS kid not found: {kid}")
        return None

    key_alg = key_data.get("alg")
    if key_alg and key_alg != alg:
        logger.warning(f"Supabase JWKS alg mismatch: {key_alg} vs {alg}")
        return None

    try:
        public_key = jwk.construct(key_data)
        payload = jwt.decode(
            token,
            public_key.to_pem().decode("utf-8"),
            algorithms=[alg],
            audience=SUPABASE_JWT_AUD,
            issuer=SUPABASE_JWT_ISSUER,
        )
        return payload
    except JWTError as exc:
        logger.error(f"Supabase token verify failed: {exc}")
        return None
