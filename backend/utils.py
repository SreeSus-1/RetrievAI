# backend/utils.py (CORRECTED)
import json
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

# --- PATHS ---
# DATA_DIR now points to the top-level folder *containing* the role subdirectories (raw)
DATA_DIR = ROOT / "Data" / "raw"
INDEX_DIR = ROOT / "data_index"
INDEX_DIR.mkdir(exist_ok=True)
USERS_PATH = ROOT / "users.json"

# map roles to the ACTUAL directory names you use (which are subfolders of DATA_DIR)
ROLE_TO_DIRS = {
    "public":  ["Public"],
    "internal":["Internal"],
    "private": ["Private"],
}

ALLOWED_ROLES = set(ROLE_TO_DIRS.keys())

def load_users():
    """Loads mock user data for authentication."""
    if not USERS_PATH.exists():
         # Create a placeholder users.json if it doesn't exist
        placeholder_data = {
            "public_user": {"password": "pwd", "categories": ["public"]},
            "internal_user": {"password": "pwd", "categories": ["public", "internal"]},
            "private_user": {"password": "pwd", "categories": ["public", "internal", "private"]}
        }
        with open(USERS_PATH, "w", encoding="utf-8") as f:
             json.dump(placeholder_data, f, indent=2)
             print(f"Created placeholder users.json at {USERS_PATH}")

    with open(USERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)