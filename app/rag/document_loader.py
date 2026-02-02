"""
Document loader for insurance Markdown files with Metadata Filtering support.

Este módulo carga documentos .md de la carpeta data/ con:
- Detección de cambios mediante hash MD5 (evita reprocesar)
- Extracción automática de metadatos desde la estructura de carpetas
- Metadatos obligatorios para Metadata Filtering en ChromaDB
- Soporte para filtrado por tipo de seguro, producto y tipo de documento

Estructura esperada:
    data/
    ├── seguro_coche/
    │   ├── Terceros/
    │   │   └── documento.md
    │   └── Todo_Riesgo/
    │       └── documento.md
    ├── seguro_hogar/
    └── seguro_moto/

Metadatos extraídos por chunk:
    - insurance_type: coche | hogar | moto (OBLIGATORIO)
    - product: nombre del producto/modalidad
    - doc_type: condiciones_generales | nota_informativa | documento_informacion | general
    - source: ruta completa del archivo
    - filename: nombre del archivo
"""
import hashlib
import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from langchain_core.documents import Document

# Configuración de logging
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data"
METADATA_PATH = BASE_DIR / "chroma_db" / "documents_metadata.json"

# ============================================================================
# CONSTANTES DE METADATOS - Valores válidos para Metadata Filtering
# ============================================================================

# Tipos de seguro válidos (obligatorio en cada chunk)
VALID_INSURANCE_TYPES = {"coche", "hogar", "moto"}

# Patrones para detectar el tipo de documento desde el nombre del archivo
DOC_TYPE_PATTERNS = {
    "condiciones_generales": [
        r"condiciones[_\s]?generales",
        r"^[A-Za-z]+\.md$",  # Archivos como "Terceros.md", "Todo_Riesgo.md"
    ],
    "nota_informativa": [
        r"nota[_\s]?info",
        r"nota[_\s]?informativa",
    ],
    "documento_informacion": [
        r"documento[_\s]?info",
        r"documento[_\s]?información",
    ],
    "general": [
        r"general",
        r"informacion[_\s]?general",
    ],
}


def normalize_text(text: str) -> str:
    """
    Normalize text for consistent metadata values.
    
    - Converts to lowercase
    - Removes accents (á -> a, ñ -> n)
    - Replaces spaces with underscores
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text string
    """
    # Lowercase
    text = text.lower()
    # Remove accents using unicode normalization
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    # Replace spaces with underscores
    text = text.replace(' ', '_')
    return text


