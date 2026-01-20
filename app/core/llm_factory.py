import os
import redis
from langchain_google_vertexai import ChatVertexAI
from langchain_openai import ChatOpenAI
from typing import Dict, Any
from langchain_community.cache import RedisCache
from langchain.globals import set_llm_cache

REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL:
    try:
        print("--- [LLM Factory] Inicializando caché de respuestas de LLM con Redis... ---")
        redis_client = redis.from_url(REDIS_URL)
        redis_client.ping()
        set_llm_cache(RedisCache(redis_client))
        print("--- [LLM Factory] Caché de LLM con Redis configurada con éxito. ---")
    except redis.exceptions.ConnectionError as e:
        print(f"--- [LLM Factory] ADVERTENCIA: No se pudo conectar a Redis para la caché de LLM. Error: {e} ---")
        print("--- [LLM Factory] La aplicación continuará sin caché de respuestas. ---")

def get_llm(llm_config: Dict[str, Any]):
    provider = llm_config.get("provider")
    model_name = llm_config.get("model")
    
    print(f"--- [LLM Factory] Creando instancia para proveedor: {provider}, modelo: {model_name} ---")

    if provider == "google":
        return ChatVertexAI(model_name=model_name, temperature=1)
    elif provider == "openai":
        return ChatOpenAI(model_name=model_name, temperature=1)
    else:
        raise ValueError(f"Proveedor de LLM desconocido: {provider}")
