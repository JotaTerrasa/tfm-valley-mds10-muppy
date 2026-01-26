"""
RAG (Retrieval-Augmented Generation) module for insurance document search.
Este es un archivo estándar de Python que marca la carpeta app como un paquete. 
Su presencia permite que otros archivos de tu proyecto (como tu futuro quote_agent) puedan importar las funciones de búsqueda haciendo algo como from app.vector_store import search_knowledge
"""
from .vector_store import VectorStore, get_vector_store
from .document_loader import load_markdown_documents

__all__ = ["VectorStore", "get_vector_store", "load_markdown_documents"]
