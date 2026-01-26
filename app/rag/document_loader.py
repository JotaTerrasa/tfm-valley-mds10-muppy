"""
Document loader for insurance Markdown files.

Este módulo carga documentos .md de la carpeta data/ con:
- Detección de cambios mediante hash MD5 (evita reprocesar)
- Extracción automática de metadatos desde la estructura de carpetas
- Soporte para filtrado por tipo de seguro

Estructura esperada:
    data/
    ├── seguro_coche/
    │   ├── Terceros/
    │   │   └── documento.md
    │   └── Todo_Riesgo/
    │       └── documento.md
    ├── seguro_hogar/
    └── seguro_moto/
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

from langchain_core.documents import Document

# Configuración de logging
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data"
METADATA_PATH = BASE_DIR / "chroma_db" / "documents_metadata.json"


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate MD5 hash of a file to detect changes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MD5 hash string
    """
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def load_metadata() -> Dict[str, str]:
    """
    Load stored metadata with file hashes.
    
    Returns:
        Dictionary mapping file paths to their MD5 hashes
    """
    if METADATA_PATH.exists():
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_metadata(metadata: Dict[str, str]) -> None:
    """
    Save metadata with file hashes.
    
    Args:
        metadata: Dictionary mapping file paths to their MD5 hashes
    """
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def extract_insurance_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from file path structure.
    
    Example: data/seguro_coche/Todo_Riesgo/documento.md
    -> insurance_type: "coche", product: "Todo_Riesgo"
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Dictionary with extracted metadata
    """
    parts = file_path.relative_to(DATA_PATH).parts
    
    metadata = {
        "source": str(file_path),
        "filename": file_path.name,
    }
    
    if len(parts) >= 2:
        # Extract insurance type from folder name (e.g., "seguro_coche" -> "coche")
        insurance_folder = parts[0]
        if insurance_folder.startswith("seguro_"):
            metadata["insurance_type"] = insurance_folder.replace("seguro_", "")
        else:
            metadata["insurance_type"] = insurance_folder
    
    if len(parts) >= 3:
        metadata["product"] = parts[1]
    
    return metadata


def load_documents(force_reload: bool = False) -> Tuple[List[Document], bool]:
    """
    Load all Markdown documents from the data directory.
    
    Features:
    - Change detection via MD5 hashes (only reprocesses when files change)
    - Automatic metadata extraction from folder structure
    - Logging of loaded documents
    
    Args:
        force_reload: If True, reload all documents regardless of changes.
    
    Returns:
        Tuple of (documents list, has_changes boolean)
    """
    documents = []
    current_hashes = {}
    stored_hashes = load_metadata()
    has_changes = force_reload
    
    # Find all .md files
    md_files = list(DATA_PATH.rglob("*.md"))
    
    if not md_files:
        logger.warning(f"No se encontraron archivos .md en {DATA_PATH}")
        return [], False
    
    logger.info(f"Found {len(md_files)} Markdown files to process")
    
    for md_file in md_files:
        file_key = str(md_file.relative_to(BASE_DIR))
        current_hash = calculate_file_hash(md_file)
        current_hashes[file_key] = current_hash
        
        # Check if file is new or modified
        if file_key not in stored_hashes or stored_hashes[file_key] != current_hash:
            has_changes = True
        
        # Load document content
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            metadata = extract_insurance_metadata(md_file)
            documents.append(Document(page_content=content, metadata=metadata))
            logger.debug(f"Loaded: {md_file.name}")
            
        except Exception as e:
            logger.error(f"Error loading {md_file}: {e}")
    
    # Check for deleted files
    for old_key in stored_hashes:
        if old_key not in current_hashes:
            has_changes = True
            logger.info(f"Detected deleted file: {old_key}")
            break
    
    # Save new metadata
    save_metadata(current_hashes)
    
    logger.info(f"Loaded {len(documents)} documents from {DATA_PATH}")
    
    return documents, has_changes


# Alias for backwards compatibility
def load_markdown_documents(force_reload: bool = False) -> Tuple[List[Document], bool]:
    """Alias for load_documents() - kept for backwards compatibility."""
    return load_documents(force_reload=force_reload)


def get_documents_by_insurance_type(insurance_type: str) -> List[Document]:
    """
    Load documents filtered by insurance type.
    
    Args:
        insurance_type: Type of insurance to filter by (e.g., "coche", "hogar", "moto")
        
    Returns:
        List of documents matching the insurance type
    """
    all_docs, _ = load_documents()
    return [
        doc for doc in all_docs 
        if doc.metadata.get("insurance_type") == insurance_type
    ]


def get_document_stats() -> Dict[str, Any]:
    """
    Get statistics about loaded documents.
    
    Returns:
        Dictionary with document statistics
    """
    documents, _ = load_documents()
    
    stats = {
        "total_documents": len(documents),
        "by_insurance": {},
        "by_product": {},
    }
    
    for doc in documents:
        # Count by insurance type
        ins_type = doc.metadata.get("insurance_type", "unknown")
        stats["by_insurance"][ins_type] = stats["by_insurance"].get(ins_type, 0) + 1
        
        # Count by product
        product = doc.metadata.get("product", "unknown")
        stats["by_product"][product] = stats["by_product"].get(product, 0) + 1
    
    return stats
