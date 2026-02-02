from typing import TypedDict, Literal

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig


# =========================
# 1️⃣ MODELO
# =========================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


# =========================
# 2️⃣ DEFINICIÓN DEL ESTADO
# =========================

class TriajeState(TypedDict):
    user_input: str
    intent: Literal["quote_agent", "contract_agent", "support_agent"]
    response: str


# =========================
# 3️⃣ PROMPT DE TRIAJE MAPFRE
# =========================

triaje_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
Eres un agente de triaje de MAPFRE Seguros.

Tu única tarea es clasificar la intención del usuario y devolver
EXACTAMENTE uno de los siguientes valores:

- quote_agent → si el usuario quiere cotizar o informarse sobre precios
- contract_agent → si el usuario quiere contratar un seguro
- support_agent → si el usuario necesita ayuda, soporte o gestión de un seguro existente

Responde SOLO con uno de esos valores.
No expliques nada.
"""
        ),
        ("human", "{user_input}")
    ]
)

triaje_chain = triaje_prompt | llm | StrOutputParser()


# =========================
# 4️⃣ NODOS
# =========================

async def triaje_node(state: TriajeState, config: RunnableConfig):
    intent = await triaje_chain.ainvoke(
        {"user_input": state["user_input"]},
        config
    )
    intent = intent.strip()

    return {"intent": intent}


async def quote_agent_node(state: TriajeState, config: RunnableConfig):
    return {
        "response": "🔎 Te ayudo a cotizar tu seguro en MAPFRE. ¿Qué tipo de seguro te interesa?"
    }


async def contract_agent_node(state: TriajeState, config: RunnableConfig):
    return {
        "response": "📝 Perfecto, vamos a iniciar el proceso de contratación de tu seguro MAPFRE."
    }


async def support_agent_node(state: TriajeState, config: RunnableConfig):
    return {
        "response": "🛠️ Estoy aquí para ayudarte con tu seguro MAPFRE. ¿Qué problema tienes?"
    }


# =========================
# 5️⃣ FUNCIÓN DE ROUTING
# =========================

def route_by_intent(state: TriajeState) -> Literal[
    "quote_agent", "contract_agent", "support_agent"
]:
    return state["intent"]


# =========================
# 6️⃣ CONSTRUCCIÓN DEL GRAFO
# =========================

graph = StateGraph(TriajeState)

graph.add_node("triaje", triaje_node)
graph.add_node("quote_agent", quote_agent_node)
graph.add_node("contract_agent", contract_agent_node)
graph.add_node("support_agent", support_agent_node)

graph.add_edge(START, "triaje")

graph.add_conditional_edges(
    "triaje",
    route_by_intent
)

graph.add_edge("quote_agent", END)
graph.add_edge("contract_agent", END)
graph.add_edge("support_agent", END)

app = graph.compile()