# 🤖 Sistema de Agentes Conversacionales para Seguros

<div align="center">

![Sistema de Agentes Conversacionales](https://img.shields.io/badge/Sistema-Agentes%20Conversacionales-blue?style=for-the-badge&logo=robot)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=chainlink&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)

**🏆 Sistema multiagente avanzado para gestión integral de seguros**

[📋 Cómo levantar (dev)](#-guía-de-puesta-en-marcha-desarrollo) • [📁 Estructura del repo](#51-estructura-del-repositorio) • [📊 Observabilidad](#52-observabilidad-arize-logs-trazabilidad) • [🛠️ API](#-api-reference) • [📖 Documentación (docs/)](docs/README.md) • [🤝 Contribuir](#-contribuir)

**Frontend desplegado (Vercel):** [https://tfm-valley-mds10-muppy.vercel.app/](https://tfm-valley-mds10-muppy.vercel.app/) — Para que funcione, el backend debe estar expuesto con **ngrok** y en Vercel debe estar configurado `VITE_API_URL` con la URL del túnel (ver [§ 5.5](#55-frontend-en-vercel-con-backend-local-ngrok)).

---

## 🎯 ¿Qué hace este sistema?

Transforma la experiencia de seguros tradicional en una **conversación inteligente y natural**. El sistema combina **inteligencia artificial avanzada** con **procesos especializados de seguros** para ofrecer:

### ✨ Características Principales

- **🎯 4 Agentes Especializados**: Cada uno experto en su dominio específico
- **💬 Conversaciones Naturales**: Entiende contexto y mantiene memoria
- **⚡ Procesamiento en Tiempo Real**: Respuestas instantáneas 24/7
- **🔄 Flujos Complejos**: Gestiona procesos multi-paso automáticamente
- **📊 Integración Total**: Conecta con sistemas de pago, bases de datos y WhatsApp

### 🚀 Casos de Uso Reales

| Escenario | ¿Qué hace el sistema? | Beneficio |
|-----------|----------------------|-----------|
| **Cliente nuevo** | Guía desde consulta inicial hasta contratación completa | Experiencia fluida sin fricción |
| **Cotización rápida** | Muestra opciones personalizadas en segundos | Comparación inteligente |
| **Soporte post-venta** | Resuelve dudas sobre pólizas existentes | Atención inmediata |
| **Gestión masiva** | Maneja cientos de conversaciones simultáneas | Escalabilidad ilimitada |

### 💡 Ejemplo de Conversación Completa

```
👤 Cliente: "Hola, quiero un seguro para mi coche nuevo"

🤖 Sistema: "¡Hola! Claro que sí. Me gustaría ayudarte con tu seguro de auto.
           ¿Podrías decirme qué tipo de vehículo tienes y dónde resides?"

👤 Cliente: "Tengo un Tesla Model 3 2024, vivo en Barcelona"

🤖 Sistema: "¡Excelente elección! El Tesla Model 3 tiene características especiales.
           Te muestro las opciones disponibles para Barcelona:

           🛡️ Seguro Básico: 45€/mes - Cobertura responsabilidad civil
           🛡️ Seguro Completo: 89€/mes - Todo riesgo con asistencia 24h
           🛡️ Seguro Premium: 145€/mes - Cobertura total + robo de batería

           ¿Cuál te interesa más conocer?"

👤 Cliente: "El completo por favor"

🤖 Sistema: "Perfecto. Para el Seguro Completo necesitaré algunos datos:
           - ¿Cuántos años tienes?
           - ¿Tienes garaje privado?
           - ¿Cuál es tu código postal exacto?"

👤 Cliente: "Tengo 35 años, sí tengo garaje, código postal 08001"

🤖 Sistema: "¡Genial! Con esa información, tu prima final es de 82€/mes
           (5% descuento por garaje privado).

           ¿Quieres proceder con la contratación? Te envío el link de pago seguro."

👤 Cliente: "Sí, vamos"

🤖 Sistema: "¡Perfecto! Aquí tienes el link de pago seguro:
           🔗 https://pago.seguros-ejemplo.com/contrato/ABC123

           Una vez completado, recibirás la póliza por email en 5 minutos."
```

---

## 🏗️ Arquitectura del Sistema

### 📊 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                           🌐 USUARIO FINAL                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  WhatsApp   │  │    Web      │  │   Mobile    │  │    API      │   │
│  │ Messages    │  │   Chat      │  │    App      │  │  Clients    │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                 │                 │                 │          │
└─────────┼─────────────────┼─────────────────┼─────────────────┼──────────┘
          │                 │                 │                 │
          └─────────────────┼─────────────────┼─────────────────┼──────────┘
                            │                 │                 │
┌───────────────────────────┼───────────────────────────────────┼──────────┐
│                           ▼                                   ▼          │
│  ┌────────────────────────────────────────────────────────────┼─────────┐ │
│  │                        🚀 CAPA DE API                      │         │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │         │ │
│  │  │   POST /invoke  │  │  GET /health    │  │   Webhooks  │ │         │ │
│  │  │   (Principal)   │  │   (Monitoreo)   │  │   (Pagos)   │ │         │ │
│  │  └─────────┬───────┘  └─────────┬───────┘  └──────┬──────┘ │         │ │
│  │            │                     │                  │        │         │ │
│  └────────────┼─────────────────────┼──────────────────┼────────┘         │
│               │                     │                  │                   │
│               └─────────────────────┼──────────────────┼──────────────────┘
│                                     │                  │
│  ┌──────────────────────────────────┼──────────────────┼──────────────────┐
│  │                                  ▼                  ▼                   │
│  │                     🤖 CAPA DE ORQUESTACIÓN                          │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  │                   AgentOrchestrator                             │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │  │
│  │  │  │ Load Config │  │ LLM Cache  │  │   Strategy Selection     │   │  │
│  │  │  │             │  │ (Redis)    │  │                         │   │  │
│  │  │  └──────┬──────┘  └──────┬──────┘  └─────────┬───────────────┘   │  │
│  │  │         │                 │                  │                   │  │
│  │  └─────────┼─────────────────┼──────────────────┼───────────────────┘  │
│               │                 │                  │                       │
│  ┌────────────┼─────────────────┼──────────────────┼─────────────────────┐
│  │            ▼                 ▼                  ▼                      │
│  │        💾 MEMORIA        ⚡ CACHE          🎯 ESTRATEGIAS              │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  ┌──────────┐  │
│  │  │ Redis Store │  │ Redis Cache │  │ Generative      │  │ State    │  │
│  │  │             │  │             │  │ Strategy        │  │ Machine  │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────────┘  └────┬─────┘  │
│  │         │                 │                 │                   │        │
│  └─────────┼─────────────────┼─────────────────┼───────────────────┼────────┘
│            │                 │                 │                   │
│            └─────────────────┼─────────────────┼───────────────────┼────────┘
│                              │                 │                   │
│  ┌───────────────────────────┼─────────────────┼───────────────────┼────────┐
│  │                           ▼                 ▼                   ▼        │
│  │                    🛠️ CAPA DE HERRAMIENTAS                           │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐       │
│  │  │ Insurance   │  │ Payment     │  │ Quote Calc  │  │ Lead     │       │
│  │  │ Products    │  │ Tools       │  │             │  │ Save     │       │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────┬─────┘       │
│  │         │                 │                 │              │            │
│  └─────────┼─────────────────┼─────────────────┼──────────────┼────────────┘
│            │                 │                 │              │
│            └─────────────────┼─────────────────┼──────────────┼────────────┘
│                              │                 │              │
│  ┌───────────────────────────┼─────────────────┼──────────────┼────────────┐
│  │                           ▼                 ▼              ▼            │
│  │                    🔗 SISTEMAS EXTERNOS                              │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐       │
│  │  │  Stripe     │  │ GSheets     │  │   Redis     │  │ WhatsApp │       │
│  │  │  Payments   │  │ Database    │  │   Cache     │  │  API     │       │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └──────────┘       │
│  │                                                                        │
│  └────────────────────────────────────────────────────────────────────────┘
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────────┐
│  │                       ⚙️ CAPA DE CONFIGURACIÓN                         │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐       │
│  │  │ TriageAgent │  │ QuoteAgent  │  │ContractAgent│  │SupportAg│       │
│  │  │ config.json │  │ config.json │  │ config.json │  │ent conf │       │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └──────────┘       │
│  └────────────────────────────────────────────────────────────────────────┘
└────────────────────────────────────────────────────────────────────────────┘
```

**Nota:** En la implementación actual, la memoria de conversaciones y la caché del LLM están **en proceso** (no se usa Redis). El RAG opcional usa **Ollama** (embeddings) y **ChromaDB** para la base de conocimientos.

### 🎭 Los 4 Agentes Especializados

| Agente | 🎯 Propósito | 🤖 Estrategia | 📋 Funciones Clave |
|--------|-------------|---------------|-------------------|
| **🔍 Triage Agent** | Clasificar intención inicial | State Machine Simple | Detectar si es cotización, contratación o soporte |
| **💰 Quote Agent** | Proporcionar cotizaciones | State Machine Complejo | Mostrar productos, calcular precios, comparar opciones |
| **📝 Contract Agent** | Gestionar contratación completa | State Machine Avanzado | Recopilar datos, verificar información, procesar pago |
| **🆘 Support Agent** | Atención post-venta | Generative Strategy | Resolver dudas, consultas sobre pólizas existentes |

---

## 📋 Guía de puesta en marcha (desarrollo)

### Requisitos

- **Python 3.9+** — `python3 --version` o `python --version`
- **Node.js 18+** y **npm** — para el frontend (`node --version`, `npm --version`)
- **Git** — para clonar el repo
- **Cuenta en Google AI Studio** — para obtener una API key de Gemini (gratuita)

No se usa Redis: la memoria de conversaciones y el estado de sesión están en memoria dentro del proceso del backend.

---

### 1. Clonar y preparar el backend

```bash
git clone https://github.com/ssillerom/tfm-valley-mds10-muppy.git
cd tfm-valley-mds10-muppy

# Entorno virtual
python3 -m venv venv

# Activar (Linux/macOS)
source venv/bin/activate
# En Windows: venv\Scripts\activate

# Dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configurar variables de entorno del backend

En la **raíz del proyecto** (donde está `app/` y `requirements.txt`):

```bash
cp .env.example .env
```

Edita `.env` y rellena al menos:

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `GOOGLE_API_KEY` | **Sí** | API key de Google AI Studio (Gemini). Crear en: https://aistudio.google.com/app/apikey |
| `API_KEY_SECRET` | No | Clave para proteger la API (si se usa en el código) |
| `OLLAMA_BASE_URL` | No | URL de Ollama para el RAG (embeddings). Por defecto `http://localhost:11434`. Solo necesaria si Ollama está en otro host/puerto. |
| `LOGIN_USER` / `LOGIN_PASSWORD` | No | Si los defines, el chat (frontend) exigirá usuario y contraseña; `/invoke` solo aceptará peticiones con un JWT válido (obtenido con `POST /auth/login`). Opcional: `JWT_SECRET_KEY` para firmar los tokens. Los usuarios también se pueden registrar en `data/users.json` (ver abajo). |
| `ARIZE_SPACE_ID`, `ARIZE_PROJECT_NAME`, `ARIZE_API_KEY` | No | Observabilidad: trazas a Arize AX. Si tu cuenta es EU, añade `ARIZE_COLLECTOR_ENDPOINT=https://otlp.eu-west-1a.arize.com/v1`. Ver [docs/ARIZE_TRACING.md](docs/ARIZE_TRACING.md). |
| `LOG_FORMAT` | No | Si vale `json`, los logs se emiten en JSON (una línea por evento). |

**Registrar usuarios:** Puedes dar de alta usuarios de dos formas:

1. **Por consola** (desde la raíz del proyecto, venv activado):
   ```bash
   python -m app.auth add_user mi_usuario
   # Te pedirá la contraseña por consola (no se muestra al escribir)
   ```
   O con contraseña en la línea de comandos: `python -m app.auth add_user mi_usuario mi_contraseña`

2. **Por API** (para scripts o integraciones): `POST /auth/register` con body `{"username": "...", "password": "..."}` y cabecera **`X-Admin-Key: <API_KEY_SECRET o REGISTER_SECRET>`**. Si no defines `API_KEY_SECRET` ni `REGISTER_SECRET`, el registro por API no estará disponible.

Los usuarios se guardan en **`data/users.json`** (archivo en `.gitignore`). El usuario definido en `LOGIN_USER` (env) no se puede sobrescribir desde el archivo.

Ejemplo mínimo de `.env` en la raíz:

```env
GOOGLE_API_KEY=tu_api_key_de_google_ai_studio
```

### 3. Levantar el backend

Desde la raíz del proyecto, con el venv activado:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Comprobar:

```bash
curl http://localhost:8000/health
# Debe devolver: {"status":"healthy"}
```

### 4. Configurar y levantar el frontend

En **otra terminal**, desde la raíz del proyecto:

```bash
cd frontend
cp .env.example .env
npm install
```

Edita `frontend/.env`:

| Variable | Descripción |
|----------|-------------|
| `VITE_API_URL` | URL del backend. En local suele ser `http://localhost:8000`. Si el backend corre en otro host/puerto, cámbialo aquí (ej. `http://localhost:8001`). |

Ejemplo `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

Levantar el frontend:

```bash
npm run dev
```

Abre en el navegador la URL que muestre Vite (normalmente `http://localhost:5173`). El chat ya debería hablar con el backend.

### 5. Resumen de comandos

| Dónde | Comando |
|-------|--------|
| Raíz del proyecto | `source venv/bin/activate` → `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| Raíz (Windows) | `.\scripts\run\start-backend.ps1` para backend, `.\scripts\run\run-stress.ps1` para stress test |
| `frontend/` | `npm run dev` |

### 5.1. Estructura del repositorio

**Levantar backend o stress test:** todos los scripts están en `scripts/`. Comandos rápidos (para Cursor o para ti): [docs/COMANDOS_RAPIDOS.md](docs/COMANDOS_RAPIDOS.md).

```
├── app/                    # Backend FastAPI (agentes, estrategias, herramientas)
├── agents/                 # Configuración y prompts por agente (triage, quote, contract, support)
├── data/                   # Documentos RAG por producto (seguro_coche, hogar, moto)
├── docs/                   # Documentación: Arize, logs, métricas, roadmap (ver docs/README.md)
├── evaluation/             # Golden Set + LLM as a Judge (run_golden.py, judge.py, golden_set.json)
├── frontend/               # Chat React/Vite
├── load_tests/             # Stress test con Locust (500 usuarios)
├── tests/                  # Tests (p. ej. tests/test_rag.py para RAG)
├── scripts/                 # Todos los scripts. run/ (backend, stress), git/, data/. Ver scripts/README.md
├── .env, .env.example      # Variables de entorno (raíz)
└── requirements.txt        # Dependencias Python (incluye Locust para stress test)
```

### 5.2. Observabilidad (Arize, logs, trazabilidad)

- **Trazas:** El backend envía trazas a **Arize AX** (Tracing Projects). Configuración en `.env`: `ARIZE_SPACE_ID`, `ARIZE_PROJECT_NAME`, `ARIZE_API_KEY`; si tu cuenta es EU, añade `ARIZE_COLLECTOR_ENDPOINT=https://otlp.eu-west-1a.arize.com/v1`. Ver [docs/ARIZE_TRACING.md](docs/ARIZE_TRACING.md).
- **Trazabilidad:** Cada petición tiene un **Request ID** (`X-Request-ID` en cabeceras y en el span de OpenTelemetry) para correlacionar logs y trazas.
- **Logs:** Los logs incluyen `request_id`, `trace_id` y `span_id`. Formato JSON opcional con `LOG_FORMAT=json` en `.env`. Ver [docs/LOGGING.md](docs/LOGGING.md).
- **Métricas y dashboards:** Definición de las 6 métricas core y qué dashboards de Arize añadir: [docs/METRICAS_CORE.md](docs/METRICAS_CORE.md), [docs/ARIZE_DASHBOARDS.md](docs/ARIZE_DASHBOARDS.md).
- **Índice de documentación:** [docs/README.md](docs/README.md).

### 5.3. Evaluación (Golden Set y LLM as a Judge)

- **Golden Set:** Casos de prueba (input → criterios de respuesta) para detectar regresiones. Con el backend en marcha: `python evaluation/run_golden.py`. Opción `--judge` para evaluar con un LLM juez los casos que tengan `judge_criteria` en `evaluation/golden_set.json`. Ver [evaluation/README.md](evaluation/README.md).

### 5.4. Pruebas de carga (stress test)

- **Locust:** Simula 500 usuarios (health + `/invoke`). Con el backend en marcha: `.\scripts\run\run-stress.ps1` (headless) o `locust -f load_tests/locustfile.py --host=http://localhost:8000` (UI en http://localhost:8089). Locust ya está en `requirements.txt`. Ver [load_tests/README.md](load_tests/README.md). Resumen de comandos: [docs/COMANDOS_RAPIDOS.md](docs/COMANDOS_RAPIDOS.md).

### 5.5. Frontend en Vercel con backend local (ngrok)

El frontend está desplegado en **Vercel** en: **[https://tfm-valley-mds10-muppy.vercel.app/](https://tfm-valley-mds10-muppy.vercel.app/)** (Muppy AI | Asistente de Seguros). Para que ese chat funcione, el backend tiene que estar **expuesto mediante ngrok**; si no, el frontend en Vercel no puede alcanzar un backend que corre solo en local.

Pasos:

1. **Backend** en local: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` (o `.\scripts\run\start-backend.ps1`)
2. **Túnel ngrok**: `ngrok http 8000 --domain=tu-dominio.ngrok-free.app` (o sin `--domain` si usas URL temporal)
3. En **Vercel** → proyecto del frontend → **Settings** → **Environment Variables**: `VITE_API_URL` = `https://tu-dominio.ngrok-free.app` (con `https://`)
4. **Redeploy** el frontend para que el build use la nueva URL.

El frontend ya envía la cabecera `ngrok-skip-browser-warning: true` en las peticiones para evitar la página intersticial de ngrok. Mientras ngrok y el backend estén activos, el chat en [tfm-valley-mds10-muppy.vercel.app](https://tfm-valley-mds10-muppy.vercel.app/) hablará con tu backend local.

### 6. Problemas frecuentes

- **Puerto 8000 ocupado**: Mata procesos con `lsof -ti :8000 | xargs kill -9` (Linux/macOS) o levanta el backend en otro puerto, p. ej. `--port 8001`, y pon en `frontend/.env` `VITE_API_URL=http://localhost:8001`.
- **El frontend no conecta**: Comprueba que el backend esté en marcha y que `VITE_API_URL` en `frontend/.env` coincida con la URL y puerto del backend.
- **Error de API / agente**: Verifica que `GOOGLE_API_KEY` en el `.env` de la raíz sea correcta y tenga cuota en Google AI Studio.

### 7. RAG y Ollama (base de conocimientos)

El sistema incluye un **RAG** (Retrieval-Augmented Generation) para que los agentes consulten documentación de seguros (coche, hogar, moto) desde la carpeta `data/`. Si quieres usar la herramienta **search_insurance_info** (consultas sobre coberturas, exclusiones, etc.), necesitas tener **Ollama** instalado y el modelo de embeddings descargado.

#### Qué hay que tener instalado

1. **Ollama**  
   - Descarga e instalación: [ollama.com](https://ollama.com)  
   - Tras instalar, Ollama suele arrancar solo y exponer la API en `http://localhost:11434`. Si no, ejecuta: `ollama serve`.

2. **Modelo de embeddings**  
   - Usamos **mxbai-embed-large** ([ollama.com/library/mxbai-embed-large](https://ollama.com/library/mxbai-embed-large)), de mixedbread.ai.  
   - Descargar el modelo en Ollama:
   ```bash
   ollama pull mxbai-embed-large
   ```

#### Cómo funciona el RAG

1. **Documentos**: Los Markdown de `data/` (p. ej. `data/seguro_coche/`, `data/seguro_hogar/`, `data/seguro_moto/`) se cargan con metadatos (`insurance_type`, `product`, `doc_type`).
2. **Fragmentación**: Se trocean con `RecursiveCharacterTextSplitter` (chunk 500, overlap 100) optimizado para títulos Markdown.
3. **Embeddings**: Cada fragmento se convierte en vector con **Ollama** y el modelo **mxbai-embed-large**.
4. **Almacenamiento**: Los vectores se guardan en **ChromaDB** (carpeta `chroma_db/`). Esta carpeta se genera localmente al hacer `rebuild` y está en `.gitignore`; cada desarrollador o entorno debe crear su propio índice.
5. **Búsqueda**: Los agentes usan la herramienta `search_insurance_info` para hacer búsqueda semántica (y opcionalmente filtrar por tipo de seguro, producto o tipo de documento).

Si **Ollama no está instalado o no está corriendo**, el chat seguirá funcionando, pero las llamadas a `search_insurance_info` fallarán cuando un agente intente consultar la base de conocimientos.

#### Cotización con RAG

Cada cotización (`calculate_quote`) consulta **automáticamente** la base de conocimientos (ChromaDB + Ollama) para obtener las coberturas. Las coberturas que se muestran al usuario salen del RAG cuando está disponible.

**Para que funcione:**

1. **Ollama en marcha** (p. ej. `ollama serve` o que arranque solo).
2. **`OLLAMA_BASE_URL` en `.env`** (por defecto `http://localhost:11434` si Ollama está en local).
3. **Índice RAG creado** (la primera vez o si cambias documentos en `data/`):
   ```bash
   python -m app.rag.vector_store rebuild
   ```
   Descarga el modelo de embeddings si hace falta: `ollama pull mxbai-embed-large`.

Cuando cotices y el RAG esté disponible, en el **terminal del backend** verás el mensaje: `--- [Insurance Tools] Cotización enriquecida con RAG (base de conocimientos) ---`. Si el RAG no está disponible (Ollama apagado, índice vacío, etc.), la cotización se devuelve igual y las coberturas salen de la lista interna del cálculo.

#### Reconstruir el índice RAG

Si añades o cambias archivos en `data/`, reconstruye el índice desde la raíz del proyecto (venv activado):

```bash
python -m app.rag.vector_store rebuild
```

La **primera vez** puede tardar **varios minutos** (10–30 según máquina): se generan miles de chunks y cada uno se embede con Ollama. Deja que termine.

Estadísticas del índice:

```bash
python -m app.rag.vector_store stats
```

Probar una búsqueda:

```bash
python -m app.rag.vector_store search "coberturas" coche
```

#### Variable de entorno opcional (Ollama)

Si Ollama no corre en `http://localhost:11434`, define en el `.env` de la raíz:

```env
OLLAMA_BASE_URL=http://localhost:11434
```

(o la URL donde tengas Ollama). Si no la pones, se usa `http://localhost:11434` por defecto.

#### Dependencias Python del RAG

En `requirements.txt` están ya incluidas: `chromadb`, `langchain-chroma`, `langchain-ollama`, `langchain-text-splitters`. Se instalan con `pip install -r requirements.txt`. No hace falta configurar nada más en el `.env` para Ollama si usas el valor por defecto.

#### Problemas con el RAG

- **"Connection refused" o error al hacer rebuild/search**: Comprueba que Ollama esté en marcha (`ollama serve` si no arranca solo) y que el modelo esté descargado (`ollama pull mxbai-embed-large`).
- **Ollama en otra máquina o puerto**: Pon en el `.env` de la raíz `OLLAMA_BASE_URL=http://IP:11434` (o la URL que uses).

#### Validación de datos (DNI/NIF/NIE)

En el **Contract Agent**, los datos de lead (nombre, DNI/NIF/NIE, etc.) se validan con un validador español en `app/utils/dni_nif.py`: algoritmo oficial módulo 23, normalización de espacios/guiones y soporte para DNI, NIF de empresa y NIE. Los esquemas estructurados en `app/schemas/structured_outputs.py` usan esta validación para rechazar documentos inválidos.

### 8. Evaluación y Arize Phoenix (tracing LangGraph)

El proyecto incluye **tracing con Arize Phoenix** para observar las invocaciones de LangGraph (qué nodo se ejecuta, qué prompt se usa, latencia, etc.) y un **sistema de evaluación** que analiza los prompts de cada parte del grafo.

1. **Dependencias** (ya en `requirements.txt`): `openinference-instrumentation-langchain`, `arize-phoenix-otel`.
2. **Activar tracing**: en tu `.env` pon `PHOENIX_PROJECT_NAME=tfm-muppy-multiagent` (o `PHOENIX_ENABLED=true`). El backend registrará el tracer antes de cargar LangGraph; las invocaciones a `/invoke` quedarán trazadas en Phoenix.
3. **Phoenix**: levanta Phoenix local o usa [Phoenix Cloud](https://docs.arize.com/phoenix/phoenix-cloud). Por defecto el tracer envía a `localhost:4317` (gRPC).
4. **Catálogo de prompts**: ejecuta `python run_evaluation.py` para listar todos los prompts por agente y nodo del grafo. Con `--catalog-json` obtienes el catálogo en JSON (agente, nodo, ruta, texto del prompt, herramientas).
5. **Muestras para trazas**: con el backend en marcha, `python run_evaluation.py --run-samples --samples 5` invoca el API con casos de prueba; en Phoenix podrás ver qué nodos y prompts se usaron en cada conversación.

---

## 🏗️ Arquitectura del Sistema

### Vista Simplificada

```
Usuario → API REST → Agentes Especializados → Respuesta
```

### Componentes Principales

- **🤖 Agentes Conversacionales**: 4 especialistas diferentes
- **🛠️ Herramientas**: Funciones específicas (calcular precios, crear pagos, etc.)
- **💾 Memoria**: Recuerda el contexto de cada conversación (en memoria, sin Redis)
- **⚙️ Estrategias**: Dos formas de procesar conversaciones (simple y compleja)

### Los 4 Agentes Especializados

| Agente | ¿Qué hace? | Cuando se usa |
|--------|------------|---------------|
| **🔍 Triage** | Clasifica qué necesita el cliente | Primera interacción |
| **💰 Quote** | Muestra productos y precios | Cliente quiere cotizar |
| **📝 Contract** | Guía el proceso de contratación | Cliente quiere comprar |
| **🆘 Support** | Resuelve dudas de pólizas | Cliente ya tiene seguro |

---

## 🚀 Instalación y Configuración Completa

### 📋 Requisitos Previos Detallados

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.9+**: Descárgalo de [python.org](https://python.org)
- **Node.js 18+** y **npm**: Para el frontend (descarga en [nodejs.org](https://nodejs.org))
- **Git**: Para clonar el repositorio
- **Cuenta en Google AI Studio**: Para obtener la API key de Gemini (gratuita, en [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey))
- **Ollama** (opcional, solo para RAG): Para que los agentes consulten la base de conocimientos (`search_insurance_info`). Descarga en [ollama.com](https://ollama.com) y luego `ollama pull mxbai-embed-large`.

**Nota:** El proyecto no usa Redis; la memoria de conversaciones y el estado de sesión están en memoria dentro del proceso del backend.

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

#### Paso 4: Crear archivo .env (backend)

Crea un archivo `.env` en la **raíz del proyecto** (junto a `app/` y `requirements.txt`). Puedes copiar desde la plantilla:

```bash
cp .env.example .env
```

Contenido mínimo necesario:

```env
# Obligatorio: API key de Google AI Studio (Gemini)
# Obtener en: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=tu_api_key_aqui

# Opcional: clave para proteger la API
# API_KEY_SECRET=mi_clave_secreta

# Opcional: URL de Ollama para RAG (embeddings). Por defecto http://localhost:11434
# OLLAMA_BASE_URL=http://localhost:11434
```

El frontend tiene su propio `.env` dentro de `frontend/`. Copia `frontend/.env.example` a `frontend/.env` y configura:

```env
# URL del backend (en local normalmente)
VITE_API_URL=http://localhost:8000
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

#### Paso 6: Iniciar el backend

```bash
# Asegúrate de que el entorno virtual esté activado (venv)
# Ejecutar con recarga automática (desarrollo)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Paso 7: Iniciar el frontend (otra terminal)

```bash
cd frontend
npm install   # solo la primera vez
npm run dev
```

Abre en el navegador la URL que muestre Vite (p. ej. `http://localhost:5173`). El chat usará el backend si `VITE_API_URL` en `frontend/.env` apunta a `http://localhost:8000`.

#### Paso 8: Verificar que funciona

```bash
# Backend
curl http://localhost:8000/health
# Debe devolver: {"status":"healthy"}

# Probar el endpoint principal
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{"input": "Hola, quiero información sobre seguros", "session_id": "test123"}'
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

#### Error: "Puerto 8000 ya en uso" o "Address already in use"
```bash
# Liberar el puerto (Linux/macOS):
lsof -ti :8000 | xargs kill -9

# O levantar el backend en otro puerto:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
# y en frontend/.env poner: VITE_API_URL=http://localhost:8001
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
- ✅ Variables de entorno (GOOGLE_API_KEY, opcional OLLAMA_BASE_URL para RAG)
- ✅ Aplicación importable

### 🚀 Próximos Pasos Después de la Instalación

1. **Probar los agentes**: Usa los endpoints para interactuar con cada agente
2. **Configurar herramientas reales**: Conecta con APIs de aseguradoras para datos reales
3. **Personalizar prompts**: Ajusta las conversaciones según el estilo de la compañía
4. **Configurar monitoring**: Agrega logs y métricas para producción

## 📡 Cómo usar el sistema

---

## 📡 API Reference

### 🏥 Endpoint: `GET /health`

Verifica el estado del sistema.

**Ejemplo:**
```bash
curl http://localhost:8000/health
```

**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:30:00Z",
  "version": "1.0.0"
}
```

**Códigos de Estado:**
- `200` - Sistema funcionando correctamente
- `503` - Servicios no disponibles

---

### 🤖 Endpoint: `POST /invoke`

**El corazón del sistema** - Envía mensajes a los agentes conversacionales.

#### 📝 Request

```http
POST /invoke
Content-Type: application/json

{
  "input": "Hola, quiero asegurar mi coche",
  "session_id": "usuario_123",
  "metadata": {
    "source": "whatsapp",
    "user_info": {
      "name": "Juan Pérez",
      "phone": "+34612345678"
    }
  }
}
```

#### 📋 Parámetros

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `input` | string | ✅ | Mensaje del usuario |
| `session_id` | string | ✅ | ID único de la conversación |
| `metadata` | object | ❌ | Información adicional (fuente, usuario, etc.) |

#### 📤 Response

```json
{
  "output": "¡Hola Juan! Claro que sí. ¿Qué tipo de vehículo tienes?",
  "agent": "quote_agent",
  "session_id": "usuario_123",
  "metadata": {
    "confidence": 0.95,
    "processing_time": 0.8,
    "next_expected_input": "vehicle_info"
  }
}
```

#### 🎯 Ejemplos Prácticos

##### 1. Primera Interacción (Triage)
```bash
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hola, necesito un seguro",
    "session_id": "user001"
  }'
```

**Respuesta:**
```json
{
  "output": "¿Qué tipo de seguro te interesa? ¿Auto, hogar, salud o vida?",
  "agent": "triage_agent",
  "session_id": "user001"
}
```

##### 2. Cotización de Seguro
```bash
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Quiero un seguro de auto para mi Toyota Corolla",
    "session_id": "user001"
  }'
```

**Respuesta:**
```json
{
  "output": "¡Perfecto! Te muestro las opciones para Toyota Corolla:\n\n🏆 Seguro Básico: 35€/mes\n🏆 Seguro Completo: 75€/mes\n🏆 Seguro Premium: 120€/mes\n\n¿Cuál te interesa?",
  "agent": "quote_agent",
  "session_id": "user001"
}
```

##### 3. Proceso de Contratación
```bash
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Me interesa el completo, tengo 28 años y vivo en Valencia",
    "session_id": "user001"
  }'
```

**Respuesta:**
```json
{
  "output": "¡Excelente! Para el Seguro Completo necesitaré:\n1. Tu DNI/NIE\n2. Permiso de conducir\n3. Datos del vehículo\n\n¿Me los puedes proporcionar?",
  "agent": "contract_agent",
  "session_id": "user001"
}
```

##### 4. Soporte Post-venta
```bash
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Tengo una duda sobre mi póliza número POL-2024-001",
    "session_id": "support001"
  }'
```

**Respuesta:**
```json
{
  "output": "Hola, veo que tienes la póliza POL-2024-001. ¿En qué puedo ayudarte? ¿Es sobre cobertura, siniestros, o modificaciones?",
  "agent": "support_agent",
  "session_id": "support001"
}
```

#### ⚠️ Manejo de Errores

```json
{
  "error": "Invalid session format",
  "code": "VALIDATION_ERROR",
  "details": "session_id must be alphanumeric"
}
```

**Códigos de Error:**
- `VALIDATION_ERROR` - Datos de entrada inválidos
- `AGENT_ERROR` - Error interno del agente
- `SERVICE_UNAVAILABLE` - Servicios externos no disponibles

---

### 🔄 Webhooks (Próximamente)

Para integraciones avanzadas con pagos y notificaciones.

#### Webhook de Pago Completado
```http
POST /webhooks/stripe/payment-success
Content-Type: application/json
X-Webhook-Signature: stripe_signature

{
  "id": "evt_1234567890",
  "type": "payment_intent.succeeded",
  "data": {
    "object": {
      "id": "pi_1234567890",
      "amount": 7500,
      "currency": "eur",
      "metadata": {
        "session_id": "user001",
        "policy_type": "auto"
      }
    }
  }
}
```

---

## 🧪 Testing y Desarrollo

### 🧰 Herramientas de Testing

#### Script de Testing Automatizado

Crea `test_api.py`:

```python
#!/usr/bin/env python3
"""
Script completo para probar todos los endpoints y flujos
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test endpoint de salud"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print("✅ Health check passed")

def test_conversation_flow():
    """Test flujo completo de conversación"""
    session_id = f"test_{int(time.time())}"

    # Paso 1: Saludo inicial
    payload = {
        "input": "Hola, quiero un seguro de auto",
        "session_id": session_id
    }

    response = requests.post(f"{BASE_URL}/invoke", json=payload)
    assert response.status_code == 200
    data = response.json()
    print(f"🤖 Triage: {data['output'][:50]}...")

    # Paso 2: Proporcionar información del vehículo
    payload["input"] = "Tengo un Seat Ibiza, vivo en Madrid, tengo 30 años"
    response = requests.post(f"{BASE_URL}/invoke", json=payload)
    data = response.json()
    print(f"🤖 Quote: {data['output'][:50]}...")

    print("✅ Conversation flow test passed")

def test_error_handling():
    """Test manejo de errores"""
    # Test con session_id inválido
    payload = {
        "input": "Hola",
        "session_id": ""  # Vacío
    }

    response = requests.post(f"{BASE_URL}/invoke", json=payload)
    # Debería manejar el error gracefully
    print("✅ Error handling test passed")

if __name__ == "__main__":
    print("🧪 Iniciando tests de API...\n")

    try:
        test_health()
        test_conversation_flow()
        test_error_handling()
        print("\n🎉 Todos los tests pasaron exitosamente!")
    except Exception as e:
        print(f"\n❌ Test falló: {e}")
        exit(1)
```

Ejecuta: `python test_api.py`

#### Postman Collection

Importa esta colección para testing visual:

```json
{
  "info": {
    "name": "Sistema de Agentes Conversacionales",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/health",
          "host": ["{{base_url}}"],
          "path": ["health"]
        }
      }
    },
    {
      "name": "Invoke Agent",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"input\": \"Hola, quiero un seguro\",\n  \"session_id\": \"test123\",\n  \"metadata\": {\n    \"source\": \"api_test\"\n  }\n}"
        },
        "url": {
          "raw": "{{base_url}}/invoke",
          "host": ["{{base_url}}"],
          "path": ["invoke"]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    }
  ]
}
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
- **Memoria en proceso**: Historial de conversaciones y estado de sesión (sin Redis)
- **Pydantic**: Validación de datos
- **Uvicorn**: Servidor ASGI

### Estructura de Archivos

```
├── app/                    # Backend FastAPI
│   ├── core/              # Orquestador, config, LLM factory
│   ├── strategies/        # State machine y estrategias por agente
│   ├── tools/             # Herramientas (pago, leads, etc.)
│   ├── components/        # Memoria, RAG
│   ├── logging_config.py  # Logs con request_id/trace_id
│   └── main.py            # API y middleware
├── agents/                # Configuración y prompts por agente
│   ├── triage_agent/      # Clasificador inicial
│   ├── quote_agent/       # Cotizaciones
│   ├── contract_agent/    # Contrataciones
│   └── support_agent/     # Soporte
├── data/                  # Documentos para RAG (seguro_coche, hogar, moto)
├── docs/                  # Documentación (Arize, logs, métricas, roadmap)
├── evaluation/            # Golden Set y LLM as a Judge
├── load_tests/            # Stress test Locust
├── scripts/               # Utilidades: git/ (sync repo), data/ (PDF→MD). Ver scripts/README.md
├── frontend/              # Chat React/Vite
├── requirements.txt       # Dependencias Python (incluye Locust)
├── tests/                  # test_rag.py (tests del RAG)
└── scripts/run/            # start-backend.ps1, start-backend.bat, run-stress.ps1
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
   - Integrar catálogo de productos de seguros
   - Sistema de cálculo de precios real
   - Conexión con pasarelas de pago (Stripe)
   - Base de datos para guardar leads

2. **Refinar conversaciones**
   - Ajustar prompts al estilo de la compañía aseguradora
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
- **`app/tools/insurance_tools.py`**: Funciones específicas de seguros. `calculate_quote` acepta `additional_data` en JSON y normaliza claves (p. ej. `car_year`/`año_vehiculo`, `birth_date`/`fecha_nacimiento`) y varios formatos de fecha; si el RAG está disponible, obtiene las coberturas de la base de conocimientos.
- **`requirements.txt`**: Lista de librerías necesarias

### Flujo típico de desarrollo

1. **Modificar prompts** en `agents/*/prompts/` para cambiar conversaciones
2. **Ajustar lógica** en `app/tools/` para cambiar comportamientos
3. **Configurar agentes** editando archivos `config.json`
4. **Probar cambios** usando el endpoint `/invoke`

## 📝 Notas Importantes

- **Herramientas placeholder**: Las funciones en `insurance_tools.py` son ejemplos - necesitan conectarse a sistemas reales de aseguradoras
- **Prompts genéricos**: Están preparados para seguros pero pueden necesitar ajustes específicos de productos de la aseguradora
- **Memoria**: El sistema utiliza memoria en proceso para el historial de conversaciones y estados de sesión (no usa Redis)
- **Seguridad**: Configura las variables de entorno correctamente antes de usar en producción

---

## 🛠️ Guía de Desarrollo

### 🏗️ Arquitectura de Desarrollo

#### Estructura de un Agente

Cada agente sigue este patrón:

```
agents/{agent_name}/
├── config.json          # Configuración del agente
└── prompts/            # Templates de conversación
    ├── {prompt_name}.prompt
    └── ...
```

#### Archivo config.json

```json
{
  "agent_role": "contract_agent",
  "strategy": "state_machine",
  "memory": {
    "type": "buffer_window",
    "config": {"k": 10}
  },
  "llm_configurations": {
    "default": {
      "provider": "openai",
      "model": "gpt-4",
      "temperature": 0.7
    }
  },
  "state_machine": {
    "states": ["data_capture", "verification", "payment", "summary"],
    "initial_state": "data_capture"
  }
}
```

### 🔧 Desarrollo de Nuevos Agentes

#### Paso 1: Crear Estructura
```bash
# Crear directorio del agente
mkdir -p agents/nuevo_agente/prompts

# Crear archivos base
touch agents/nuevo_agente/config.json
touch agents/nuevo_agente/prompts/main.prompt
```

#### Paso 2: Configurar Agente

```json
{
  "agent_role": "nuevo_agente",
  "strategy": "generative",
  "memory": {
    "type": "buffer",
    "config": {}
  },
  "llm_configurations": {
    "default": {
      "provider": "openai",
      "model": "gpt-3.5-turbo",
      "temperature": 0.3
    }
  }
}
```

#### Paso 3: Crear Prompts

**Archivo: `prompts/main.prompt`**
```
Eres un agente especializado en [DOMINIO].

Tu personalidad: [DESCRIPCIÓN]

Instrucciones específicas:
- [INSTRUCCIÓN 1]
- [INSTRUCCIÓN 2]

Siempre responde de manera [ESTILO].
```

#### Paso 4: Probar Agente

```bash
# Reiniciar servidor
uvicorn app.main:app --reload

# Probar en otra terminal
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Mensaje de prueba",
    "session_id": "test_nuevo_agente"
  }'
```

### 🧪 Testing y QA

#### Tests Unitarios
```python
# tests/test_agents.py
import pytest
from app.core.agent_factory import get_agent_orchestrator

def test_agent_creation():
    orchestrator = get_agent_orchestrator("quote_agent")
    assert orchestrator is not None

def test_agent_response():
    # Test de respuesta del agente
    pass
```

#### Tests de Integración
```python
# tests/test_integration.py
def test_full_conversation_flow():
    # Test end-to-end de un flujo completo
    pass
```

#### Ejecutar Tests
```bash
# Instalar pytest si no lo tienes
pip install pytest pytest-asyncio

# Ejecutar tests
pytest tests/

# Con cobertura
pytest --cov=app tests/
```

### 📊 Monitoreo y Logs

#### Variables de Entorno para Logging
```env
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=logs/app.log
```

#### Ver Logs en Tiempo Real
```bash
# Tail logs
tail -f logs/app.log

# Filtrar por agente
tail -f logs/app.log | grep "quote_agent"
```

---

## ❓ FAQ - Preguntas Frecuentes

### 🤖 Sobre los Agentes

**¿Puedo tener más de 4 agentes?**
> Sí, el sistema está diseñado para ser extensible. Solo crea un nuevo directorio en `agents/` con su configuración.

**¿Cómo cambio el comportamiento de un agente?**
> Modifica los archivos `.prompt` en `agents/{agent}/prompts/` o ajusta la configuración en `config.json`.

**¿Los agentes pueden comunicarse entre sí?**
> Actualmente no directamente, pero el Triage Agent puede redirigir conversaciones a otros agentes.

### 💾 Sobre Memoria y Almacenamiento

**¿El proyecto usa Redis?**
> No. La memoria de conversaciones y el estado de sesión están en memoria dentro del proceso del backend. Si reinicias el backend, las sesiones se pierden.

**¿Cuánto tiempo duran las sesiones?**
> Por defecto 1 hora (3600 segundos), configurable en el código.

**¿Dónde se guardan los leads?**
> En Google Sheets por defecto. Se puede cambiar a cualquier base de datos.

### 🚀 Sobre Performance

**¿Cuántas conversaciones simultáneas soporta?**
> Depende del hardware. En un servidor básico: 50-100 conversaciones simultáneas.

**¿Cómo optimizar para alta carga?**
> - Implementar cache de respuestas
> - Usar balanceo de carga con múltiples instancias
> - Para memoria distribuida entre instancias, se podría integrar Redis u otro almacén externo (no incluido por defecto).

### 🔧 Sobre Desarrollo

**¿Puedo usar otros proveedores de IA además de OpenAI?**
> Sí, el sistema soporta múltiples proveedores (Google Vertex AI, Anthropic, etc.) configurables por agente.

**¿Cómo agregar nuevas herramientas?**
> Crea una función en `app/tools/` y regístrala en `app/tools/registry.py`.

**¿Es posible integrar con WhatsApp?**
> Sí, la configuración ya está preparada. Solo necesitas configurar las credenciales de WhatsApp Business API.

### 🐛 Sobre Errores Comunes

**Error al usar RAG / search_insurance_info (connection refused, etc.)**
> El RAG usa Ollama para embeddings. Asegúrate de que Ollama esté en marcha (`ollama serve` si no arranca solo) y de que el modelo esté descargado (`ollama pull mxbai-embed-large`). Si Ollama está en otro host/puerto, define `OLLAMA_BASE_URL` en el `.env` de la raíz.

**Error: "Agent not found"**
> Verifica que el directorio del agente existe en `agents/` y tiene un `config.json` válido.

**Error: "LLM API quota exceeded"**
> Revisa los límites de tu proveedor de IA o cambia a un modelo más económico.

---

## 🔧 Troubleshooting Avanzado

### 🐛 Problemas Comunes y Soluciones

#### 1. **El servidor no inicia**
```bash
# Verificar Python
python --version  # Debe ser 3.8+

# Verificar dependencias
pip check

# Verificar .env
python -c "import os; print(os.getenv('REDIS_URL'))"

# Iniciar con debug
uvicorn app.main:app --reload --log-level debug
```

#### 2. **Redis pierde conexión**
```bash
# Verificar estado de Redis
redis-cli ping

# Reiniciar Redis
sudo systemctl restart redis  # Linux
brew services restart redis   # macOS

# Verificar configuración
redis-cli config get maxmemory
```

#### 3. **Agentes responden lento**
```bash
# Verificar uso de CPU/Memoria
top  # Linux/Mac
taskmgr  # Windows

# Verificar llamadas a APIs externas
# Agregar logging para medir tiempos
```

#### 4. **Errores de memoria**
```bash
# Verificar uso de Redis
redis-cli info memory

# Limpiar sesiones antiguas
redis-cli keys "*" | xargs redis-cli del

# Ajustar límites de memoria
redis-cli config set maxmemory 256mb
```

### 📊 Diagnóstico del Sistema

#### Script de Diagnóstico Completo

Crea `diagnose_system.py`:

```python
#!/usr/bin/env python3
"""
Diagnóstico completo del sistema de agentes
"""

import os
import redis
import requests
import json
from pathlib import Path

def check_environment():
    """Verificar variables de entorno críticas"""
    required = ['API_KEY_SECRET', 'REDIS_URL']
    missing = []

    for var in required:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print(f"❌ Variables faltantes: {', '.join(missing)}")
        return False

    print("✅ Variables de entorno OK")
    return True

def check_redis_connection():
    """Verificar conexión con Redis"""
    try:
        url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        client = redis.Redis.from_url(url)
        client.ping()

        # Estadísticas
        info = client.info()
        print(f"✅ Redis OK - Conexiones: {info['connected_clients']}")
        return True
    except Exception as e:
        print(f"❌ Redis ERROR: {e}")
        return False

def check_api_endpoints():
    """Verificar endpoints de la API"""
    base_url = "http://localhost:8000"

    try:
        # Health check
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Health OK")
        else:
            print(f"❌ API Health ERROR: {response.status_code}")
            return False

        # Test invoke
        payload = {"input": "test", "session_id": "diag_test"}
        response = requests.post(f"{base_url}/invoke", json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ API Invoke OK")
        else:
            print(f"❌ API Invoke ERROR: {response.status_code}")
            return False

        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ API Connection ERROR: {e}")
        return False

def check_agent_configs():
    """Verificar configuración de agentes"""
    agents_dir = Path("agents")
    if not agents_dir.exists():
        print("❌ Directorio agents no existe")
        return False

    valid_agents = 0
    for agent_dir in agents_dir.iterdir():
        if agent_dir.is_dir() and not agent_dir.name.startswith('.'):
            config_file = agent_dir / "config.json"
            if config_file.exists():
                try:
                    with open(config_file) as f:
                        json.load(f)
                    valid_agents += 1
                except:
                    print(f"❌ Config inválida: {agent_dir.name}")
            else:
                print(f"❌ Falta config.json: {agent_dir.name}")

    if valid_agents >= 4:  # triage, quote, contract, support
        print(f"✅ Agentes OK: {valid_agents} configurados")
        return True
    else:
        print(f"❌ Pocos agentes: {valid_agents} (esperados: 4+)")
        return False

def main():
    print("🔍 Diagnóstico Completo del Sistema de Agentes Conversacionales")
    print("=" * 60)

    checks = [
        ("Variables de Entorno", check_environment),
        ("Conexión Redis", check_redis_connection),
        ("Configuración de Agentes", check_agent_configs),
        ("API Endpoints", check_api_endpoints),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n🔍 Verificando: {name}")
        result = check_func()
        results.append(result)

    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL:")

    if all(results):
        print("🎉 ¡Sistema completamente funcional!")
        print("\n📝 Recomendaciones:")
        print("   - Monitorea los logs regularmente")
        print("   - Configura backups de Redis")
        print("   - Revisa límites de APIs externas")
    else:
        print("⚠️  Sistema con problemas - revisa errores arriba")
        print("\n🔧 Acciones recomendadas:")
        print("   - Corrige las configuraciones faltantes")
        print("   - Reinicia servicios necesarios")
        print("   - Revisa la documentación de troubleshooting")

if __name__ == "__main__":
    main()
```

Ejecuta: `python diagnose_system.py`

También disponible: `python test_api.py` para tests básicos de API.

#### Métricas de Performance
```bash
# Instalar monitoring básico
pip install psutil

# Ver métricas del sistema
python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Disk: {psutil.disk_usage(\"/\").percent}%')
"
```

---

## 🤝 Contribuir

### 📋 Proceso de Contribución

1. **🍴 Fork** el repositorio
2. **🌿 Crea** una rama descriptiva: `git checkout -b feature/nueva-funcionalidad`
3. **💻 Desarrolla** siguiendo las guías de estilo
4. **🧪 Testea** exhaustivamente
5. **📝 Documenta** tus cambios
6. **🔄 Commit** con mensajes claros: `git commit -m "feat: agregar nueva funcionalidad X"`
7. **📤 Push** tu rama: `git push origin feature/nueva-funcionalidad`
8. **🔀 Pull Request** con descripción detallada

### 🎯 Estándares de Código

#### Python Style Guide
```python
# ✅ Bien
def calculate_premium(vehicle_type: str, age: int) -> float:
    """Calculate insurance premium based on vehicle and driver age."""
    base_rate = VEHICLE_RATES.get(vehicle_type, 100)
    age_discount = max(0, (age - 25) * 2)
    return base_rate - age_discount

# ❌ Mal
def calc_prem(v, a):  # Sin tipos, nombre poco descriptivo
    return VEHICLE_RATES.get(v, 100) - max(0, (a - 25) * 2)  # Sin comentarios
```

#### Commit Messages
```
✅ feat: agregar soporte para seguros de vida
✅ fix: corregir cálculo de descuentos por edad
✅ docs: actualizar guía de configuración de Google Sheets
✅ refactor: simplificar lógica de validación de datos

❌ cambio algo
❌ fix bug
❌ update
```

### 🏷️ Labels para Issues/PRs

- `🐛 bug` - Error que necesita corrección
- `✨ feature` - Nueva funcionalidad
- `📚 documentation` - Cambios en documentación
- `🔧 maintenance` - Mantenimiento/refactorización
- `🚀 enhancement` - Mejora de funcionalidad existente
- `❓ question` - Pregunta o discusión

### 🏆 Reconocimientos

¡Gracias a todos los contribuidores!

<a href="https://github.com/ssillerom/tfm-valley-mds10-muppy/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=ssillerom/tfm-valley-mds10-muppy" />
</a>

---

## 📞 Soporte y Comunidad

### 🆘 Canales de Soporte

#### 📧 Email
- **Soporte Técnico**: [GitHub Issues](https://github.com/ssillerom/tfm-valley-mds10-muppy/issues)
- **Consultas Generales**: [GitHub Discussions](https://github.com/ssillerom/tfm-valley-mds10-muppy/discussions)

#### 💬 Comunidad
- [GitHub Discussions](https://github.com/ssillerom/tfm-valley-mds10-muppy/discussions) - Para preguntas y discusiones
- [GitHub Issues](https://github.com/ssillerom/tfm-valley-mds10-muppy/issues) - Para reportar bugs

#### 📖 Documentación
- **Documentación Técnica**: Este README.md
- **Guía de Desarrollo**: Sección "Guía de Desarrollo" en este documento
- **API Reference**: Sección "API Reference" en este documento

### 🌍 Comunidad

- **🐛 Reportar Issues**: [GitHub Issues](https://github.com/ssillerom/tfm-valley-mds10-muppy/issues)
- **💡 Sugerencias**: [GitHub Discussions](https://github.com/ssillerom/tfm-valley-mds10-muppy/discussions)
- **🤝 Colaborar**: Ver sección [Contribuir](#-contribuir)

### 📋 Checklist para Issues

Antes de reportar un problema, verifica:

- [ ] ¿Es un problema reproducible?
- [ ] ¿Has revisado la documentación?
- [ ] ¿Es un problema conocido? (busca en Issues)
- [ ] ¿Tienes logs or screenshots?
- [ ] ¿Has probado con la última versión?

**Template para bugs:**
```
## Descripción del Problema
[Describe claramente qué ocurre]

## Pasos para Reproducir
1. [Paso 1]
2. [Paso 2]
3. [Resultado esperado vs real]

## Información del Sistema
- OS: [Windows/Linux/macOS]
- Python: [versión]
- Redis: [versión]
- Browser: [si aplica]

## Logs
[Adjunta logs relevantes]
```

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

<div align="center">

**Proyecto académico desarrollado con ❤️**

---

[⬆️ Volver al Inicio](#-sistema-de-agentes-conversacionales-para-seguros)

</div>

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
