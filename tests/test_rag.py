"""
Test script for the RAG (Retrieval-Augmented Generation) system.

This script tests the search functionality of the insurance knowledge base.
Ejecutar desde la raíz del proyecto: python tests/test_rag.py
"""
import logging
from app.rag.vector_store import search_insurance_info, search_knowledge, get_vector_store

# Configurar logging para ver lo que hace el RAG
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def test_basic_search():
    """Test basic search functionality."""
    print("\n" + "=" * 60)
    print("TEST 1: Búsqueda básica")
    print("=" * 60)
    
    pregunta = "¿Qué coberturas tiene el seguro de moto líder?"
    print(f"\nPregunta: {pregunta}")
    print("-" * 40)
    
    respuesta = search_insurance_info(pregunta)
    
    if respuesta and "No se encontró" not in respuesta:
        print("✅ INFORMACIÓN ENCONTRADA:")
        print(respuesta[:1000])  # Mostrar solo primeros 1000 caracteres
    else:
        print("⚠️  No se encontró información.")


def test_filtered_search():
    """Test search with insurance type filter."""
    print("\n" + "=" * 60)
    print("TEST 2: Búsqueda filtrada por tipo de seguro")
    print("=" * 60)
    
    pregunta = "coberturas todo riesgo"
    tipo = "coche"
    print(f"\nPregunta: {pregunta}")
    print(f"Filtro: insurance_type = {tipo}")
    print("-" * 40)
    
    respuesta = search_insurance_info(pregunta, insurance_type=tipo)
    
    if respuesta and "No se encontró" not in respuesta:
        print("✅ INFORMACIÓN ENCONTRADA:")
        print(respuesta[:1000])
    else:
        print("⚠️  No se encontró información para este tipo de seguro.")


def test_stats():
    """Test vector store statistics."""
    print("\n" + "=" * 60)
    print("TEST 3: Estadísticas del Vector Store")
    print("=" * 60)
    
    store = get_vector_store()
    stats = store.get_collection_stats()
    
    print("\nEstadísticas:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")


if __name__ == "__main__":
    print("\n🧪 TESTS DEL SISTEMA RAG")
    print("=" * 60)
    
    # Ejecutar todos los tests
    test_stats()
    test_basic_search()
    test_filtered_search()
    
    print("\n" + "=" * 60)
    print("✅ Tests completados")
    print("=" * 60)
