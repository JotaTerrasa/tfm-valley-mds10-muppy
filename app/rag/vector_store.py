"""
Vector Store management with ChromaDB and Ollama (local embeddings).

Este módulo gestiona la base de datos vectorial para búsqueda semántica:
- Embeddings locales con Ollama (mxbai-embed-large)
- Almacenamiento persistente con ChromaDB
- Actualizaciones incrementales (solo reprocesa cuando hay cambios)
- Búsqueda filtrada por tipo de seguro

Uso:
    from app.rag.vector_store import search_insurance_info
    
    result = search_insurance_info("coberturas todo riesgo", insurance_type="coche")
"""
import logging
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

from .document_loader import load_documents

# Configuración de logging
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHROMA_PATH = BASE_DIR / "chroma_db"

# Singleton instance
_vector_store_instance: Optional["VectorStore"] = None


class VectorStore:
    """
    ChromaDB-based vector store for insurance document search.
    
    Features:
    - Automatic initialization and update detection
    - Support for PDF and Markdown documents
    - Filtered search by insurance type
    - Relevance scoring
    
    Attributes:
        embeddings: Ollama embedding model
        text_splitter: Chunk splitter optimized for insurance documents
        db: ChromaDB instance
    """
    
    def __init__(self, embedding_model: str = "mxbai-embed-large"):
        """
        Initialize the VectorStore.
        
        Args:
            embedding_model: Name of the Ollama embedding model to use
        """
        logger.info(f"Initializing VectorStore with model: {embedding_model}")
        
        # Usar embeddings locales con Ollama
        self.embeddings = OllamaEmbeddings(
            model=embedding_model
        )
        
        # Chunk splitter optimizado para documentos de seguros
        # Separadores específicos para Markdown y estructura de documentos
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=[
                "\n## ",      # Headers nivel 2
                "\n### ",     # Headers nivel 3
                "\n#### ",    # Headers nivel 4
                "\n---\n",    # Separadores horizontales
                "\n\n",       # Párrafos
                "\n",         # Líneas
                ". ",         # Oraciones
                " ",          # Palabras
                ""            # Caracteres
            ]
        )
        self.db: Optional[Chroma] = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize or load the vector store."""
        documents, has_changes = load_documents()
        
        if not documents:
            logger.warning("No documents found to index")
            return
        
        # Check if ChromaDB already exists
        chroma_exists = CHROMA_PATH.exists() and any(CHROMA_PATH.iterdir()) if CHROMA_PATH.exists() else False
        
        if chroma_exists and not has_changes:
            # Load existing ChromaDB
            logger.info("Loading existing ChromaDB...")
            self.db = Chroma(
                persist_directory=str(CHROMA_PATH),
                embedding_function=self.embeddings,
                collection_name="insurance_docs"
            )
            doc_count = self.db._collection.count()
            logger.info(f"ChromaDB loaded with {doc_count} chunks")
        else:
            # Create new index
            logger.info("Creating new ChromaDB index (documents changed or new)...")
            self._create_index(documents)
    
    def _create_index(self, documents: List[Document]) -> None:
        """
        Create a new ChromaDB index from documents.
        
        Args:
            documents: List of Document objects to index
        """
        # Split documents into chunks
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks")
        
        # Ensure directory exists
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        
        # Remove existing ChromaDB if present
        if CHROMA_PATH.exists() and any(CHROMA_PATH.iterdir()):
            shutil.rmtree(CHROMA_PATH)
            CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        
        # Create ChromaDB index
        self.db = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=str(CHROMA_PATH),
            collection_name="insurance_docs"
        )
        logger.info(f"ChromaDB index created and saved to {CHROMA_PATH}")
    
    def rebuild_index(self) -> None:
        """Force rebuild the entire index from scratch."""
        logger.info("Rebuilding ChromaDB index...")
        
        # Delete existing collection if exists
        if self.db:
            try:
                self.db.delete_collection()
            except Exception as e:
                logger.debug(f"Could not delete collection: {e}")
        
        # Remove existing files
        if CHROMA_PATH.exists():
            shutil.rmtree(CHROMA_PATH)
        
        documents, _ = load_documents(force_reload=True)
        if documents:
            self._create_index(documents)
            logger.info("Index rebuild complete")
        else:
            logger.warning("No documents found during rebuild")
    
    def add_documents(self, documents: List[Document]) -> int:
        """
        Add new documents to existing index.
        
        Args:
            documents: List of Document objects to add
            
        Returns:
            Number of chunks added
        """
        if self.db is None:
            self._create_index(documents)
            return len(self.text_splitter.split_documents(documents))
        
        chunks = self.text_splitter.split_documents(documents)
        self.db.add_documents(chunks)
        logger.info(f"Added {len(chunks)} new chunks to ChromaDB")
        return len(chunks)
    
    def search(
        self, 
        query: str, 
        k: int = 3, 
        insurance_type: Optional[str] = None,
        product: Optional[str] = None
    ) -> List[Document]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            k: Number of results to return
            insurance_type: Optional filter by insurance type (coche, hogar, moto)
            product: Optional filter by product name
        
        Returns:
            List of relevant Document objects
        """
        if self.db is None:
            logger.warning("Search called but no database initialized")
            return []
        
        # Build filter if specified
        search_filter = {}
        if insurance_type:
            search_filter["insurance_type"] = insurance_type
        if product:
            search_filter["product"] = product
        
        logger.debug(f"Searching: '{query}' with filter={search_filter}, k={k}")
        
        if search_filter:
            results = self.db.similarity_search(
                query, 
                k=k,
                filter=search_filter
            )
        else:
            results = self.db.similarity_search(query, k=k)
        
        logger.debug(f"Found {len(results)} results")
        return results
    
    def search_with_scores(
        self, 
        query: str, 
        k: int = 3,
        insurance_type: Optional[str] = None
    ) -> List[Tuple[Document, float]]:
        """
        Search for relevant documents with relevance scores.
        
        Lower scores indicate higher relevance (distance-based).
        
        Args:
            query: Search query
            k: Number of results to return
            insurance_type: Optional filter by insurance type
        
        Returns:
            List of (Document, score) tuples, sorted by relevance
        """
        if self.db is None:
            logger.warning("Search called but no database initialized")
            return []
        
        if insurance_type:
            results = self.db.similarity_search_with_score(
                query, 
                k=k,
                filter={"insurance_type": insurance_type}
            )
        else:
            results = self.db.similarity_search_with_score(query, k=k)
        
        logger.debug(f"Found {len(results)} results with scores")
        return results
    
    def get_collection_stats(self) -> dict:
        """
        Get statistics about the vector store collection.
        
        Returns:
            Dictionary with collection statistics
        """
        if self.db is None:
            return {"status": "not_initialized", "count": 0}
        
        try:
            count = self.db._collection.count()
            return {
                "status": "ready",
                "count": count,
                "path": str(CHROMA_PATH)
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"status": "error", "error": str(e)}


