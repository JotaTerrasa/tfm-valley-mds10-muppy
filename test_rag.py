from app.rag_engine import search_knowledge

# Simulamos una pregunta de un cliente
pregunta = "¿Qué coberturas tiene el seguro de moto líder?"

print(f"Buscando: {pregunta}...")
respuesta = search_knowledge(pregunta)

if respuesta:
    print("--- INFORMACIÓN ENCONTRADA ---")
    print(respuesta)
else:
    print("No se encontró información. Revisa si los archivos .md están en la carpeta data.")