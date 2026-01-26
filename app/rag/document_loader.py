"""
Document loader for markdown files.
Loads .md files from the data directory without heavy dependencies.
Qué hace este documento? 
Utiliza langchain para leer los archivos .md de la carpeta data/.
Divide los documentos largos en fragmentos más pequeños (chunks).
"""
import os
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.documents import Document

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data"
METADATA_PATH = BASE_DIR / "chroma_db" / "documents_metadata.json"


def calculate_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of a file to detect changes."""
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def load_metadata() -> Dict[str, str]:
    """Load stored metadata with file hashes."""
    if METADATA_PATH.exists():
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_metadata(metadata: Dict[str, str]) -> None:
    """Save metadata with file hashes."""
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def extract_insurance_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from file path structure.
    Example: data/seguro_coche/Todo_Riesgo/documento.md
    -> insurance_type: "coche", product: "Todo_Riesgo"
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


def load_markdown_documents(force_reload: bool = False) -> tuple[List[Document], bool]:
    """
    Load all markdown documents from the data directory.
    
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
        print("⚠️  No se encontraron archivos .md en el directorio data/")
        return [], False
    
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
            
        except Exception as e:
            print(f"❌ Error loading {md_file}: {e}")
    
    # Check for deleted files
    for old_key in stored_hashes:
        if old_key not in current_hashes:
            has_changes = True
            break
    
    # Save new metadata
    save_metadata(current_hashes)
    
    print(f"📄 Loaded {len(documents)} documents from {DATA_PATH}")
    
    return documents, has_changes


def get_documents_by_insurance_type(insurance_type: str) -> List[Document]:
    """
    Load documents filtered by insurance type.
    Useful for targeted searches.
    """
    all_docs, _ = load_markdown_documents()
    return [
        doc for doc in all_docs 
        if doc.metadata.get("insurance_type") == insurance_type
    ]
