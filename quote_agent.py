import os
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

# --- 1. CONFIGURACIÓN ---
# Cargar variables de entorno (asegúrate de tener tu .env con GOOGLE_API_KEY)
from dotenv import load_dotenv
load_dotenv()

# Configurar modelo de Embeddings (el mismo que usaste para crear la DB)
embedding_function = OllamaEmbeddings(model="mxbai-embed-large")

# Conectar con la base de datos que ya existe
db = Chroma(
    persist_directory="./chroma_db", 
    embedding_function=embedding_function
)

# --- 2. DEFINICIÓN DE HERRAMIENTAS (TOOLS) ---

@tool
def consultar_seguros(pregunta: str) -> str:
    """
    Usa esta herramienta para consultar condiciones, coberturas y detalles 
    de los seguros de Mapfre (Coche, Hogar, etc).
    Input: Una pregunta específica sobre el seguro.
    """
    # Busca los 3 fragmentos más relevantes en los PDFs
    docs = db.similarity_search(pregunta, k=3)
    
    # Devuelve el texto encontrado para que Gemini lo lea
    contexto = "\n\n".join([d.page_content for d in docs])
    return f"Información encontrada en los manuales:\n{contexto}"

@tool
def calcular_precio(tipo_seguro: str, edad: int, valor: float) -> str:
    """
    Calcula un presupuesto estimado.
    Input:
    - tipo_seguro: 'coche', 'hogar' o 'salud'.
    - edad: edad del cliente.
    - valor: valor del coche o casa (0 si es salud).
    """
    base = 200
    if tipo_seguro.lower() == "coche":
        precio = base + (valor * 0.02)
        if edad < 25: precio += 100 # Recargo joven
    elif tipo_seguro.lower() == "hogar":
        precio = 150 + (valor * 0.001)
    else:
        precio = 50 * 12 # Salud anual
    
    return f"El precio estimado para {tipo_seguro} es: {precio:.2f}€ anuales."

# Lista de herramientas
tools = [consultar_seguros, calcular_precio]

# --- 3. CREACIÓN DEL AGENTE ---

# Usamos Gemini Pro
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest")
# Creamos el grafo del agente (ReAct)
agent_executor = create_react_agent(llm, tools)

# --- 4. PRUEBA RÁPIDA (SOLO SI SE EJECUTA ESTE ARCHIVO) ---
if __name__ == "__main__":
    print("💬 Preguntando al agente...")
    query = "Hola, tengo 20 años y un coche que vale 10000 euros. ¿Qué cubre el seguro de terceros y cuánto me costaría?"
    
    response = agent_executor.invoke({"messages": [HumanMessage(content=query)]})
    
    print("\n🤖 RESPUESTA DEL AGENTE:")
    print(response["messages"][-1].content)