def get_vector_store() -> VectorStore:
    """
    Get or create the singleton VectorStore instance.
    This ensures we only load the index once per application lifecycle.
    """
    global _vector_store_instance
    
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    
    return _vector_store_instance


def search_insurance_info(
    query: str, 
    insurance_type: Optional[str] = None,
    k: int = 3,
    include_scores: bool = False
) -> str:
    """
    Search insurance information in the knowledge base.
    This is the main function to be used by agents.
    
    Args:
        query: What to search for (e.g., "coberturas todo riesgo")
        insurance_type: Optional filter (coche, hogar, moto)
        k: Number of results
        include_scores: If True, include relevance scores in output
    
    Returns:
        Formatted string with relevant information
    
    Example:
        >>> result = search_insurance_info("coberturas todo riesgo", insurance_type="coche")
        >>> print(result)
    """
    logger.info(f"Searching: '{query}' | type={insurance_type} | k={k}")
    
    store = get_vector_store()
    
    if include_scores:
        results_with_scores = store.search_with_scores(query, k=k, insurance_type=insurance_type)
        if not results_with_scores:
            return "No se encontró información relevante en la base de conocimientos."
        
        formatted_results = []
        for i, (doc, score) in enumerate(results_with_scores, 1):
            source = doc.metadata.get("filename", "Desconocido")
            product = doc.metadata.get("product", "")
            ins_type = doc.metadata.get("insurance_type", "")
            file_type = doc.metadata.get("file_type", "")
            
            header = f"**Fuente {i}** (relevancia: {score:.3f}): {source}"
            if product:
                header += f" | Producto: {product}"
            if ins_type:
                header += f" | Tipo: {ins_type}"
            if file_type:
                header += f" | Formato: {file_type}"
            
            # Truncate content if too long
            content = doc.page_content
            if len(content) > 1500:
                content = content[:1500] + "..."
            
            formatted_results.append(f"{header}\n{content}")
        
        return "\n\n---\n\n".join(formatted_results)
    
    else:
        results = store.search(query, k=k, insurance_type=insurance_type)
        
        if not results:
            return "No se encontró información relevante en la base de conocimientos."
        
        # Format results
        formatted_results = []
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get("filename", "Desconocido")
            product = doc.metadata.get("product", "")
            ins_type = doc.metadata.get("insurance_type", "")
            file_type = doc.metadata.get("file_type", "")
            
            header = f"**Fuente {i}:** {source}"
            if product:
                header += f" | Producto: {product}"
            if ins_type:
                header += f" | Tipo: {ins_type}"
            if file_type:
                header += f" | Formato: {file_type}"
            
            # Truncate content if too long
            content = doc.page_content
            if len(content) > 1500:
                content = content[:1500] + "..."
            
            formatted_results.append(f"{header}\n{content}")
        
        return "\n\n---\n\n".join(formatted_results)


# Alias for backwards compatibility with quote_agent.py
def search_knowledge(query: str, k: int = 3) -> str:
    """
    Legacy function for searching the knowledge base.
    
    Deprecated: Use search_insurance_info() instead.
    
    Args:
        query: Search query
        k: Number of results
        
    Returns:
        Formatted search results
    """
    return search_insurance_info(query, k=k)


# CLI for testing and rebuilding
if __name__ == "__main__":
    import sys
    
    # Configure logging for CLI
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "rebuild":
            print("Rebuilding ChromaDB index...")
            store = get_vector_store()
            store.rebuild_index()
            print("Done!")
            
        elif command == "stats":
            store = get_vector_store()
            stats = store.get_collection_stats()
            print(f"\nVector Store Stats:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
                
        elif command == "search":
            if len(sys.argv) < 3:
                print("Usage: python vector_store.py search 'your query'")
                sys.exit(1)
            query = sys.argv[2]
            insurance_type = sys.argv[3] if len(sys.argv) > 3 else None
            
            print(f"\nSearching: '{query}'")
            if insurance_type:
                print(f"Filter: insurance_type={insurance_type}")
            print("-" * 50)
            
            result = search_insurance_info(query, insurance_type=insurance_type, include_scores=True)
            print(result)
            
        else:
            print(f"Unknown command: {command}")
            print("Available commands: rebuild, stats, search")
    else:
        print("RAG Vector Store CLI")
        print("Usage:")
        print("  python vector_store.py rebuild              - Rebuild the index")
        print("  python vector_store.py stats                - Show index statistics")
        print("  python vector_store.py search 'query' [type] - Search the index")
