# Muppy AI — Frontend (Web Chat)

Frontend web para interactuar con el sistema multiagente **Muppy** (Mapfre Seguros). Incluye una interfaz de chat moderna y conecta con el backend (FastAPI) a través del endpoint `POST /invoke`.

## ✨ Funcionalidades

- **Chat en tiempo real** con UI moderna (dark theme, animaciones, typing indicator).
- **Auto‑inicio**: al abrir el chat, el agente de triage responde automáticamente (sin escribir).
- **Indicador de conexión** con el backend (`/health`).
- **Agente activo visible** (triage / quote / contract / support).
- **Nueva conversación** (reinicia sesión y estado del chat).

## 🧱 Stack

- **React** + **Vite**
- **ESLint**
- Backend esperado: **FastAPI** (repo del sistema de agentes)

## ✅ Requisitos

- **Node.js** 18+ (recomendado) y **npm**
- Backend de agentes ejecutándose (por defecto en `http://localhost:8000`)

## 🚀 Arranque rápido (solo frontend)

```bash
cp .env.example .env   # primera vez: crear .env desde plantilla
npm install
npm run dev
```

Luego abre la URL que muestre Vite (p. ej. `http://localhost:5173`).

### Variables de entorno (`frontend/.env`)

| Variable | Descripción |
|----------|-------------|
| `VITE_API_URL` | URL del backend. En local suele ser `http://localhost:8000`. Si el backend corre en otro puerto (p. ej. 8001), pon aquí `http://localhost:8001`. |

Ejemplo `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

## 🔌 Conexión con el backend (Muppy Agents)

Este frontend llama a:

- **Health check**: `GET http://localhost:8000/health`
- **Chat**: `POST http://localhost:8000/invoke`

### Payload (ejemplo)

```json
{
  "input": "Hola, quiero un seguro de auto",
  "session_id": "session_123",
  "metadata": {
    "source": "web_frontend"
  }
}
```

### Respuesta esperada (resumen)

El frontend utiliza principalmente:

- `response` (texto para mostrar)
- `session_id`
- `structured_data.active_agent_key` (para mostrar el agente activo)
- `request_cost` (si viene informado)

## ▶️ Ejecutar el backend (referencia)

Desde la **raíz del proyecto** (no desde `frontend/`):

```bash
source venv/bin/activate   # Linux/macOS. En Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El backend necesita en la raíz un `.env` con `GOOGLE_API_KEY` (API key de Google AI Studio). No usa Redis. Opcionalmente, para que los agentes consulten documentación de seguros (RAG), instala [Ollama](https://ollama.com), ejecuta `ollama pull mxbai-embed-large` y, si Ollama no está en localhost:11434, define `OLLAMA_BASE_URL` en el `.env` del backend.

## ⚙️ Configuración

La URL del backend se configura con la variable de entorno **`VITE_API_URL`** en `frontend/.env` (por defecto `http://localhost:8000`). El frontend la usa en `src/App.jsx`. Si el backend corre en otro host o puerto, edita `frontend/.env`.

## 🧪 Scripts útiles

```bash
npm run dev       # Desarrollo (Vite)
npm run build     # Build de producción
npm run preview   # Preview del build
npm run lint      # Linter
```

## 🧩 Estructura del proyecto

```txt
.
├─ public/
├─ src/
│  ├─ App.jsx      # UI y lógica del chat
│  ├─ App.css      # Estilos del chat
│  ├─ index.css    # Estilos globales
│  └─ main.jsx     # Entry
├─ index.html
├─ vite.config.js
└─ package.json
```

## 🛠️ Troubleshooting

### “Desconectado” en el indicador

- Confirma que el backend responde: `GET <VITE_API_URL>/health` (p. ej. `http://localhost:8000/health`)
- Verifica que `VITE_API_URL` en `frontend/.env` coincida con la URL y puerto donde corre el backend
- Verifica CORS en el backend (debe permitir el origen del frontend, p. ej. `http://localhost:5173`)

### El chat no muestra respuesta al iniciar

- El auto‑inicio llama a `/invoke` con `input: "Hola"`. Si el backend está caído, verás un mensaje de error.

## 📦 Deploy (opción simple)

Genera el build:

```bash
npm run build
```

El output queda en `dist/`. Puedes servirlo con cualquier hosting estático (Nginx, GitHub Pages, Vercel, etc.).  
Si despliegas el frontend, configura **`VITE_API_URL`** en el entorno de build para apuntar al backend desplegado.

## 🔒 Seguridad

Este frontend no gestiona autenticación por defecto. Si expones el backend públicamente, considera:

- Autenticación/autorizar requests (API key/JWT)
- Limitar `allow_origins` en CORS

## 📄 Licencia

Pendiente de definir.
