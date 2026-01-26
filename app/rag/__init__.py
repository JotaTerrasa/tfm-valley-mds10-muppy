"""
RAG (Retrieval-Augmented Generation) module for insurance document search.

Este módulo proporciona funcionalidades de búsqueda semántica para documentos
de seguros usando ChromaDB y embeddings locales con Ollama.

Uso básico:
    from app.rag import search_insurance_info
    
    # Búsqueda simple
    result = search_insurance_info("coberturas todo riesgo")
    
    # Búsqueda filtrada por tipo de seguro
    result = search_insurance_info("franquicia", insurance_type="coche")

Componentes:
    - VectorStore: Clase que gestiona la base de datos vectorial
    - search_insurance_info: Función principal para búsquedas
    - load_documents: Carga documentos Markdown desde data/
"""
from .vector_store import (
    VectorStore, 
    get_vector_store, 
    search_insurance_info,
    search_knowledge
)
from .document_loader import (
    load_documents,
    load_markdown_documents,
    get_documents_by_insurance_type,
    get_document_stats
)

__all__ = [
    "VectorStore",
    "get_vector_store",
    "search_insurance_info",
    "search_knowledge",
    "load_documents",
    "load_markdown_documents",
    "get_documents_by_insurance_type",
    "get_document_stats",
]
