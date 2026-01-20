# 🏗️ Arquitectura del Sistema de Agentes de Seguros - Mapfre

## Diagrama de Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            USUARIO FINAL                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                               │
│  │  WhatsApp   │  │    API      │  │  Web App   │                               │
│  │ Messages    │  │  REST       │  │  (Future)  │                               │
│  └──────┬──────┘  └──────┬──────┘  └────────────┘                               │
└─────────┼─────────────────┼──────────────────────────────────────────────────────┘
          │                 │
          └─────────────────┼──────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────────────────────────┐
│                           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                          CAPA DE API                                        │  │
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │  │
│  │  │   /invoke           │  │   /health           │  │   /webhooks/*       │  │  │
│  │  │   Endpoint          │  │   Health Check      │  │   Payment Handler   │  │  │
│  │  └─────────┬───────────┘  └─────────┬──────────┘  └─────────┬──────────┘  │  │
│  │            │                        │                        │             │  │
│  └────────────┼────────────────────────┼────────────────────────┼─────────────┘  │
│               │                        │                        │                │
│               └────────────────────────┼────────────────────────┼────────────────┘
│                                        │                        │
│                                        └────────────────────────┼────────────────┘
│                                                                 │
│  ┌──────────────────────────────────────────────────────────────┼────────────────┐
│  │                                                              ▼                │
│  │                       CAPA DE ORQUESTACIÓN                                      │
│  │  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │  │                        AgentOrchestrator                                  │ │
│  │  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐    │ │
│  │  │  │  Load Config    │  │  LLM Factory    │  │   Strategy Selection     │    │ │
│  │  │  │                 │  │  (Cache)        │  │                         │    │ │
│  │  │  └──────┬──────────┘  └──────┬──────────┘  └─────────┬───────────────┘    │ │
│  │  │         │                     │                      │                    │ │
│  │  └─────────┼─────────────────────┼──────────────────────┼────────────────────┘ │
│               │                     │                      │                       │
│               └─────────────────────┼──────────────────────┼──────────────────────┘
│                                     │                      │
│  ┌──────────────────────────────────┼──────────────────────┼──────────────────────┐
│  │                                  ▼                      ▼                       │
│  │                        CAPA DE ESTRATEGIAS                                    │
│  │  ┌─────────────────────────────┐  ┌─────────────────────────────────────────┐  │
│  │  │     GenerativeStrategy       │  │          StateMachineStrategy          │  │
│  │  │  ┌─────────────────────────┐ │  │  ┌─────────────────┐ ┌─────────────┐   │  │
│  │  │  │   Prompt + LLM + Tools   │ │  │  │   Router       │ │   Nodes     │   │  │
│  │  │  │                         │ │  │  │                 │ │             │   │  │
│  │  │  └─────────┬───────────────┘ │  │  └─────┬───────────┘ └─────┬───────┘   │  │
│  │  │           │                 │  │        │                   │           │  │
│  │  └───────────┼─────────────────┘  │        │                   │           │  │
│                  │                    │        └───────────────────┼───────────┘  │
│                  └────────────────────┼────────────────────────────┼──────────────┘
│                                       │                            │
│  ┌────────────────────────────────────┼────────────────────────────┼──────────────┐
│  │                                    ▼                            ▼               │
│  │                          CAPA DE MEMORIA                     CAPA DE HERRAMIENTAS │
│  │  ┌─────────────────────────────┐  ┌─────────────────────────────────────────┐  │
│  │  │      Memory Factory         │  │           TOOLS REGISTRY                │  │
│  │  │  ┌─────────────────────────┐ │  │  ┌─────────────┐ ┌─────────────┐ ┌─────┐ │  │
│  │  │  │  Buffer Window Memory   │ │  │  │ Insurance   │ │ Payment     │ │ Save│ │  │
│  │  │  │                         │ │  │  │ Products    │ │ Tools       │ │Lead │ │  │
│  │  │  └─────────────────────────┘ │  │  └─────┬───────┘ └─────┬──────┘ └─────┘ │  │
│  │  │                              │  │        │               │                │  │
│  │  │  ┌─────────────────────────┐  │  │        │               │                │  │
│  │  │  │  Entity Memory          │  │  │        └───────────────┼────────────────┘  │  │
│  │  │  │                         │  │  │                        │                  │  │
│  │  │  └─────────────────────────┘  │  │                        │                  │  │
│  │                                  │  │                        ▼                  │  │
│  └──────────────────────────────────┼──┼────────────────────────────────────────────┘  │
│                                     │  │
│                                     │  │
│  ┌──────────────────────────────────┼──┼─────────────────────────────────────────────┐  │
│  │                                  ▼  ▼                                             │  │
│  │                        SISTEMAS EXTERNOS                                         │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │  │
│  │  │   Stripe    │ │  BigQuery   │ │   Redis     │ │   WhatsApp │  │  │
│  │  │  Payments   │ │  Data Lake  │ │   Cache     │ │   API      │  │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘  │  │
│  │                                                                                   │  │
│  └───────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                           CAPA DE CONFIGURACIÓN                                    │  │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │  │
│  │  │  Triage Agent   │ │  Quote Agent    │ │ Contract Agent  │ │ Support Agent   │  │  │
│  │  │  config.json    │ │  config.json    │ │  config.json    │ │  config.json    │  │  │
│  │  └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘  │  │
│  │                                                                                   │  │
│  └───────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                         │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

## Flujo de Datos en el Sistema

### 1. **Entrada del Usuario**
```
Usuario → API REST → Capa de API → AgentOrchestrator
```

### 2. **Procesamiento del Agente**
```
Config JSON → Memory Factory → Strategy Selection → LLM + Tools → Response
```

### 3. **Persistencia y Estado**
```
Response → Redis (Session State) → BigQuery (Leads) → Stripe (Payments)
```

## Tipos de Agentes y Sus Flujos

### **🔄 Triage Agent** (Clasificación)
```
Mensaje Usuario → Triage → Quote/Contract/Support Agent
```

### **💰 Quote Agent** (Cotización)
```
Greet → Identify Insurance Type → Get Products → Calculate Quote → Present Options
```

### **📝 Contract Agent** (Contratación)
```
Data Capture → Verification → Payment → Final Summary
```

### **🆘 Support Agent** (Atención al Cliente)
```
Query → Understand Issue → Provide Solution / Escalate
```

## Componentes Clave por Capa

### **Config Layer**
- `agent_role`: Identidad del agente
- `strategy`: Tipo de estrategia (generative/state_machine)
- `memory`: Configuración de memoria
- `llm_configurations`: Modelos y proveedores
- `state_machine`: Definición de estados (para state_machine strategy)

### **Strategy Layer**
- **GenerativeStrategy**: Prompt único + validación post-hoc
- **StateMachineStrategy**: Router + múltiples nodos especializados

### **Tools Layer**
- **Insurance Products**: Consulta de productos de seguros disponibles
- **Payment Tools**: Creación de links de pago
- **Quote Calculation**: Cálculo de cotizaciones
- **Persistence Tools**: Guardado de leads en BigQuery

## Beneficios Arquitectónicos

✅ **Modularidad**: Cada capa tiene responsabilidad única
✅ **Escalabilidad**: Cache de LLM y orquestadores
✅ **Extensibilidad**: Nuevos agentes = nuevos JSON
✅ **Resiliencia**: Fallbacks y validación de respuestas
✅ **Multi-tenancy**: Múltiples agentes especializados

## Diferencias con el Sistema Original

### Adaptaciones para Seguros:
1. **Schemas**: Adaptados para datos de seguros (vehículos, propiedades, etc.)
2. **Tools**: Herramientas específicas de seguros (cotizaciones, productos)
3. **Agents**: Especializados en flujos de seguros
4. **Prompts**: Contexto de seguros y productos Mapfre

### Mantenido del Original:
1. **Arquitectura modular**: Misma estructura de capas
2. **Sistema de estrategias**: Generative y State Machine
3. **Gestión de memoria**: Redis-based
4. **Configuración JSON**: Agentes definidos por configuración