def detect_doc_type(filename: str) -> str:
    """
    Detect document type from filename using pattern matching.
    
    Args:
        filename: Name of the file (e.g., "moto_condiciones_generales_terceros.md")
        
    Returns:
        Document type: condiciones_generales | nota_informativa | documento_informacion | general | unknown
    """
    filename_lower = normalize_text(filename)
    
    for doc_type, patterns in DOC_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, filename_lower, re.IGNORECASE):
                return doc_type
    
    return "unknown"


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
    Extract and validate metadata from file path structure.
    
    Implements Metadata Filtering requirements:
    - insurance_type: OBLIGATORIO, normalizado (coche, hogar, moto)
    - product: nombre del producto/modalidad, normalizado
    - doc_type: tipo de documento detectado del nombre del archivo
    
    Example: data/seguro_coche/Todo_Riesgo/documento.md
    -> insurance_type: "coche", product: "todo_riesgo", doc_type: "condiciones_generales"
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Dictionary with extracted and validated metadata
        
    Raises:
        ValueError: If insurance_type cannot be extracted (mandatory field)
    """
    parts = file_path.relative_to(DATA_PATH).parts
    
    metadata = {
        "source": str(file_path),
        "filename": file_path.name,
    }
    
    # Extract insurance_type (OBLIGATORIO)
    if len(parts) >= 1:
        insurance_folder = parts[0]
        if insurance_folder.startswith("seguro_"):
            insurance_type = insurance_folder.replace("seguro_", "")
        else:
            insurance_type = insurance_folder
        
        # Normalize insurance type
        insurance_type = normalize_text(insurance_type)
        
        # Validate against allowed values
        if insurance_type not in VALID_INSURANCE_TYPES:
            logger.warning(
                f"Unknown insurance_type '{insurance_type}' for {file_path}. "
                f"Valid types: {VALID_INSURANCE_TYPES}"
            )
        
        metadata["insurance_type"] = insurance_type
    else:
        raise ValueError(
            f"Cannot extract insurance_type from path: {file_path}. "
            "File must be inside a seguro_* folder."
        )
    
    # Extract product (normalizado)
    if len(parts) >= 2:
        product = normalize_text(parts[1])
        metadata["product"] = product
    else:
        metadata["product"] = "general"
    
    # Detect document type from filename
    doc_type = detect_doc_type(file_path.name)
    metadata["doc_type"] = doc_type
    
    return metadata


def validate_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Validate that metadata contains all required fields for Metadata Filtering.
    
    Required fields:
    - insurance_type: must be one of VALID_INSURANCE_TYPES
    
    Args:
        metadata: Metadata dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Check insurance_type exists and is valid
    insurance_type = metadata.get("insurance_type")
    if not insurance_type:
        logger.error("Missing required metadata field: insurance_type")
        return False
    
    if insurance_type not in VALID_INSURANCE_TYPES:
        logger.warning(
            f"Invalid insurance_type: '{insurance_type}'. "
            f"Expected one of: {VALID_INSURANCE_TYPES}"
        )
        # Still return True as it might be a new type
    
    return True


def load_documents(force_reload: bool = False) -> Tuple[List[Document], bool]:
    """
    Load all Markdown documents from the data directory with validated metadata.
    
    Features:
    - Change detection via MD5 hashes (only reprocesses when files change)
    - Automatic metadata extraction from folder structure
    - Metadata validation for Metadata Filtering compliance
    - Logging of loaded documents with metadata stats
    
    Each document will have the following metadata (for Metadata Filtering):
    - insurance_type: coche | hogar | moto (OBLIGATORIO)
    - product: nombre del producto normalizado
    - doc_type: tipo de documento
    - source: ruta completa
    - filename: nombre del archivo
    
    Args:
        force_reload: If True, reload all documents regardless of changes.
    
    Returns:
        Tuple of (documents list, has_changes boolean)
    """
    documents = []
    current_hashes = {}
    stored_hashes = load_metadata()
    has_changes = force_reload
    
    # Stats for logging
    metadata_stats: Dict[str, Dict[str, int]] = {
        "by_insurance_type": {},
        "by_product": {},
        "by_doc_type": {},
    }
    skipped_invalid = 0
    
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
            
            # Validate metadata before adding document
            if not validate_metadata(metadata):
                logger.warning(f"Skipping document with invalid metadata: {md_file}")
                skipped_invalid += 1
                continue
            
            documents.append(Document(page_content=content, metadata=metadata))
            
            # Update stats
            ins_type = metadata.get("insurance_type", "unknown")
            product = metadata.get("product", "unknown")
            doc_type = metadata.get("doc_type", "unknown")
            
            metadata_stats["by_insurance_type"][ins_type] = \
                metadata_stats["by_insurance_type"].get(ins_type, 0) + 1
            metadata_stats["by_product"][product] = \
                metadata_stats["by_product"].get(product, 0) + 1
            metadata_stats["by_doc_type"][doc_type] = \
                metadata_stats["by_doc_type"].get(doc_type, 0) + 1
            
            logger.debug(
                f"Loaded: {md_file.name} | "
                f"type={ins_type}, product={product}, doc_type={doc_type}"
            )
            
        except ValueError as e:
            logger.error(f"Metadata extraction failed for {md_file}: {e}")
            skipped_invalid += 1
        except Exception as e:
            logger.error(f"Error loading {md_file}: {e}")
            skipped_invalid += 1
    
    # Check for deleted files
    for old_key in stored_hashes:
        if old_key not in current_hashes:
            has_changes = True
            logger.info(f"Detected deleted file: {old_key}")
            break
    
    # Save new metadata
    save_metadata(current_hashes)
    
    # Log summary with metadata distribution
    logger.info(f"Loaded {len(documents)} documents from {DATA_PATH}")
    if skipped_invalid > 0:
        logger.warning(f"Skipped {skipped_invalid} documents with invalid metadata")
    
    logger.info(f"Metadata distribution:")
    logger.info(f"  By insurance_type: {metadata_stats['by_insurance_type']}")
    logger.info(f"  By product: {metadata_stats['by_product']}")
    logger.info(f"  By doc_type: {metadata_stats['by_doc_type']}")
    
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
    # Normalize input for consistent matching
    insurance_type = normalize_text(insurance_type)
    
    all_docs, _ = load_documents()
    return [
        doc for doc in all_docs 
        if doc.metadata.get("insurance_type") == insurance_type
    ]


def get_documents_by_filter(
    insurance_type: Optional[str] = None,
    product: Optional[str] = None,
    doc_type: Optional[str] = None
) -> List[Document]:
    """
    Load documents filtered by multiple metadata fields.
    
    Args:
        insurance_type: Filter by insurance type (coche, hogar, moto)
        product: Filter by product name
        doc_type: Filter by document type
        
    Returns:
        List of documents matching all specified filters
    """
    all_docs, _ = load_documents()
    
    filtered = all_docs
    
    if insurance_type:
        insurance_type = normalize_text(insurance_type)
        filtered = [d for d in filtered if d.metadata.get("insurance_type") == insurance_type]
    
    if product:
        product = normalize_text(product)
        filtered = [d for d in filtered if d.metadata.get("product") == product]
    
    if doc_type:
        filtered = [d for d in filtered if d.metadata.get("doc_type") == doc_type]
    
    return filtered


def get_document_stats() -> Dict[str, Any]:
    """
    Get statistics about loaded documents.
    
    Returns:
        Dictionary with document statistics including metadata distribution
    """
    documents, _ = load_documents()
    
    stats = {
        "total_documents": len(documents),
        "by_insurance_type": {},
        "by_product": {},
        "by_doc_type": {},
        "valid_insurance_types": list(VALID_INSURANCE_TYPES),
    }
    
    for doc in documents:
        # Count by insurance type
        ins_type = doc.metadata.get("insurance_type", "unknown")
        stats["by_insurance_type"][ins_type] = stats["by_insurance_type"].get(ins_type, 0) + 1
        
        # Count by product
        product = doc.metadata.get("product", "unknown")
        stats["by_product"][product] = stats["by_product"].get(product, 0) + 1
        
        # Count by doc_type
        doc_type = doc.metadata.get("doc_type", "unknown")
        stats["by_doc_type"][doc_type] = stats["by_doc_type"].get(doc_type, 0) + 1
    
    return stats


def get_available_metadata_values() -> Dict[str, List[str]]:
    """
    Get all unique metadata values currently in the document collection.
    
    Useful for building filter dropdowns or validating user input.
    
    Returns:
        Dictionary with lists of unique values for each metadata field
    """
    documents, _ = load_documents()
    
    values: Dict[str, set] = {
        "insurance_types": set(),
        "products": set(),
        "doc_types": set(),
    }
    
    for doc in documents:
        if ins_type := doc.metadata.get("insurance_type"):
            values["insurance_types"].add(ins_type)
        if product := doc.metadata.get("product"):
            values["products"].add(product)
        if doc_type := doc.metadata.get("doc_type"):
            values["doc_types"].add(doc_type)
    
    return {k: sorted(list(v)) for k, v in values.items()}
