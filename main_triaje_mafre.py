import os
from typing import Annotated, Literal, TypedDict, Optional
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

# --- CONFIGURACIÓN ---
load_dotenv()
# Temperatura 0 es vital para que respete estrictamente  JSON
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# --- ESQUEMA DE SALIDA 
class TriageOutput(BaseModel):
    route: Literal["cotizar", "contratar", "soporte", "triage"]
    intent: str
    next_agent: Literal["quote_agent", "contract_agent", "support_agent", "null"]
    status: str
    reply: str = Field(description="La respuesta amable y natural al usuario antes del JSON")

# --- ESTADO DEL AGENTE ---
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    next_step: str

# --- NODO DE TRIAJE  ---
async def triage_node(state: AgentState):
    # Guardián contra inicio vacío
    if not state.get("messages"):
        return {"messages": [AIMessage(content="¡Hola! Bienvenido a Mapfre. ¿En qué puedo ayudarte hoy?")]}

    # TU PROMPT EXACTO AQUÍ
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres un agente de triaje especializado en seguros de Mapfre. Tu función es clasificar la intención del usuario y dirigirlo al agente apropiado.

        ## Prioridad (MÁXIMA - URGENTE):
        - **soporte**: Si detectas urgencia, accidente, siniestro o asistencia inmediata → SIEMPRE asigna a support_agent.
          Palabras clave: grúa, choque, siniestro, asistencia, accidente, avería, rotura, pinchazo, batería, emergencia, urgencia, no arranca.

        ## Tu función:
        1. Analiza el mensaje del usuario (y el contexto de la conversación si existe).
        2. Identifica su intención principal:
           - **soporte**: Consulta sobre seguro existente, problema, siniestro, asistencia en carretera, urgencia.
           - **cotizar**: Información sobre precios, presupuestos, tarifas, coberturas.
             Palabras clave: precio, cuánto vale, presupuesto, tarifas, cotización, cuánto cuesta, comparar precios.
           - **contratar**: Contratar, dar de alta, renovar, firmar póliza.
             Palabras clave: contratar, dar de alta, firmar póliza, contrato, nueva póliza, renovar, suscripción.
           - **triage**: Si no está claro, es un saludo genérico sin contexto o no tiene relación con seguros → continúa en triage (no envíes next_agent o usa null).

        3. Responde de forma amable y profesional.
        4. Si identificas claramente la intención, incluye en tu respuesta JSON el campo "next_agent" con el valor correspondiente:
           - "support_agent" para soporte / urgencias
           - "quote_agent" para cotizar
           - "contract_agent" para contratar

        ## Formato de respuesta:
        Responde al usuario de forma natural y amable (esto irá en el campo 'reply'). El sistema generará el JSON automáticamente basado en tu decisión.
        """),
        ("placeholder", "{messages}"),
    ])
    
    # Usamos salida estructurada para garantizar que el JSON sea válido siempre
    router = prompt | llm.with_structured_output(TriageOutput)
    result = await router.ainvoke({"messages": state["messages"]})
    
    
    # Nota: He convertido "null" string a null real de JSON para la visualización si es necesario
    agent_display = result.next_agent if result.next_agent != "null" else "null"
    
    json_block = f"""
```json
{{
  "route": "{result.route}",
  "intent": "{result.intent}",
  "next_agent": "{agent_display}",
  "status": "{result.status}"
}}
```"""
    
    full_response = f"{result.reply}\n{json_block}"
    
    # Determinamos el siguiente paso real para el grafo
    real_next_step = result.next_agent if result.next_agent != "null" else "triage"
    
    return {
        "messages": [AIMessage(content=full_response)],
        "next_step": real_next_step
    }

# --- NODOS ESPECIALISTAS  ---
async def specialist_node(state: AgentState):
    agent = state.get("next_step", "general")
    # Mensaje de sistema para confirmar la transferencia en el chat
    return {"messages": [AIMessage(content=f"🔄 [SISTEMA] Transfiriendo conversación a: {agent.upper()}")]}

# --- LÓGICA DE RUTEO ---
def route_decision(state: AgentState):
    target = state.get("next_step", "triage")
    # Si el target es uno de los agentes válidos, vamos ahí
    if target in ["quote_agent", "contract_agent", "support_agent"]:
        return target
    # Si es triage (o null), terminamos el turno para esperar que el usuario hable de nuevo
    return END

# --- CONSTRUCCIÓN DEL GRAFO ---
workflow = StateGraph(AgentState)

workflow.add_node("triage", triage_node)
workflow.add_node("quote_agent", specialist_node)
workflow.add_node("contract_agent", specialist_node)
workflow.add_node("support_agent", specialist_node)

workflow.add_edge(START, "triage")

workflow.add_conditional_edges(
    "triage",
    route_decision,
    {
        "quote_agent": "quote_agent",
        "contract_agent": "contract_agent",
        "support_agent": "support_agent",
        END: END
    }
)

workflow.add_edge("quote_agent", END)
workflow.add_edge("contract_agent", END)
workflow.add_edge("support_agent", END)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)