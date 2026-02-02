from typing import List, Optional, Literal, TypedDict
from langgraph.graph import StateGraph, START, END

class Ruta(TypedDict):
    destino: Literal[
        "quote_agent",
        "contract_agent",
        "support_agent",
        "clarification"
    ]
    confidence: float

class Estado(TypedDict):
    mensajes: List[str]
    destino: Optional[Ruta]
    respuesta: Optional[str]

# Nodos simulados
async def nodo_triaje(estado: Estado, config=None):
    msg = estado["mensajes"][-1].lower()
    if any(x in msg for x in ["cotización", "precio", "cotizar"]):
        return {"destino": {"destino": "quote_agent", "confidence": 0.9}}
    elif any(x in msg for x in ["contratar", "alta", "contratación"]):
        return {"destino": {"destino": "contract_agent", "confidence": 0.85}}
    elif any(x in msg for x in ["problema", "accidente", "siniestro"]):
        return {"destino": {"destino": "support_agent", "confidence": 0.95}}
    else:
        return {"destino": {"destino": "clarification", "confidence": 0.3}}

async def nodo_aclaracion(estado: Estado, config=None):
    return {"respuesta": "Para ayudarte mejor:\n1️⃣ Cotizar\n2️⃣ Contratar\n3️⃣ Soporte"}

async def nodo_quote(estado: Estado, config=None):
    return {"respuesta": "Perfecto 👍 Te paso con el agente de cotización."}

async def nodo_contract(estado: Estado, config=None):
    return {"respuesta": "Genial 👍 Te paso con el agente de contratación."}

async def nodo_support(estado: Estado, config=None):
    return {"respuesta": "De acuerdo 👍 Te paso con el agente de soporte."}

def elegir_ruta(estado: Estado) -> str:
    destino = estado["destino"]["destino"]
    confidence = estado["destino"]["confidence"]
    return "clarification" if destino == "clarification" or confidence < 0.6 else destino

def build_graph():
    grafo = StateGraph(Estado)
    grafo.add_node("triaje", nodo_triaje)
    grafo.add_node("clarification", nodo_aclaracion)
    grafo.add_node("quote_agent", nodo_quote)
    grafo.add_node("contract_agent", nodo_contract)
    grafo.add_node("support_agent", nodo_support)

    grafo.add_edge(START, "triaje")
    grafo.add_conditional_edges(
        "triaje",
        elegir_ruta,
        {
            "clarification": "clarification",
            "quote_agent": "quote_agent",
            "contract_agent": "contract_agent",
            "support_agent": "support_agent",
        }
    )

    grafo.add_edge("clarification", "triaje")  # LOOP
    grafo.add_edge("quote_agent", END)
    grafo.add_edge("contract_agent", END)
    grafo.add_edge("support_agent", END)

    return grafo.compile()