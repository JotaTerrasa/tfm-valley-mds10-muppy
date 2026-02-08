"""
Convierte todos los PDFs dentro de data/ a Markdown (.md) en la misma ruta.
Requisito: PyMuPDF (pymupdf en requirements.txt).
Ejecutar desde la raíz del proyecto: python scripts/data/convert_to_md.py
"""
import os
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Instala PyMuPDF: pip install pymupdf", file=sys.stderr)
    sys.exit(2)


def convert_pdfs_to_md(base_path: str) -> None:
    for root, _dirs, files in os.walk(base_path):
        for file in files:
            if not file.lower().endswith(".pdf"):
                continue
            pdf_path = os.path.join(root, file)
            md_path = os.path.join(root, file[:-4] + ".md")
            try:
                doc = fitz.open(pdf_path)
                text_content = [f"# Documento: {file}\n"]
                for i, page in enumerate(doc, start=1):
                    text_content.append(f"\n---\n## Página {i}\n")
                    text_content.append(page.get_text())
                doc.close()
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(text_content))
                print(f"✅ Convertido: {pdf_path}")
            except Exception as e:
                print(f"❌ Error convirtiendo {file}: {e}", file=sys.stderr)


if __name__ == "__main__":
    # Ruta relativa a la raíz del proyecto (ejecutar desde la raíz)
    convert_pdfs_to_md("data")
