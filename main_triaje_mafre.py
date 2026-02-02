# main_triaje_mafre.py
# Agente de Triaje para MAPFRE - Versión Mejorada

import os
import asyncio
import logging
from typing import Literal, TypedDict, Annotated, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# ======================================================
# Configuración de Logging
# ======================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ======================================================
# 1. Configuración de Entorno
# ======================================================
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# MEJORA: Validación de API key
if not api_key:
    raise ValueError("OPENAI_API_KEY no encontrada en las variables de entorno")

# MEJORA: Configuración más flexible del LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0,
    api_key=api_key,
    timeout=30  # Timeout para evitar esperas infinitas
)

# ======================================================
# 2. Definición del Estado y Memoria
# ======================================================
class DecisionTriaje(TypedDict):
    intencion: Literal["quote_agent", "contract_agent", "support_agent", "clarification"]
    confianza: float
    razonamiento: str

class EstadoAgente(TypedDict):
    messages: Annotated[list, add_messages]
    decision: DecisionTriaje
    respuesta_final: str

# MEJORA: Memoria con límite para evitar crecimiento infinito
MEMORIA_USUARIOS = {}  # {user_id: [messages]}
MAX_MEMORIA_MENSAJES = 50  # Límite de mensajes por usuario

# ======================================================
# 3. Nodo de Triaje MAPFRE - MEJORADO
# ======================================================
async def nodo_triaje(estado: EstadoAgente, config: RunnableConfig):
    """
    Nodo de triaje mejorado con prompt más específico para MAPFRE
    y mejor manejo de errores.
    """
    try:
        # MEJORA: Prompt más detallado y específico para MAPFRE
        prompt_triaje = ChatPromptTemplate.from_messages([
            ("system", """Eres el experto en triaje de MAPFRE, una de las principales aseguradoras de España.
Tu misión es clasificar la intención del usuario y dirigirlo al agente especializado correcto.

AGENTES DISPONIBLES:
1. **support_agent** (MÁXIMA PRIORIDAD - URGENTE):
   - Asistencia inmediata: grúa, accidente, siniestro, avería, rotura de lunas
   - Emergencias en carretera, asistencia 24h
   - Palabras clave: "grúa", "choque", "siniestro", "asistencia", "accidente", "avería", 
     "rotura", "pinchazo", "batería", "emergencia", "urgencia", "no arranca"

2. **quote_agent** (Cotizaciones):
   - Consultas de precios, presupuestos, tarifas
   - Comparativas, información de coberturas y precios
   - Palabras clave: "precio", "cuánto vale", "presupuesto", "tarifas", "cotización", 
     "cuánto cuesta", "precio del seguro", "comparar precios"

3. **contract_agent** (Contratación):
   - Proceso de contratación, alta de póliza, renovación
   - Información sobre contratación, documentos necesarios
   - Palabras clave: "contratar", "dar de alta", "firmar póliza", "contrato", 
     "nueva póliza", "renovar", "suscripción"

4. **clarification** (Aclaración):
   - Solo si el mensaje NO tiene relación con seguros o servicios de MAPFRE
   - Saludos genéricos sin contexto, preguntas fuera de tema

REGLAS IMPORTANTES:
- Si detectas URGENCIA o ACCIDENTE, SIEMPRE asigna a support_agent (confianza alta)
- Analiza el contexto completo de la conversación, no solo el último mensaje
- Si hay ambigüedad, usa el historial de mensajes para decidir
- La confianza debe reflejar tu certeza: 0.0-1.0 (1.0 = muy seguro)

Responde con la estructura JSON requerida."""),
            ("placeholder", "{messages}"),
        ])

        router = prompt_triaje | llm.with_structured_output(DecisionTriaje)
        resultado = await router.ainvoke({"messages": estado["messages"]}, config)
        
        # MEJORA: Validación de la decisión
        if resultado["confianza"] < 0 or resultado["confianza"] > 1:
            logger.warning(f"Confianza fuera de rango: {resultado['confianza']}, ajustando a 0.5")
            resultado["confianza"] = 0.5
        
        logger.info(f"Triaje: {resultado['intencion']} (confianza: {resultado['confianza']:.2f})")
        return {"decision": resultado}
    
    except Exception as e:
        logger.error(f"Error en nodo_triaje: {e}")
        # MEJORA: Fallback seguro en caso de error
        return {
            "decision": {
                "intencion": "clarification",
                "confianza": 0.0,
                "razonamiento": f"Error en el triaje: {str(e)}"
            }
        }

