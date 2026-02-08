"""
Carga las variables de entorno desde .env antes que el resto de la aplicación.
Se importa al inicio de main.py para que GOOGLE_API_KEY y demás estén disponibles.
"""
import os
from pathlib import Path

# Raíz del proyecto: carpeta que contiene app/, agents/, .env
_THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _THIS_DIR.parent
ENV_PATH = PROJECT_ROOT / ".env"


def _load_dotenv_safe():
    try:
        from dotenv import load_dotenv
        return load_dotenv
    except ImportError:
        return None


def _parse_env_file(path: Path) -> dict:
    """Lee un .env y devuelve un dict key=value (sin comentarios ni líneas vacías)."""
    out = {}
    if not path.is_file():
        return out
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key, value = key.strip(), value.strip()
                    if key:
                        if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
                            value = value[1:-1]
                        out[key] = value
    except Exception:
        pass
    return out


def load_env():
    """Carga .env desde la raíz del proyecto y desde el directorio actual."""
    load_dotenv = _load_dotenv_safe()
    if load_dotenv is None:
        parsed = _parse_env_file(ENV_PATH)
        for k, v in parsed.items():
            if k not in os.environ and v:
                os.environ[k] = v
        return

    load_dotenv(str(ENV_PATH))
    load_dotenv()

    if not os.getenv("GOOGLE_API_KEY"):
        for candidate in (ENV_PATH, Path.cwd() / ".env", Path.cwd().parent / ".env"):
            if candidate.is_file():
                parsed = _parse_env_file(candidate)
                if parsed.get("GOOGLE_API_KEY"):
                    os.environ["GOOGLE_API_KEY"] = parsed["GOOGLE_API_KEY"]
                    break


load_env()
