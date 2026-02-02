import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from typing import Dict, Any

def get_llm(llm_config: Dict[str, Any]):
    provider = llm_config.get("provider")
    model_name = llm_config.get("model")
    
    print(f"--- [LLM Factory] Creando instancia para proveedor: {provider}, modelo: {model_name} ---")

    if provider == "google":
        # API key de Google AI Studio (https://aistudio.google.com/app/apikey)
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY no está configurada. "
                "Crea una API key en https://aistudio.google.com/app/apikey y añádela al .env"
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