# ======================================================
# 4. Nodo Especialista - MEJORADO
# ======================================================
async def ejecutar_agente_especialista(rol: str, estado: EstadoAgente, config: RunnableConfig):
    """
    Ejecuta el agente especialista con mejor manejo de contexto
    y prompts más específicos para cada rol.
    """
    try:
        # MEJORA: Extracción más robusta del mensaje del usuario
        if not estado.get("messages") or len(estado["messages"]) == 0:
            texto_usuario = "El usuario acaba de iniciar conversación."
        else:
            ultimo_mensaje = estado["messages"][-1]
            # MEJORA: Manejo de diferentes tipos de mensajes
            if hasattr(ultimo_mensaje, 'content'):
                texto_usuario = ultimo_mensaje.content
            elif isinstance(ultimo_mensaje, dict):
                texto_usuario = ultimo_mensaje.get("content", str(ultimo_mensaje))
            else:
                texto_usuario = str(ultimo_mensaje)

        # MEJORA: Prompts más específicos por rol
        prompts_especializados = {
            "Cotizaciones y Precios": """Eres un experto de MAPFRE especializado en Cotizaciones y Precios.
Tu función es ayudar a los clientes a:
- Obtener información sobre precios de seguros
- Comparar diferentes opciones y coberturas
- Explicar factores que influyen en el precio
- Proporcionar presupuestos personalizados

Responde de forma clara, profesional y amigable. Si no tienes información específica de precios,
ofrece contactar con un asesor o proporcionar información general sobre cómo se calculan las primas.""",

            "Contratación de Pólizas": """Eres un experto de MAPFRE especializado en Contratación de Pólizas.
Tu función es ayudar a los clientes a:
- Entender el proceso de contratación
- Conocer los documentos necesarios
- Explicar los pasos para dar de alta una póliza
- Resolver dudas sobre el proceso de suscripción

Responde de forma clara, profesional y amigable. Guía al cliente paso a paso en el proceso.""",

            "Asistencia Inmediata y Siniestros": """Eres un experto de MAPFRE especializado en Asistencia Inmediata y Siniestros.
Tu función es ayudar a los clientes en situaciones urgentes:
- Coordinar asistencia en carretera (grúa, mecánico, etc.)
- Gestionar siniestros y accidentes
- Proporcionar información sobre coberturas de asistencia
- Guiar en el proceso de reclamación

IMPORTANTE: Si es una emergencia real, proporciona números de contacto de emergencia de MAPFRE.
Responde de forma clara, profesional, empática y eficiente. La rapidez es crucial."""
        }

        prompt_texto = prompts_especializados.get(
            rol, 
            f"Eres un experto de MAPFRE en {rol}. Responde de forma clara, profesional y amigable."
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_texto),
            ("human", "{texto}")
        ])

        cadena = prompt | llm | StrOutputParser()
        respuesta = await cadena.ainvoke({"texto": texto_usuario}, config)
        
        logger.info(f"Agente {rol} respondió correctamente")
        return {"respuesta_final": respuesta, "messages": [AIMessage(content=respuesta)]}
    
    except Exception as e:
        logger.error(f"Error en ejecutar_agente_especialista ({rol}): {e}")
        mensaje_error = f"Lo siento, ha ocurrido un error al procesar tu solicitud. Por favor, intenta de nuevo o contacta con atención al cliente de MAPFRE."
        return {"respuesta_final": mensaje_error, "messages": [AIMessage(content=mensaje_error)]}

# ======================================================
# 5. Nodos concretos
# ======================================================
async def nodo_quote(estado: EstadoAgente, config: RunnableConfig):
    return await ejecutar_agente_especialista("Cotizaciones y Precios", estado, config)

async def nodo_contract(estado: EstadoAgente, config: RunnableConfig):
    return await ejecutar_agente_especialista("Contratación de Pólizas", estado, config)

async def nodo_support(estado: EstadoAgente, config: RunnableConfig):
    return await ejecutar_agente_especialista("Asistencia Inmediata y Siniestros", estado, config)

# MEJORA: Nodo de aclaración más completo y con config
async def nodo_aclaracion(estado: EstadoAgente, config: Optional[RunnableConfig] = None):
    """
    Nodo de aclaración mejorado que proporciona opciones claras al usuario.
    """
    mensaje = """¡Hola! Bienvenido a MAPFRE. Soy tu asistente virtual y estoy aquí para ayudarte.

¿En qué puedo asistirte hoy?

🔧 **Asistencia y Emergencias**: Si necesitas una grúa, has tenido un accidente o necesitas asistencia inmediata
💰 **Cotizaciones**: Si quieres conocer precios o solicitar un presupuesto
📋 **Contratación**: Si deseas contratar o renovar una póliza

Por favor, indícame cómo puedo ayudarte y te dirigiré al especialista adecuado."""
    
    return {
        "respuesta_final": mensaje,
        "messages": [AIMessage(content=mensaje)]
    }

# ======================================================
# 6. Enrutador - MEJORADO
# ======================================================
def enrutador(estado: EstadoAgente) -> str:
    """
    Enrutador mejorado con validación y logging.
    """
    try:
        decision = estado.get("decision", {})
        
        # MEJORA: Validación de la decisión
        if not decision or "intencion" not in decision:
            logger.warning("Decisión inválida, redirigiendo a clarification")
            return "clarification"
        
        confianza = decision.get("confianza", 0.0)
        intencion = decision.get("intencion", "clarification")
        
        # MEJORA: Umbral de confianza ajustable
        UMBRAL_CONFIANZA = 0.3
        
        if confianza < UMBRAL_CONFIANZA:
            logger.info(f"Confianza baja ({confianza:.2f}), redirigiendo a clarification")
            return "clarification"
        
        logger.info(f"Enrutando a: {intencion} (confianza: {confianza:.2f})")
        return intencion
    
    except Exception as e:
        logger.error(f"Error en enrutador: {e}")
        return "clarification"

