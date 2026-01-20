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

### 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.8+**: Descárgalo de [python.org](https://python.org)
- **Git**: Para clonar el repositorio
- **Redis**: Base de datos para cache y sesiones
- **Cuenta de Google**: Para Google Sheets (opcional para desarrollo local)

#### Instalación de Redis

**Windows:**
```bash
# Usando Chocolatey (recomendado)
choco install redis-64

# O descarga desde: https://redis.io/download
```

**Linux/Ubuntu:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

**macOS:**
```bash
# Usando Homebrew
brew install redis
brew services start redis
```

**Verificar que Redis funciona:**
```bash
redis-cli ping
# Debería responder: PONG
```

### 🔧 Instalación Paso a Paso

#### Paso 1: Clonar el repositorio

```bash
# Clonar el proyecto
git clone https://github.com/ssillerom/tfm-valley-mds10-muppy.git
cd tfm-valley-mds10-muppy

# Cambiar a la rama Dev
git checkout Dev
```

#### Paso 2: Configurar entorno virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
# source venv/bin/activate

# Verificar que estamos en el entorno virtual
# Deberías ver (venv) al inicio de la línea de comandos
```

#### Paso 3: Instalar dependencias

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar todas las dependencias
pip install -r requirements.txt

# Verificar instalación
pip list | grep fastapi
# Deberías ver: fastapi, uvicorn, etc.
```

### ⚙️ Configuración del Entorno

#### Paso 4: Crear archivo .env

Crea un archivo llamado `.env` en la raíz del proyecto con esta configuración:

```env
# ======================================
# CONFIGURACIÓN BÁSICA
# ======================================

# Clave secreta para la API (genera una segura para producción)
API_KEY_SECRET=mi_clave_super_secreta_para_desarrollo_12345

# URL de Redis (ajusta según tu instalación)
REDIS_URL=redis://localhost:6379

# ======================================
# WHATSAPP BUSINESS API (OPCIONAL)
# ======================================

# Solo si vas a usar WhatsApp
PHONE_NUMBER_ID=tu_numero_de_telefono_id
WHATSAPP_ACCESS_TOKEN=tu_token_de_acceso_whatsapp
WHATSAPP_APP_SECRET=tu_app_secret_whatsapp
WHATSAPP_VERIFY_TOKEN=tu_verify_token_whatsapp

# ======================================
# GOOGLE CLOUD (OPCIONAL)
# ======================================

# Para Google Sheets
# Credenciales de Google Sheets API
GOOGLE_SHEETS_CREDENTIALS=ruta/a/tu/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=tu_spreadsheet_id

# ======================================
# OTROS SERVICIOS (OPCIONAL)
# ======================================
```

#### Paso 5: Configurar Google Sheets (opcional pero recomendado)

Si quieres usar Google Sheets para persistir datos:

```bash
# 1. Ve a Google Cloud Console: https://console.cloud.google.com/
# 2. Crea un nuevo proyecto o selecciona uno existente
# 3. Habilita la Google Sheets API:
#    - Ve a "APIs & Services" > "Library"
#    - Busca "Google Sheets API" y habilítala

# 4. Crea credenciales:
#    - Ve a "APIs & Services" > "Credentials"
#    - Crea "OAuth 2.0 Client IDs"
#    - Descarga el archivo JSON y colócalo en el proyecto

# 5. Comparte tu Google Sheet:
#    - Crea un nuevo Google Sheet
#    - Copia el ID del URL (entre /d/ y /edit)
#    - Comparte el sheet con el email del service account
```

### ▶️ Ejecutar el Sistema

#### Paso 6: Iniciar el servidor

```bash
# Asegúrate de que el entorno virtual esté activado
# Deberías ver (venv) al inicio de la línea

# Ejecutar con recarga automática (desarrollo)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# O para producción:
# uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Paso 7: Verificar que funciona

Abre otra terminal y prueba:

```bash
# Verificar estado del servicio
curl http://localhost:8000/health

# Deberías obtener:
# {"status": "healthy"}

# Probar el endpoint principal
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hola, quiero información sobre seguros",
    "session_id": "test123"
  }'

# Deberías obtener una respuesta del agente
```

### 🔍 Solución de Problemas

#### Error: "ModuleNotFoundError"
```bash
# Asegúrate de tener el entorno virtual activado
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Reinstala dependencias
pip install -r requirements.txt
```

#### Error: "Redis connection refused"
```bash
# Verificar que Redis esté ejecutándose
redis-cli ping

# Si no responde, iniciar Redis:
# Windows: redis-server
# Linux: sudo systemctl start redis-server
# macOS: brew services start redis
```

#### Error: "Port 8000 already in use"
```bash
# Cambiar el puerto
uvicorn app.main:app --reload --port 8001

