# 🤖 Sistema de Agentes Conversacionales - Mapfre Seguros

## 🎯 ¿Qué es este proyecto?

Este proyecto es un **sistema inteligente de chatbots especializados** para la gestión completa del ciclo de vida de seguros en Mapfre. Imagina tener varios asistentes virtuales especializados que pueden:

- **Atender consultas iniciales** y dirigirte al especialista correcto
- **Cotizar seguros** mostrando opciones personalizadas
- **Ayudarte a contratar** un seguro paso a paso
- **Resolver dudas** sobre pólizas existentes

El sistema está diseñado para ser **conversacional y natural**, como hablar con un asesor humano, pero con la ventaja de estar disponible 24/7 y manejar múltiples conversaciones simultáneamente.

## 📋 ¿Cómo funciona para el usuario final?

Cuando un cliente contacta (por WhatsApp, web o API), el sistema:

1. **Primero entiende qué necesita** el cliente (cotización, contratación, soporte)
2. **Lo dirige al agente especializado** apropiado
3. **Mantiene una conversación natural** recopilando información necesaria
4. **Proporciona respuestas precisas** y acciones concretas (cotizaciones, links de pago, etc.)

### Ejemplo de conversación:
```
Cliente: "Hola, quiero asegurar mi coche"

Sistema: "¡Hola! Claro, me gustaría ayudarte con tu seguro de auto.
         ¿Podrías decirme qué tipo de vehículo tienes y dónde resides?"

Cliente: "Tengo un Seat Ibiza 2020, vivo en Madrid"

Sistema: "Perfecto. Te muestro las opciones disponibles para tu Seat Ibiza en Madrid..."
```

## 🏗️ Arquitectura del Sistema

### Vista Simplificada

```
Usuario → API REST → Agentes Especializados → Respuesta
```

### Componentes Principales

- **🤖 Agentes Conversacionales**: 4 especialistas diferentes
- **🛠️ Herramientas**: Funciones específicas (calcular precios, crear pagos, etc.)
- **💾 Memoria**: Recuerda el contexto de cada conversación
- **⚙️ Estrategias**: Dos formas de procesar conversaciones (simple y compleja)

### Los 4 Agentes Especializados

| Agente | ¿Qué hace? | Cuando se usa |
|--------|------------|---------------|
| **🔍 Triage** | Clasifica qué necesita el cliente | Primera interacción |
| **💰 Quote** | Muestra productos y precios | Cliente quiere cotizar |
| **📝 Contract** | Guía el proceso de contratación | Cliente quiere comprar |
| **🆘 Support** | Resuelve dudas de pólizas | Cliente ya tiene seguro |

## 🚀 Instalación y Configuración

### Paso 1: Preparar el entorno

```bash
# Crear un entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate  # En Windows
# source venv/bin/activate  # En Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 2: Configurar credenciales

Crea un archivo `.env` con tus configuraciones:

```env
# Base de datos y cache
REDIS_URL=redis://localhost:6379

# API Keys (si usas WhatsApp, pagos, etc.)
API_KEY_SECRET=tu_clave_secreta
PHONE_NUMBER_ID=tu_numero_whatsapp
WHATSAPP_ACCESS_TOKEN=tu_token_whatsapp
```

### Paso 3: Ejecutar el sistema

```bash
# Iniciar el servidor
uvicorn app.main:app --reload
```

El sistema estará disponible en `http://localhost:8000`

## 📡 Cómo usar el sistema

### Endpoint principal: `/invoke`

Para enviar mensajes al sistema:

```bash
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hola, quiero información sobre seguros de hogar",
    "session_id": "usuario123"
  }'
```

**Respuesta típica:**
```json
{
  "output": "¡Hola! Claro que sí. Los seguros de hogar incluyen cobertura...",
  "agent": "quote_agent",
  "session_id": "usuario123"
}
```

### Verificar que funciona: `/health`

```bash
curl http://localhost:8000/health
# Respuesta: {"status": "healthy"}
```

## 🔧 Detalles Técnicos

### Arquitectura por Capas

```
┌─────────────────┐
│   CAPA API      │ ← Endpoints REST
├─────────────────┤
│ ORQUESTACIÓN    │ ← Coordina agentes
├─────────────────┤
│  ESTRATEGIAS    │ ← Lógica conversacional
├─────────────────┤
│  HERRAMIENTAS   │ ← Funciones específicas
├─────────────────┤
│   MEMORIA       │ ← Contexto de conversación
├─────────────────┤
│ CONFIGURACIÓN   │ ← Archivos JSON de agentes
└─────────────────┘
```

