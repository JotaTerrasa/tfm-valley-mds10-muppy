"""
Autenticación simple: login con usuario/contraseña y JWT.
- Usuario desde env (LOGIN_USER, LOGIN_PASSWORD) o desde archivo data/users.json.
- Para registrar usuarios: script `python -m app.auth add_user` o endpoint POST /auth/register (con clave admin).
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import bcrypt

from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "cambiar-en-produccion-clave-secreta-muppy")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 días

LOGIN_USER = os.getenv("LOGIN_USER", "").strip()
LOGIN_PASSWORD_PLAIN = os.getenv("LOGIN_PASSWORD", "").strip()

# Archivo de usuarios registrados (data/users.json). No se sube a git.
_USERS_FILE_ENV = os.getenv("USERS_FILE", "").strip()
USERS_FILE = _USERS_FILE_ENV if _USERS_FILE_ENV else os.path.join(os.getcwd(), "data", "users.json")

security = HTTPBearer(auto_error=False)

# bcrypt limita la contraseña a 72 bytes
def _truncate_password(password: str) -> bytes:
    return (password or "").encode("utf-8")[:72]


def _get_password_hash(password: str) -> str:
    return bcrypt.hashpw(_truncate_password(password), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_truncate_password(plain), hashed.encode("utf-8"))
    except Exception:
        return False


def _users_path() -> str:
    return USERS_FILE


def _load_users() -> Dict[str, str]:
    """Lee data/users.json. Devuelve dict { username: password_hash }."""
    path = _users_path()
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("users", {})
    except (json.JSONDecodeError, IOError):
        return {}


def _save_users(users: Dict[str, str]) -> None:
    path = Path(_users_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"users": users}, f, indent=2)


# Hash del password de env (se calcula al importar si hay LOGIN_PASSWORD)
_LOGIN_PASSWORD_HASH: Optional[str] = None
if LOGIN_PASSWORD_PLAIN:
    _LOGIN_PASSWORD_HASH = _get_password_hash(LOGIN_PASSWORD_PLAIN)
_LOGIN_PASSWORD_HASH_ENV = os.getenv("LOGIN_PASSWORD_HASH", "").strip()
if _LOGIN_PASSWORD_HASH_ENV:
    _LOGIN_PASSWORD_HASH = _LOGIN_PASSWORD_HASH_ENV


def is_login_required() -> bool:
    """True si hay al menos un usuario (env o archivo)."""
    if LOGIN_USER and (_LOGIN_PASSWORD_HASH or LOGIN_PASSWORD_PLAIN):
        return True
    return len(_load_users()) > 0


def verify_user(username: str, password: str) -> bool:
    username = (username or "").strip()
    password = (password or "").strip()
    # Usuario de env
    if LOGIN_USER and username == LOGIN_USER:
        if _LOGIN_PASSWORD_HASH:
            return _verify_password(password, _LOGIN_PASSWORD_HASH)
        return password == LOGIN_PASSWORD_PLAIN
    # Usuarios del archivo
    users = _load_users()
    if username not in users:
        return False
    return _verify_password(password, users[username])


def register_user(username: str, password: str) -> bool:
    """
    Registra un usuario (hash de contraseña) en data/users.json.
    Devuelve True si se creó. Lanza ValueError si el usuario ya existe.
    """
    username = username.strip()
    if not username:
        raise ValueError("El usuario no puede estar vacío")
    users = _load_users()
    if username in users:
        raise ValueError(f"El usuario '{username}' ya existe")
    if username == LOGIN_USER:
        raise ValueError("Ese usuario está reservado (env)")
    users[username] = _get_password_hash(password)
    _save_users(users)
    return True


def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """Si login está activo, exige token válido; si no, devuelve None (acceso permitido)."""
    if not is_login_required():
        return None
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Requiere autenticación",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = decode_token(credentials.credentials)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


# --- CLI para registrar usuarios desde consola ---
if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "add_user":
        user = sys.argv[2]
        pwd = sys.argv[3] if len(sys.argv) > 3 else None
        if not pwd:
            import getpass
            pwd = getpass.getpass("Contraseña: ")
        try:
            register_user(user, pwd)
            print(f"Usuario '{user}' registrado correctamente.")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Uso: python -m app.auth add_user <usuario> [contraseña]")
        print("  Si no pasas contraseña, se pedirá por consola.")
        sys.exit(0)
