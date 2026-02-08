import os
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from typing import Dict, Any

# Cargar GOOGLE_API_KEY al importar este módulo (mismo proceso que atiende /invoke)
_GOOGLE_API_KEY: str = ""


def _load_google_api_key_at_import():
    global _GOOGLE_API_KEY
    if _GOOGLE_API_KEY:
        return
    key = os.getenv("GOOGLE_API_KEY")
    if key and key.strip():
        _GOOGLE_API_KEY = key.strip()
        return
    # Raíz del proyecto = carpeta que contiene app/
    root = Path(__file__).resolve().parent.parent.parent
    env_file = root / ".env"
    if not env_file.is_file():
        return
    try:
        with open(env_file, "r", encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                if k.strip() == "GOOGLE_API_KEY":
                    v = v.strip().strip('"\'')
                    if v:
                        _GOOGLE_API_KEY = v
                        return
    except Exception:
        pass


def _get_google_api_key() -> str:
    """Devuelve GOOGLE_API_KEY (cargada al importar el módulo o desde env)."""
    global _GOOGLE_API_KEY
    if _GOOGLE_API_KEY:
        return _GOOGLE_API_KEY
    _load_google_api_key_at_import()
    return _GOOGLE_API_KEY


def get_llm(llm_config: Dict[str, Any]):
    provider = llm_config.get("provider")
    model_name = llm_config.get("model")

    print(f"--- [LLM Factory] Creando instancia para proveedor: {provider}, modelo: {model_name} ---")

    if provider == "google":
        api_key = _get_google_api_key()
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY no está configurada. "
                "Crea una API key en https://aistudio.google.com/app/apikey y añádela al .env en la raíz del proyecto."
            )
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=1,
        )
    elif provider == "openai":
        return ChatOpenAI(model_name=model_name, temperature=1)
    else:
        raise ValueError(f"Proveedor de LLM desconocido: {provider}")


# Cargar la clave en cuanto se importe este módulo (mismo proceso que sirve /invoke)
_load_google_api_key_at_import()
if _GOOGLE_API_KEY:
    print("--- [LLM Factory] GOOGLE_API_KEY lista (cargada al importar). ---")
else:
    print("--- [LLM Factory] AVISO: GOOGLE_API_KEY vacía al importar. .env en:", Path(__file__).resolve().parent.parent.parent / ".env", "---")
