import os
from langchain.memory import ConversationBufferWindowMemory, ConversationEntityMemory, ConversationBufferMemory
from langchain_core.language_models import BaseLanguageModel
from langchain_community.chat_message_histories import RedisChatMessageHistory
from dotenv import load_dotenv

load_dotenv()

def get_memory_for_agent(config: dict, llm: BaseLanguageModel, session_id: str):
    """
    Factory function to create the correct memory object based on agent configuration,
    using Redis as the backend for message history.
    """
    memory_config = config.get("memory", {})
    memory_type = memory_config.get("type")
    redis_url = os.getenv("REDIS_URL")

    if not redis_url:
        raise ValueError("La variable de entorno REDIS_URL no está configurada.")

    print(f"--- [Memoria] Intentando conectar a Redis en: {redis_url} ---")
    message_history = RedisChatMessageHistory(session_id=session_id, url=redis_url)
    print("--- [Memoria] Conexión con Redis establecida con éxito. ---")
    
    memory = None

    if memory_type == "entity":
        print(f"--- Creando memoria de tipo: Entity (Sesión: {session_id}) ---")
        memory = ConversationEntityMemory(
            llm=llm, 
            chat_memory=message_history, 
            memory_key="history", 
            return_messages=True
        )
    
    elif memory_type == "window":
        k = memory_config.get("k", 5)
        print(f"--- Creando memoria de tipo: Window (k={k}, Sesión: {session_id}) ---")
        memory = ConversationBufferWindowMemory(
            k=k, 
            chat_memory=message_history, 
            memory_key="history", 
            return_messages=True
        )

    elif memory_type == "buffer":
        print(f"--- Creando memoria de tipo: Buffer (Sesión: {session_id}) ---")
        memory = ConversationBufferMemory(
            chat_memory=message_history, 
            memory_key="history", 
            return_messages=True
        )

    else: 
        print(f"--- Creando memoria de tipo: Window por defecto (Sesión: {session_id}) ---")
        memory = ConversationBufferWindowMemory(
            k=5, 
            chat_memory=message_history, 
            memory_key="history", 
            return_messages=True
        )
    
    return memory
