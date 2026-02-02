"""
Vector Store management with ChromaDB and Ollama (local embeddings).

Este módulo gestiona la base de datos vectorial para búsqueda semántica con
soporte completo de Metadata Filtering:

- Embeddings locales con Ollama (mxbai-embed-large)
- Almacenamiento persistente con ChromaDB
- Actualizaciones incrementales (solo reprocesa cuando hay cambios)
- Metadata Filtering: cada chunk tiene etiquetas obligatorias
- Búsqueda filtrada por insurance_type, product, doc_type

Metadatos por chunk (heredados del documento padre):
    - insurance_type: coche | hogar | moto (OBLIGATORIO)
    - product: nombre del producto/modalidad
    - doc_type: condiciones_generales | nota_informativa | documento_informacion
    - source: ruta completa del archivo
    - filename: nombre del archivo

Uso:
    from app.rag.vector_store import search_insurance_info
    
    # Búsqueda filtrada por tipo de seguro
    result = search_insurance_info("coberturas todo riesgo", insurance_type="coche")
    
    # Búsqueda filtrada por producto específico
    result = search_insurance_info("franquicia", insurance_type="moto", product="moto_todo_riesgo")
"""
import logging
import shutil
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

from .document_loader import (
    load_documents,
    validate_metadata,
    normalize_text,
    VALID_INSURANCE_TYPES,
)

# Configuración de logging
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHROMA_PATH = BASE_DIR / "chroma_db"

# Singleton instance
_vector_store_instance: Optional["VectorStore"] = None


