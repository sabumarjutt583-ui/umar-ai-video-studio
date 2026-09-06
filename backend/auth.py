"""
Authentication, User Management, and Branding Module.

Features:
- Role-based access control: 'owner' (Hafiz Muhammad Umar) vs 'user' (Standard Registered Users).
- Secure password hashing (SHA-256 with salt).
- Persistent JSON user storage.
- Token-based session management.
- Owner-only tool logo management and persistence.
"""

import os
import json
import uuid
import time
import hashlib
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "auth_sessions.json")
BRANDING_DIR = os.path.join(DATA_DIR, "branding")
LOGO_FILE = os.path.join(BRANDING_DIR, "tool_logo.png")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BRANDING_DIR, exist_ok=True)

# In-memory active tokens cache: token -> {user_id, email, name, role, expires_at}
_ACTIVE_TOKENS = {}
TOKEN_EXPIRY_SECONDS = 30 * 24 * 3600  # 30 days


def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if not salt:
        salt = uuid.uuid4().hex[:16]
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return hashed, salt


def _load_users() -> list[dict]:
    if not os.path.exists(USERS_FILE):
        # Default pre-seeded Owner account: Hafiz Muhammad Umar
        default_owner_salt = uuid.uuid4().hex[:16]
        default_owner_hash = hashlib.sha256((default_owner_salt + "admin123").encode("utf-8")).hexdigest()
        initial_users = [
            {
                "id": "owner_1",
                "name": "Hafiz Muhammad Umar",
                "email": "umar@videobot.com",
                "password_hash": default_owner_hash,
                "salt": default_owner_salt,
                "role": "owner",
                "created_at": time.time(),
            }
        ]
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_users, f, indent=2, ensure_ascii=False)
        return initial_users

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_users(users: list[dict]):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def _load_sessions():
    global _ACTIVE_TOKENS
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                now = time.time()
                _ACTIVE_TOKENS = {k: v for k, v in data.items() if v.get("expires_at", 0) > now}
        except Exception:
            _ACTIVE_TOKENS = {}


def _save_sessions():
    try:
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(_ACTIVE_TOKENS, f, indent=2)
    except Exception:
        pass


# Initialize on import
_load_users()
_load_sessions()


def register_user(name: str, email: str, password: str) -> dict:
    """Naya user register karta hai with role 'user'."""
    name = (name or "").strip()
    email = (email or "").strip().lower()
    password = (password or "").strip()

    if not name:
        raise ValueError("Name lazmi hai.")
    if not email or "@" not in email:
        raise ValueError("Valid email address darj karein.")
    if len(password) < 4:
        raise ValueError("Password kam se kam 4 characters ka hona chahiye.")

    users = _load_users()
    for u in users:
        if u["email"].lower() == email:
            raise ValueError("Ye email already registered hai. Baraye meherbani login karein.")

    hashed, salt = _hash_password(password)
    user_id = str(uuid.uuid4())[:8]

    new_user = {
        "id": user_id,
        "name": name,
        "email": email,
        "password_hash": hashed,
        "salt": salt,
        "role": "user",  # Only registered user, not owner
        "created_at": time.time(),
    }
    users.append(new_user)
    _save_users(users)

    # Automatically generate login session token
    token = _create_token(new_user)
    return {
        "token": token,
        "user": {
            "id": new_user["id"],
            "name": new_user["name"],
            "email": new_user["email"],
            "role": new_user["role"],
        }
    }


def authenticate_user(email: str, password: str) -> dict:
    """Email aur password check karke token return karta hai."""
    email = (email or "").strip().lower()
    password = (password or "").strip()

    users = _load_users()
    target = None
    for u in users:
        if u["email"].lower() == email:
            target = u
            break

    if not target:
        raise ValueError("Email ya password durust nahi hai.")

    expected_hash, _ = _hash_password(password, target["salt"])
    if expected_hash != target["password_hash"]:
        raise ValueError("Email ya password durust nahi hai.")

    token = _create_token(target)
    return {
        "token": token,
        "user": {
            "id": target["id"],
            "name": target["name"],
            "email": target["email"],
            "role": target["role"],
        }
    }


def _create_token(user: dict) -> str:
    token = uuid.uuid4().hex + uuid.uuid4().hex
    _ACTIVE_TOKENS[token] = {
        "user_id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user.get("role", "user"),
        "expires_at": time.time() + TOKEN_EXPIRY_SECONDS,
    }
    _save_sessions()
    return token


def get_current_user(token: str) -> dict | None:
    """Token check karke user data deta hai."""
    if not token:
        return None
    session = _ACTIVE_TOKENS.get(token)
    if not session:
        return None
    if session.get("expires_at", 0) < time.time():
        _ACTIVE_TOKENS.pop(token, None)
        _save_sessions()
        return None

    return {
        "id": session["user_id"],
        "name": session["name"],
        "email": session["email"],
        "role": session.get("role", "user"),
    }


def logout_user(token: str) -> bool:
    if token in _ACTIVE_TOKENS:
        del _ACTIVE_TOKENS[token]
        _save_sessions()
        return True
    return False


def is_owner(token: str) -> bool:
    user = get_current_user(token)
    return bool(user and user.get("role") == "owner")


# ----------------------------------------------------------------------------
# Tool Logo / Branding Management (Owner Only)
# ----------------------------------------------------------------------------

BRANDING_SETTINGS_FILE = os.path.join(BRANDING_DIR, "settings.json")
DEFAULT_BRANDING = {
    "tool_name": "Umar AI Video Studio",
    "creator_name": "Hafiz Muhammad Umar",
    "creator_title": "Creator & Owner",
}


def get_branding_settings() -> dict:
    settings = dict(DEFAULT_BRANDING)
    if os.path.exists(BRANDING_SETTINGS_FILE):
        try:
            with open(BRANDING_SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    settings.update(data)
        except Exception:
            pass
    # Creator name and title are strictly locked to Hafiz Muhammad Umar
    settings["creator_name"] = "Hafiz Muhammad Umar"
    settings["creator_title"] = "Creator & Owner"
    return settings


def save_branding_settings(new_settings: dict) -> dict:
    current = get_branding_settings()
    if "tool_name" in new_settings and str(new_settings["tool_name"]).strip():
        current["tool_name"] = str(new_settings["tool_name"]).strip()
    # Creator always stays locked
    current["creator_name"] = "Hafiz Muhammad Umar"
    current["creator_title"] = "Creator & Owner"

    try:
        with open(BRANDING_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    return current


def save_tool_logo(file_bytes: bytes, filename: str) -> str:
    """Tool logo file save karta hai. Extension maintain karta hai."""
    ext = os.path.splitext(filename)[1].lower() or ".png"
    target = os.path.join(BRANDING_DIR, f"tool_logo{ext}")
    # Remove previous logo files if any with other extensions
    for item in os.listdir(BRANDING_DIR):
        if item.startswith("tool_logo"):
            try:
                os.remove(os.path.join(BRANDING_DIR, item))
            except OSError:
                pass

    with open(target, "wb") as f:
        f.write(file_bytes)
    return target


def get_tool_logo_path() -> str | None:
    """Agar custom logo uploaded hai to uska path deta hai."""
    if not os.path.isdir(BRANDING_DIR):
        return None
    for item in os.listdir(BRANDING_DIR):
        if item.startswith("tool_logo") and os.path.isfile(os.path.join(BRANDING_DIR, item)):
            return os.path.join(BRANDING_DIR, item)
    return None

