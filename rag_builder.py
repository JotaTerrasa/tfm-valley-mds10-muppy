import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma

# 1. CONFIGURACIÓN
# Carpeta donde están tus PDFs (veo en tu foto que se llama 'data')
DATA_PATH = "./data"
# Carpeta donde se guardará la "memoria" del robot
CHROMA_PATH = "./chroma_db"
# El modelo que te bajaste en Ollama
EMBEDDING_MODEL = "mxbai-embed-large"

def main():
    print(f"🔍 Buscando PDFs en {DATA_PATH} y subcarpetas...")
    
    # 2. CARGAR PDFs (recursivamente)
    documents = []
    # Recorremos todas las carpetas dentro de data
    for root, dirs, files in os.walk(DATA_PATH):
        for file in files:
            if file.endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                print(f"   📄 Cargando: {file}")
                try:
                    loader = PyPDFLoader(pdf_path)
                    documents.extend(loader.load())
                except Exception as e:
                    print(f"   ❌ Error cargando {file}: {e}")

    if not documents:
        print("⚠️ No he encontrado ningún PDF. Revisa la ruta.")
        return

    print(f"✅ Cargadas {len(documents)} páginas en total.")

    # 3. TROCEAR EL TEXTO (Chunking)
    # Partimos el texto en trozos de 1000 letras con un poco de solapamiento
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"🧩 Dividido en {len(chunks)} trozos de información.")

    # 4. GUARDAR EN CHROMA (Embeddings)
    print("💾 Guardando en base de datos vectorial (esto tardará un poco)...")
    
    # Borrar la DB anterior si existe para empezar de cero (opcional)
    if os.path.exists(CHROMA_PATH):
        import shutil
        shutil.rmtree(CHROMA_PATH)

    db = Chroma.from_documents(
        documents=chunks, 
        embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
        persist_directory=CHROMA_PATH
    )
    
    print("🎉 ¡ÉXITO! Base de datos creada en './chroma_db'")

if __name__ == "__main__":
    main()