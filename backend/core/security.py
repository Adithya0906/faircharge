import os
import time
import hmac
import hashlib
import base64
import json
from typing import Optional, Dict
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.getenv("FAIRCHARGE_SECRET_KEY", "faircharge-enterprise-super-secret-key-2026")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
ADMIN_USERS = {
    "admin": {"name": "Campus Facilities Manager", "role": "admin"},
    "ops": {"name": "Operations Team Lead", "role": "operator"},
    "fleet": {"name": "EV Fleet Coordinator", "role": "fleet_manager"},
}

bearer_scheme = HTTPBearer(auto_error=False)


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(admin_id: str, expires_in_seconds: int = 86400) -> str:
    user_info = ADMIN_USERS.get(admin_id, {"name": admin_id, "role": "admin"})
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": admin_id,
        "name": user_info["name"],
        "role": user_info["role"],
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in_seconds,
    }
    
    header_b64 = base64url_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = base64url_encode(json.dumps(payload).encode('utf-8'))
    
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    sig_b64 = base64url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_access_token(token: str) -> Dict:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid token structure")
        
        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
        
        if not hmac.compare_digest(base64url_encode(expected_sig), sig_b64):
            raise ValueError("Signature verification failed")
        
        payload = json.loads(base64url_decode(payload_b64).decode('utf-8'))
        if payload.get("exp", 0) < int(time.time()):
            raise ValueError("Token expired")
        
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_admin_credentials(admin_id: str, password: str) -> Dict:
    expected_pass = os.getenv(f"ADMIN_PASSWORD_{admin_id.upper()}", ADMIN_PASSWORD)
    if admin_id not in ADMIN_USERS or not hmac.compare_digest(password, expected_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
        )
    return ADMIN_USERS[admin_id]


def get_current_admin(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> Optional[Dict]:
    if not credentials:
        return None
    return verify_access_token(credentials.credentials)
