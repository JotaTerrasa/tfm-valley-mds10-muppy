# Plataforma de Agentes de IA - Mapfre Seguros

Sistema multiagente conversacional para gestión de seguros, basado en LangGraph y FastAPI.

## 🏗️ Arquitectura

Este proyecto implementa una arquitectura modular de agentes conversacionales especializados en seguros, adaptada del sistema de ventas de telefonía móvil.

### Componentes Principales

- **Capa de API**: Endpoints REST para interacción
- **Capa de Orquestación**: Gestión de agentes y sesiones
- **Capa de Estrategias**: Generative y State Machine
- **Capa de Herramientas**: Funcionalidades específicas de seguros
- **Capa de Configuración**: Agentes definidos mediante JSON

## 🚀 Instalación

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Ejecutar servidor
uvicorn app.main:app --reload
```

## 📋 Variables de Entorno

```env
REDIS_URL=redis://localhost:6379
API_KEY_SECRET=tu_secret_key
PHONE_NUMBER_ID=tu_phone_number_id
WHATSAPP_ACCESS_TOKEN=tu_token
WHATSAPP_VERIFY_TOKEN=tu_verify_token
```

## 🤖 Agentes Disponibles

### 1. Triage Agent
Clasifica la intención del usuario y dirige al agente apropiado.

### 2. Quote Agent
Proporciona cotizaciones de seguros y muestra productos disponibles.

### 3. Contract Agent
Gestiona el proceso completo de contratación de seguros.

### 4. Support Agent
Atención al cliente para consultas sobre pólizas existentes.

## 📡 API Endpoints

### POST /invoke
Invocar un agente con un mensaje del usuario.

```json
{
  "input": "Hola, quiero información sobre seguros de auto",
  "session_id": "opcional-session-id",
  "metadata": {}
}
```

### GET /health
Verificar el estado del servicio.

## 🔧 Desarrollo

### Estructura del Proyecto

```
├── app/
│   ├── core/           # Componentes centrales
│   ├── strategies/     # Estrategias de agentes
│   ├── tools/          # Herramientas disponibles
│   ├── schemas/        # Esquemas de datos
│   └── handlers/       # Handlers de eventos
├── agents/             # Configuraciones de agentes
│   ├── triage_agent/
│   ├── quote_agent/
│   ├── contract_agent/
│   └── support_agent/
└── requirements.txt
```

### Agregar un Nuevo Agente

1. Crear directorio en `agents/nuevo_agente/`
2. Crear `config.json` con la configuración
3. Crear prompts necesarios
4. El sistema lo cargará automáticamente

## 📝 Notas

- Las herramientas en `app/tools/insurance_tools.py` son placeholders y deben ser implementadas según necesidades reales
- La persistencia en BigQuery debe ser configurada según el entorno de Mapfre
- Los prompts pueden ser ajustados según el tono y estilo de comunicación deseado

## 📄 Licencia

Ver archivo LICENSE