### Tecnologías Principales

- **FastAPI**: API web rápida y moderna
- **LangGraph**: Framework para agentes conversacionales
- **Redis**: Memoria y cache de conversaciones
- **Pydantic**: Validación de datos
- **Uvicorn**: Servidor ASGI

### Estructura de Archivos

```
tfm-valley-mds10-muppy/
├── app/                    # Código principal
│   ├── core/              # Componentes centrales
│   ├── strategies/        # Lógica de agentes
│   ├── tools/            # Herramientas específicas
│   ├── schemas/          # Estructura de datos
│   └── handlers/         # Gestores de eventos
├── agents/                # Configuración de agentes
│   ├── triage_agent/     # Clasificador inicial
│   ├── quote_agent/      # Cotizaciones
│   ├── contract_agent/   # Contrataciones
│   └── support_agent/    # Soporte
└── requirements.txt      # Dependencias
```

## 📊 Estado Actual del Proyecto

### ✅ Lo que ya está implementado

- **Arquitectura completa** y modular
- **4 agentes especializados** configurados
- **Sistema de prompts** para conversaciones
- **API REST funcional**
- **Esquemas de datos** para seguros
- **Herramientas base** (placeholders listos para implementar)

### 🔄 Próximos pasos prioritarios

1. **Conectar herramientas reales**
   - Integrar catálogo de productos Mapfre
   - Sistema de cálculo de precios real
   - Conexión con pasarelas de pago (Stripe)
   - Base de datos para guardar leads

2. **Refinar conversaciones**
   - Ajustar prompts al estilo Mapfre
   - Agregar ejemplos específicos
   - Mejorar manejo de casos complejos

3. **Agregar funcionalidades**
   - Integración WhatsApp completa
   - Webhooks de pago
   - Dashboard de métricas

## 🛠️ Desarrollo Avanzado

### Agregar un nuevo agente

1. Crear carpeta: `agents/nuevo_agente/`
2. Archivo `config.json` con configuración
3. Crear prompts necesarios
4. El sistema lo detecta automáticamente

### Configuración de agentes

Cada agente se define con un archivo JSON:

```json
{
  "agent_role": "mi_agente",
  "strategy": "state_machine",
  "memory": {
    "type": "buffer_window",
    "config": {"k": 10}
  },
  "llm_configurations": {...},
  "state_machine": {...}
}
```

## 🎓 Guía para Compañeros de Máster

### Conceptos básicos que necesitas entender

- **Agente conversacional**: Un programa que mantiene conversaciones naturales
- **API REST**: Interfaz para que otros sistemas se comuniquen con el nuestro
- **JSON**: Formato de datos estructurado (como un diccionario)
- **Prompt**: Instrucciones que le damos al modelo de IA

### ¿Qué hace cada archivo importante?

- **`app/main.py`**: El "cerebro" principal que recibe peticiones
- **`agents/*/config.json`**: Configuración de cada agente especializado
- **`app/tools/insurance_tools.py`**: Funciones específicas de seguros
- **`requirements.txt`**: Lista de librerías necesarias

### Flujo típico de desarrollo

1. **Modificar prompts** en `agents/*/prompts/` para cambiar conversaciones
2. **Ajustar lógica** en `app/tools/` para cambiar comportamientos
3. **Configurar agentes** editando archivos `config.json`
4. **Probar cambios** usando el endpoint `/invoke`

## 📝 Notas Importantes

- **Herramientas placeholder**: Las funciones en `insurance_tools.py` son ejemplos - necesitan conectarse a sistemas reales de Mapfre
- **Prompts genéricos**: Están preparados para seguros pero pueden necesitar ajustes específicos de productos Mapfre
- **Base de datos**: Actualmente usa Redis para conversaciones, pero necesitarás BigQuery para datos persistentes
- **Seguridad**: Configura las variables de entorno correctamente antes de usar en producción

## 🤝 Contribuir

1. Crea una rama para tu feature: `git checkout -b feature/nueva-funcionalidad`
2. Haz tus cambios y commits descriptivos
3. Sube la rama: `git push origin feature/nueva-funcionalidad`
4. Crea un Pull Request explicando los cambios

## 📄 Licencia

Ver archivo LICENSE para detalles.