# ======================================================
# 7. Grafo del Agente
# ======================================================
workflow = StateGraph(EstadoAgente)

workflow.add_node("triaje", nodo_triaje)
workflow.add_node("quote_agent", nodo_quote)
workflow.add_node("contract_agent", nodo_contract)
workflow.add_node("support_agent", nodo_support)
workflow.add_node("clarification", nodo_aclaracion)

workflow.add_edge(START, "triaje")

workflow.add_conditional_edges(
    "triaje",
    enrutador,
    {
        "clarification": "clarification",
        "quote_agent": "quote_agent",
        "contract_agent": "contract_agent",
        "support_agent": "support_agent",
    }
)

workflow.add_edge("quote_agent", END)
workflow.add_edge("contract_agent", END)
workflow.add_edge("support_agent", END)
workflow.add_edge("clarification", END)

app = workflow.compile()

# ======================================================
# 8. Función de Interacción con Memoria - MEJORADA
# ======================================================
def limpiar_memoria(user_id: str):
    """
    Limpia la memoria del usuario si excede el límite máximo.
    Mantiene solo los últimos MAX_MEMORIA_MENSAJES mensajes.
    """
    if user_id in MEMORIA_USUARIOS:
        mensajes = MEMORIA_USUARIOS[user_id]
        if len(mensajes) > MAX_MEMORIA_MENSAJES:
            # Mantener solo los últimos mensajes
            MEMORIA_USUARIOS[user_id] = mensajes[-MAX_MEMORIA_MENSAJES:]
            logger.info(f"Memoria limpiada para usuario {user_id}")

async def interactuar(user_id: str, mensaje_usuario: str) -> str:
    """
    Función principal de interacción mejorada con mejor manejo de memoria
    y tipos de mensaje correctos.
    """
    try:
        # MEJORA: Validación de entrada
        if not user_id or not mensaje_usuario:
            raise ValueError("user_id y mensaje_usuario son requeridos")
        
        # MEJORA: Inicialización de memoria si no existe
        if user_id not in MEMORIA_USUARIOS:
            MEMORIA_USUARIOS[user_id] = []
            logger.info(f"Nueva sesión iniciada para usuario: {user_id}")
        
        # MEJORA: Uso de HumanMessage en lugar de dict
        mensaje = HumanMessage(content=mensaje_usuario)
        MEMORIA_USUARIOS[user_id].append(mensaje)
        
        # MEJORA: Limpieza de memoria si es necesario
        limpiar_memoria(user_id)
        
        estado_inicial = EstadoAgente(
            messages=MEMORIA_USUARIOS[user_id],
            decision={
                "intencion": "clarification",
                "confianza": 0.0,
                "razonamiento": ""
            },
            respuesta_final=""
        )

        resultado = await app.ainvoke(estado_inicial, RunnableConfig())
        
        # MEJORA: Guardar respuesta correctamente en memoria
        respuesta_final = resultado.get("respuesta_final", "")
        if respuesta_final:
            # Asegurar que los mensajes se guardan correctamente
            mensajes_respuesta = resultado.get("messages", [])
            if mensajes_respuesta:
                # Si ya son AIMessage, agregarlos directamente
                if isinstance(mensajes_respuesta[0], AIMessage):
                    MEMORIA_USUARIOS[user_id].extend(mensajes_respuesta)
                else:
                    # Si son strings, convertirlos a AIMessage
                    for msg in mensajes_respuesta:
                        if isinstance(msg, str):
                            MEMORIA_USUARIOS[user_id].append(AIMessage(content=msg))
                        else:
                            MEMORIA_USUARIOS[user_id].append(AIMessage(content=str(msg)))
        
        logger.info(f"Interacción completada para usuario {user_id}")
        return respuesta_final
    
    except Exception as e:
        logger.error(f"Error en interactuar para usuario {user_id}: {e}")
        return "Lo siento, ha ocurrido un error. Por favor, intenta de nuevo o contacta con atención al cliente de MAPFRE."

# ======================================================
# 9. Ejemplo de uso
# ======================================================
if __name__ == "__main__":
    async def main():
        print("=== Agente de Triaje MAPFRE ===\n")
        
        # Ejemplo 1: Saludo inicial
        respuesta = await interactuar("usuario_123", "Hola, buenos días")
        print(f"Usuario: Hola, buenos días")
        print(f"Agente: {respuesta}\n")
        
        # Ejemplo 2: Consulta sobre seguros
        respuesta = await interactuar("usuario_123", "Quiero información sobre seguros de auto")
        print(f"Usuario: Quiero información sobre seguros de auto")
        print(f"Agente: {respuesta}\n")
        
        # Ejemplo 3: Emergencia
        respuesta = await interactuar("usuario_456", "Necesito una grúa, tuve un accidente")
        print(f"Usuario: Necesito una grúa, tuve un accidente")
        print(f"Agente: {respuesta}\n")

    asyncio.run(main())