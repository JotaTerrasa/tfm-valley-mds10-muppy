from langchain.memory import ConversationBufferWindowMemory, ConversationEntityMemory, ConversationBufferMemory
from langchain_core.language_models import BaseLanguageModel
from langchain_core.chat_history import InMemoryChatMessageHistory

# Historial de mensajes por sesión (en memoria, sin Redis)
_session_histories: dict = {}

def _get_or_create_history(session_id: str):
    if session_id not in _session_histories:
        _session_histories[session_id] = InMemoryChatMessageHistory()
    return _session_histories[session_id]

def get_memory_for_agent(config: dict, llm: BaseLanguageModel, session_id: str):
    """
    Factory function to create the correct memory object based on agent configuration,
    using in-memory message history.
    """
    memory_config = config.get("memory", {})
    memory_type = memory_config.get("type")
    message_history = _get_or_create_history(session_id)
    
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
