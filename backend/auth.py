import os, time, jwt
from typing import Optional, List
from .utils import load_users, ALLOWED_ROLES  # ALLOWED_ROLES = {"public","internal","private"}

JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALG = "HS256"

def _normalize_categories(cats: List[str]) -> List[str]:
    return [str(c).strip().lower() for c in cats or []]

def issue_token(username: str, categories: list, exp_seconds: int = 60 * 60 * 12) -> str:
    now = int(time.time())
    payload = {
        "sub": username,
        "categories": _normalize_categories(categories),
        "iat": now,
        "exp": now + exp_seconds,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def login(username: str, password: str) -> Optional[dict]:
    users = load_users()
    for u in users:
        if u.get("username") == username and u.get("password") == password:
            cats = _normalize_categories(u.get("categories", []))
            cats = [c for c in cats if c in ALLOWED_ROLES]
            if not cats:
                return None
            tok = issue_token(username, cats)
            return {"token": tok, "categories": cats}
    return None

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
