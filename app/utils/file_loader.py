import re
import os

# Importación opcional de Google Cloud Storage
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    storage = None

def load_file_content(path: str) -> str:
    """Carga el contenido de un fichero desde una ruta local o GCS."""
    
    print(f"--- [File Loader] Cargando fichero desde: {path} ---")

    if path.startswith("gs://"):
        if not GCS_AVAILABLE:
            raise ImportError("Google Cloud Storage no está disponible. Instala google-cloud-storage.")
        try:
            from google.cloud import storage
            client = storage.Client()
            match = re.match(r"gs://([^/]+)/(.+)", path)
            if not match:
                raise ValueError("Ruta GCS inválida.")
            bucket_name, blob_name = match.groups()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            return blob.download_as_text(encoding="utf-8")
        except Exception as e:
            print(f"--- ERROR: No se pudo cargar desde GCS: {e} ---")
            raise
    else:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