# O matar el proceso que usa el puerto
# Linux/Mac: lsof -ti:8000 | xargs kill -9
# Windows: En PowerShell como admin: Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process
```

#### Error: "Google Cloud credentials not found"
```bash
# Si no vas a usar Google Sheets, comenta esas líneas en .env
# O configura las credenciales correctamente
export GOOGLE_APPLICATION_CREDENTIALS=/ruta/a/tu/service_account.json
```

### 📊 Verificar Instalación Completa

Ejecuta el script de verificación incluido:

```bash
# Ejecutar verificación automática
python verify_installation.py
```

Este script verifica:
- ✅ Versión de Python (3.8+)
- ✅ Todas las dependencias instaladas
- ✅ Archivo .env configurado
- ✅ Conexión con Redis
- ✅ Aplicación importable

### 🚀 Próximos Pasos Después de la Instalación

1. **Probar los agentes**: Usa los endpoints para interactuar con cada agente
2. **Configurar herramientas reales**: Conecta con APIs de Mapfre para datos reales
3. **Personalizar prompts**: Ajusta las conversaciones según el estilo de Mapfre
4. **Configurar monitoring**: Agrega logs y métricas para producción

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
- **Base de datos**: Actualmente usa Redis para conversaciones, pero necesitarás Google Sheets para datos persistentes
- **Memoria**: El sistema utiliza Redis para almacenar el historial de conversaciones y estados de sesión
- **Seguridad**: Configura las variables de entorno correctamente antes de usar en producción

## 🤝 Contribuir

1. Crea una rama para tu feature: `git checkout -b feature/nueva-funcionalidad`
2. Haz tus cambios y commits descriptivos
3. Sube la rama: `git push origin feature/nueva-funcionalidad`
4. Crea un Pull Request explicando los cambios

## 📖 Glosario de Términos Técnicos

### 🛠️ Desarrollo y Programación

- **API REST**: Interfaz de programación que permite que diferentes sistemas se comuniquen entre sí a través de internet, usando operaciones como GET, POST, PUT, DELETE.

- **JSON**: Formato de texto ligero para intercambiar datos. Es como un diccionario estructurado que tanto humanos como máquinas pueden entender fácilmente.

- **FastAPI**: Framework moderno y rápido para crear APIs web en Python. Es como un constructor de carreteras que hace más fácil crear conexiones entre sistemas.

- **Pydantic**: Biblioteca de Python que valida y convierte datos automáticamente. Asegura que la información que entra al sistema tenga el formato correcto.

- **Uvicorn**: Servidor web ultrarrápido que ejecuta aplicaciones Python. Es el "motor" que hace funcionar nuestra API.

- **ASGI**: Estándar técnico para servidores web asíncronos. Permite manejar múltiples conexiones simultáneamente sin bloquearse.

- **Endpoint**: Una URL específica en nuestra API donde se puede enviar o recibir información (como `/invoke` o `/health`).

### 🤖 Inteligencia Artificial y Agentes

- **Agente Conversacional**: Un programa inteligente que puede mantener conversaciones naturales con humanos, entendiendo contexto y respondiendo de manera coherente.

- **LangGraph**: Framework especializado para construir agentes conversacionales complejos. Es como un mapa que guía cómo fluyen las conversaciones.

- **LLM (Large Language Model)**: Modelo de inteligencia artificial grande entrenado en enormes cantidades de texto, capaz de generar respuestas naturales (como GPT).

- **Prompt**: Las instrucciones específicas que le damos al modelo de IA para que sepa cómo comportarse en una conversación.


- **Buffer Window**: Técnica de memoria que mantiene solo las últimas N interacciones de una conversación para no sobrecargar el sistema.

### 💾 Almacenamiento y Datos

- **Redis**: Base de datos súper rápida especializada en almacenar datos temporales y cache. Perfecta para conversaciones en tiempo real.

- **Google Sheets**: Hoja de cálculo de Google que usaremos como base de datos simple para almacenar leads y datos de seguros.

- **Session ID**: Identificador único para cada conversación. Es como el número de ticket que te dan en una tienda para recordar tu turno.

- **Metadata**: Información adicional que acompaña a los mensajes principales, como timestamps, configuración del usuario, etc.

### 🔧 Herramientas de Desarrollo

- **Virtual Environment (venv)**: Entorno aislado de Python donde instalas las librerías del proyecto sin afectar otras aplicaciones.

- **Pip**: Gestor de paquetes de Python. Es como un "instalador de apps" para librerías y herramientas de Python.

- **Requirements.txt**: Archivo que lista todas las librerías necesarias para el proyecto con sus versiones específicas.

- **.env**: Archivo de configuración que contiene variables secretas (como contraseñas de APIs) sin subirlas al código público.

- **Curl**: Herramienta de línea de comandos para hacer peticiones HTTP. Es como un navegador de texto para probar APIs.

- **HTTP Headers**: Información adicional que se envía con cada petición web, como el tipo de contenido o autenticación.

- **Content-Type**: Cabecera HTTP que indica qué tipo de datos se están enviando (como "application/json" para datos JSON).

### 🏗️ Arquitectura y Diseño

- **State Machine**: Máquina de estados que define cómo fluye una conversación paso a paso, como un diagrama de flujo automatizado.

- **Strategy Pattern**: Patrón de diseño que permite cambiar el comportamiento de un sistema sin modificar su código principal.

- **Placeholder**: Código temporal que representa una funcionalidad que se implementará más tarde. Es como un "por hacer" en el código.

- **Webhook**: Mecanismo que permite que un sistema notifique automáticamente a otro cuando ocurre un evento (como cuando se completa un pago).

- **Pull Request**: Propuesta de cambios en el código que otros desarrolladores pueden revisar y aprobar antes de integrar al proyecto principal.

### 💰 Pagos y Negocio

- **Stripe**: Plataforma de pagos en línea que permite procesar transacciones de manera segura y sencilla.

- **Lead**: Potencial cliente que ha mostrado interés en un producto o servicio.

### 📊 Estados y Ciclo de Desarrollo

- **Branch**: Rama en Git que permite desarrollar features de manera aislada sin afectar el código principal.

- **Commit**: Guardado de cambios en el repositorio con un mensaje descriptivo de qué se modificó.

- **Repository/Repo**: Almacén digital donde se guarda todo el código y su historial de cambios.

## 📄 Licencia

Ver archivo LICENSE para detalles.