class VectorStore:
    """
    ChromaDB-based vector store for insurance document search with Metadata Filtering.
    
    Features:
    - Automatic initialization and update detection
    - Support for Markdown documents
    - Metadata Filtering: every chunk has mandatory labels (insurance_type, product, doc_type)
    - Filtered search by insurance_type, product, doc_type
    - Relevance scoring
    - Statistics by metadata category
    
    Metadata Fields (inherited from parent document):
        - insurance_type: coche | hogar | moto (REQUIRED)
        - product: nombre del producto normalizado
        - doc_type: tipo de documento
        - source: ruta completa
        - filename: nombre del archivo
    
    Attributes:
        embeddings: Ollama embedding model
        text_splitter: Chunk splitter optimized for insurance documents
        db: ChromaDB instance
    """
    
    # Required metadata fields that must be present in every chunk
    REQUIRED_METADATA_FIELDS = ["insurance_type"]
    
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
    
    def _validate_chunks_metadata(self, chunks: List[Document]) -> Tuple[List[Document], int]:
        """
        Validate that all chunks have required metadata fields.
        
        Args:
            chunks: List of document chunks to validate
            
        Returns:
            Tuple of (valid_chunks, invalid_count)
        """
        valid_chunks = []
        invalid_count = 0
        
        for chunk in chunks:
            # Check required fields
            missing_fields = [
                field for field in self.REQUIRED_METADATA_FIELDS 
                if not chunk.metadata.get(field)
            ]
            
            if missing_fields:
                logger.warning(
                    f"Chunk missing required metadata fields {missing_fields}: "
                    f"{chunk.page_content[:50]}..."
                )
                invalid_count += 1
                continue
            
            valid_chunks.append(chunk)
        
        return valid_chunks, invalid_count
    
    def _log_chunks_metadata_stats(self, chunks: List[Document]) -> Dict[str, Dict[str, int]]:
        """
        Log statistics about metadata distribution in chunks.
        
        Args:
            chunks: List of document chunks
            
        Returns:
            Dictionary with metadata statistics
        """
        stats: Dict[str, Dict[str, int]] = {
            "by_insurance_type": {},
            "by_product": {},
            "by_doc_type": {},
        }
        
        for chunk in chunks:
            ins_type = chunk.metadata.get("insurance_type", "unknown")
            product = chunk.metadata.get("product", "unknown")
            doc_type = chunk.metadata.get("doc_type", "unknown")
            
            stats["by_insurance_type"][ins_type] = \
                stats["by_insurance_type"].get(ins_type, 0) + 1
            stats["by_product"][product] = \
                stats["by_product"].get(product, 0) + 1
            stats["by_doc_type"][doc_type] = \
                stats["by_doc_type"].get(doc_type, 0) + 1
        
        logger.info("Chunks metadata distribution:")
        logger.info(f"  By insurance_type: {stats['by_insurance_type']}")
        logger.info(f"  By product: {stats['by_product']}")
        logger.info(f"  By doc_type: {stats['by_doc_type']}")
        
        return stats
    
    def _create_index(self, documents: List[Document]) -> None:
        """
        Create a new ChromaDB index from documents with validated metadata.
        
        Each chunk inherits metadata from its parent document, ensuring
        Metadata Filtering capabilities in ChromaDB.
        
        Args:
            documents: List of Document objects to index
        """
        # Split documents into chunks (metadata is automatically inherited)
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks")
        
        # Validate chunks have required metadata
        valid_chunks, invalid_count = self._validate_chunks_metadata(chunks)
        
        if invalid_count > 0:
            logger.warning(f"Filtered out {invalid_count} chunks with missing metadata")
        
        if not valid_chunks:
            logger.error("No valid chunks to index after metadata validation")
            return
        
        # Log metadata statistics for transparency
        self._log_chunks_metadata_stats(valid_chunks)
        
        # Ensure directory exists
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        
        # Remove existing ChromaDB if present
        if CHROMA_PATH.exists() and any(CHROMA_PATH.iterdir()):
            shutil.rmtree(CHROMA_PATH)
            CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        
        # Create ChromaDB index with validated chunks
        self.db = Chroma.from_documents(
            documents=valid_chunks,
            embedding=self.embeddings,
            persist_directory=str(CHROMA_PATH),
            collection_name="insurance_docs"
        )
        logger.info(
            f"ChromaDB index created with {len(valid_chunks)} chunks "
            f"(Metadata Filtering enabled) at {CHROMA_PATH}"
        )
    
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
    
    def _build_chroma_filter(
        self,
        insurance_type: Optional[str] = None,
        product: Optional[str] = None,
        doc_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Build a ChromaDB-compatible filter from metadata fields.
        
        ChromaDB requires $and operator when multiple conditions are specified.
        
        Args:
            insurance_type: Filter by insurance type
            product: Filter by product name
            doc_type: Filter by document type
            
        Returns:
            ChromaDB filter dict or None if no filters
        """
        conditions = []
        
        if insurance_type:
            conditions.append({"insurance_type": normalize_text(insurance_type)})
        if product:
            conditions.append({"product": normalize_text(product)})
        if doc_type:
            conditions.append({"doc_type": doc_type})
        
        if not conditions:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            # Multiple conditions require $and operator
            return {"$and": conditions}
    
    def search(
        self, 
        query: str, 
        k: int = 3, 
        insurance_type: Optional[str] = None,
        product: Optional[str] = None,
        doc_type: Optional[str] = None
    ) -> List[Document]:
        """
        Search for relevant documents with Metadata Filtering.
        
        Args:
            query: Search query
            k: Number of results to return
            insurance_type: Optional filter by insurance type (coche, hogar, moto)
            product: Optional filter by product name
            doc_type: Optional filter by document type (condiciones_generales, etc.)
        
        Returns:
            List of relevant Document objects
            
        Example:
            # Search only in car insurance documents
            results = store.search("coberturas", insurance_type="coche")
            
            # Search in a specific product
            results = store.search("franquicia", insurance_type="moto", product="moto_todo_riesgo")
        """
        if self.db is None:
            logger.warning("Search called but no database initialized")
            return []
        
        # Build ChromaDB-compatible filter
        search_filter = self._build_chroma_filter(insurance_type, product, doc_type)
        
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
        insurance_type: Optional[str] = None,
        product: Optional[str] = None,
        doc_type: Optional[str] = None
    ) -> List[Tuple[Document, float]]:
        """
        Search for relevant documents with relevance scores and Metadata Filtering.
        
        Lower scores indicate higher relevance (distance-based).
        
        Args:
            query: Search query
            k: Number of results to return
            insurance_type: Optional filter by insurance type (coche, hogar, moto)
            product: Optional filter by product name
            doc_type: Optional filter by document type
        
        Returns:
            List of (Document, score) tuples, sorted by relevance
        """
        if self.db is None:
            logger.warning("Search called but no database initialized")
            return []
        
        # Build ChromaDB-compatible filter
        search_filter = self._build_chroma_filter(insurance_type, product, doc_type)
        
        if search_filter:
            results = self.db.similarity_search_with_score(
                query, 
                k=k,
                filter=search_filter
            )
        else:
            results = self.db.similarity_search_with_score(query, k=k)
        
        logger.debug(f"Found {len(results)} results with scores")
        return results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection including metadata distribution.
        
        Returns:
            Dictionary with collection statistics and metadata breakdown
        """
        if self.db is None:
            return {"status": "not_initialized", "count": 0}
        
        try:
            count = self.db._collection.count()
            
            stats = {
                "status": "ready",
                "total_chunks": count,
                "path": str(CHROMA_PATH),
                "valid_insurance_types": list(VALID_INSURANCE_TYPES),
            }
            
            # Get metadata distribution by querying all documents
            try:
                all_docs = self.db._collection.get(include=["metadatas"])
                metadatas = all_docs.get("metadatas", [])
                
                metadata_stats: Dict[str, Dict[str, int]] = {
                    "by_insurance_type": {},
                    "by_product": {},
                    "by_doc_type": {},
                }
                
                for meta in metadatas:
                    if meta:
                        ins_type = meta.get("insurance_type", "unknown")
                        product = meta.get("product", "unknown")
                        doc_type = meta.get("doc_type", "unknown")
                        
                        metadata_stats["by_insurance_type"][ins_type] = \
                            metadata_stats["by_insurance_type"].get(ins_type, 0) + 1
                        metadata_stats["by_product"][product] = \
                            metadata_stats["by_product"].get(product, 0) + 1
                        metadata_stats["by_doc_type"][doc_type] = \
                            metadata_stats["by_doc_type"].get(doc_type, 0) + 1
                
                stats["metadata_distribution"] = metadata_stats
                
            except Exception as e:
                logger.warning(f"Could not get metadata distribution: {e}")
            
            return stats
            
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
    product: Optional[str] = None,
    doc_type: Optional[str] = None,
    k: int = 3,
    include_scores: bool = False
) -> str:
    """
    Search insurance information in the knowledge base with Metadata Filtering.
    This is the main function to be used by agents.
    
    Metadata Filtering allows precise retrieval by filtering chunks based on:
    - insurance_type: coche | hogar | moto
    - product: specific product name (e.g., "moto_todo_riesgo", "terceros")
    - doc_type: condiciones_generales | nota_informativa | documento_informacion
    
    Args:
        query: What to search for (e.g., "coberturas todo riesgo")
        insurance_type: Filter by insurance type (coche, hogar, moto)
        product: Filter by specific product
        doc_type: Filter by document type
        k: Number of results
        include_scores: If True, include relevance scores in output
    
    Returns:
        Formatted string with relevant information
    
    Example:
        >>> # Search only in car insurance
        >>> result = search_insurance_info("coberturas", insurance_type="coche")
        
        >>> # Search in specific motorcycle product
        >>> result = search_insurance_info("franquicia", insurance_type="moto", product="moto_todo_riesgo")
        
        >>> # Search only in general conditions documents
        >>> result = search_insurance_info("exclusiones", doc_type="condiciones_generales")
    """
    filter_info = f"type={insurance_type}" if insurance_type else "no filter"
    if product:
        filter_info += f", product={product}"
    if doc_type:
        filter_info += f", doc_type={doc_type}"
    
    logger.info(f"Searching: '{query}' | {filter_info} | k={k}")
    
    store = get_vector_store()
    
    if include_scores:
        results_with_scores = store.search_with_scores(
            query, k=k, 
            insurance_type=insurance_type,
            product=product,
            doc_type=doc_type
        )
        if not results_with_scores:
            return "No se encontró información relevante en la base de conocimientos."
        
        formatted_results = []
        for i, (doc, score) in enumerate(results_with_scores, 1):
            source = doc.metadata.get("filename", "Desconocido")
            meta_product = doc.metadata.get("product", "")
            ins_type = doc.metadata.get("insurance_type", "")
            meta_doc_type = doc.metadata.get("doc_type", "")
            
            header = f"**Fuente {i}** (relevancia: {score:.3f}): {source}"
            if ins_type:
                header += f" | Seguro: {ins_type}"
            if meta_product:
                header += f" | Producto: {meta_product}"
            if meta_doc_type:
                header += f" | Tipo doc: {meta_doc_type}"
            
            # Truncate content if too long
            content = doc.page_content
            if len(content) > 1500:
                content = content[:1500] + "..."
            
            formatted_results.append(f"{header}\n{content}")
        
        return "\n\n---\n\n".join(formatted_results)
    
    else:
        results = store.search(
            query, k=k, 
            insurance_type=insurance_type,
            product=product,
            doc_type=doc_type
        )
        
        if not results:
            return "No se encontró información relevante en la base de conocimientos."
        
        # Format results
        formatted_results = []
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get("filename", "Desconocido")
            meta_product = doc.metadata.get("product", "")
            ins_type = doc.metadata.get("insurance_type", "")
            meta_doc_type = doc.metadata.get("doc_type", "")
            
            header = f"**Fuente {i}:** {source}"
            if ins_type:
                header += f" | Seguro: {ins_type}"
            if meta_product:
                header += f" | Producto: {meta_product}"
            if meta_doc_type:
                header += f" | Tipo doc: {meta_doc_type}"
            
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
