"""
Vector Store management with ChromaDB and Ollama (local embeddings).
Supports incremental updates when new documents are added.
Se conecta al modelo OllamaEmbeddings para convertir los fragmentos de texto en vectores numéricos. Estos números representan el significado semántico del texto.
Contiene la lógica para interactuar con ChromaDB. Define cómo se guardan los vectores y cómo se realiza la "búsqueda por similitud" cuando el usuario hace una pregunta
"""
import os
import shutil
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

from .document_loader import load_markdown_documents

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHROMA_PATH = BASE_DIR / "chroma_db"

# Singleton instance
_vector_store_instance: Optional["VectorStore"] = None


class VectorStore:
    """
    ChromaDB-based vector store for insurance document search.
    Supports automatic updates when documents change.
    """
    
    def __init__(self):
        # Usar embeddings locales con Ollama
        self.embeddings = OllamaEmbeddings(
            model="mxbai-embed-large"
        )
        # Chunk size reducido para compatibilidad con Ollama embeddings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n## ", "\n### ", "\n---\n", "\n\n", "\n", " ", ""]
        )
        self.db: Optional[Chroma] = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize or load the vector store."""
        documents, has_changes = load_markdown_documents()
        
        if not documents:
            print("⚠️  No documents to index")
            return
        
        # Check if ChromaDB already exists
        chroma_exists = CHROMA_PATH.exists() and any(CHROMA_PATH.iterdir()) if CHROMA_PATH.exists() else False
        
        if chroma_exists and not has_changes:
            # Load existing ChromaDB
            print("📂 Loading existing ChromaDB...")
            self.db = Chroma(
                persist_directory=str(CHROMA_PATH),
                embedding_function=self.embeddings,
                collection_name="insurance_docs"
            )
            print(f"✅ ChromaDB loaded with {self.db._collection.count()} documents")
        else:
            # Create new index
            print("🔨 Creating new ChromaDB index...")
            self._create_index(documents)
    
    def _create_index(self, documents: List[Document]) -> None:
        """Create a new ChromaDB index from documents."""
        # Split documents into chunks
        chunks = self.text_splitter.split_documents(documents)
        print(f"📑 Split into {len(chunks)} chunks")
        
        # Ensure directory exists
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        
        # Create ChromaDB index
        self.db = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=str(CHROMA_PATH),
            collection_name="insurance_docs"
        )
        print(f"💾 ChromaDB saved to {CHROMA_PATH}")
    
    def rebuild_index(self) -> None:
        """Force rebuild the entire index."""
        print("🔄 Rebuilding ChromaDB index...")
        
        # Delete existing collection if exists
        if self.db:
            try:
                self.db.delete_collection()
            except Exception:
                pass
        
        # Remove existing files
        if CHROMA_PATH.exists():
            shutil.rmtree(CHROMA_PATH)
        
        documents, _ = load_markdown_documents(force_reload=True)
        if documents:
            self._create_index(documents)
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add new documents to existing index."""
        if self.db is None:
            self._create_index(documents)
            return
        
        chunks = self.text_splitter.split_documents(documents)
        self.db.add_documents(chunks)
        print(f"➕ Added {len(chunks)} new chunks to ChromaDB")
    
    def search(
        self, 
        query: str, 
        k: int = 3, 
        insurance_type: Optional[str] = None
    ) -> List[Document]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            k: Number of results to return
            insurance_type: Optional filter by insurance type (coche, hogar, moto)
        
        Returns:
            List of relevant Document objects
        """
        if self.db is None:
            return []
        
        if insurance_type:
            # Filter search by metadata - ChromaDB native filtering
            results = self.db.similarity_search(
                query, 
                k=k,
                filter={"insurance_type": insurance_type}
            )
        else:
            results = self.db.similarity_search(query, k=k)
        
        return results
    
    def search_with_scores(
        self, 
        query: str, 
        k: int = 3
    ) -> List[tuple[Document, float]]:
        """
        Search for relevant documents with relevance scores.
        
        Args:
            query: Search query
            k: Number of results to return
        
        Returns:
            List of (Document, score) tuples
        """
        if self.db is None:
            return []
        
        return self.db.similarity_search_with_score(query, k=k)


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
    k: int = 3
) -> str:
    """
    Search insurance information in the knowledge base.
    This is the main function to be used by agents.
    
    Args:
        query: What to search for (e.g., "coberturas todo riesgo")
        insurance_type: Optional filter (coche, hogar, moto)
        k: Number of results
    
    Returns:
        Formatted string with relevant information
    """
    store = get_vector_store()
    results = store.search(query, k=k, insurance_type=insurance_type)
    
    if not results:
        return "No se encontró información relevante en la base de conocimientos."
    
    # Format results
    formatted_results = []
    for i, doc in enumerate(results, 1):
        source = doc.metadata.get("filename", "Desconocido")
        product = doc.metadata.get("product", "")
        ins_type = doc.metadata.get("insurance_type", "")
        
        header = f"**Fuente {i}:** {source}"
        if product:
            header += f" | Producto: {product}"
        if ins_type:
            header += f" | Tipo: {ins_type}"
        
        formatted_results.append(f"{header}\n{doc.page_content[:1500]}...")
    
    return "\n\n---\n\n".join(formatted_results)


# CLI for testing and rebuilding
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rebuild":
        store = get_vector_store()
        store.rebuild_index()
    else:
        # Test search
        print("\n🔍 Testing search...")
        result = search_insurance_info("coberturas todo riesgo coche")
        print(result[:500])
