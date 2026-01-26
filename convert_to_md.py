import fitz  # PyMuPDF
import os

def convert_pdfs_to_md(base_path):
    # Caminamos por todas las subcarpetas de /data
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                # Creamos el nombre del archivo .md en la misma ubicación
                md_path = os.path.join(root, file.replace(".pdf", ".md"))
                
                try:
                    doc = fitz.open(pdf_path)
                    text_content = [f"# Documento: {file}\n"]
                    
                    for i, page in enumerate(doc, start=1):
                        text_content.append(f"\n---\n## Página {i}\n")
                        text_content.append(page.get_text())
                    
                    doc.close()  # Buena práctica cerrar el documento
                    
                    with open(md_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(text_content))
                    
                    print(f"✅ Convertido: {pdf_path}")
                except Exception as e:
                    print(f"❌ Error convirtiendo {file}: {e}")

if __name__ == "__main__":
    # Ejecutamos apuntando a tu carpeta data
    convert_pdfs_to_md("data")