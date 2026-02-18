# Muppy AI — Frontend (Web Chat)

Frontend web para interactuar con el sistema multiagente **Muppy** (Mapfre Seguros). Incluye una interfaz de chat moderna y conecta con el backend (FastAPI) a través del endpoint `POST /invoke`.

**Desplegado en Vercel:** [https://tfm-valley-mds10-muppy.vercel.app/](https://tfm-valley-mds10-muppy.vercel.app/) — Para que funcione, el backend debe estar expuesto con **ngrok** y en Vercel debe estar configurado `VITE_API_URL` con la URL del túnel (ver README raíz, § 5.5).

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

## 📦 Deploy en Vercel (mismo repo, solo esta carpeta)

Puedes desplegar **solo el frontend** desde este mismo repositorio:

1. En [vercel.com](https://vercel.com) → **Add New** → **Project** → elige este repo.
2. En **Root Directory** pon: **`frontend`** (así Vercel usa solo esta carpeta y no el backend).
3. Añade la variable **`VITE_API_URL`** con la URL pública de tu backend.
4. **Deploy**.

Para que el deploy de producción use la rama **Dev**: en el proyecto → **Settings** → **Git** → **Production Branch**, pon **`Dev`** y guarda.

Vercel tirará del repo pero construirá y desplegará únicamente lo que hay en `frontend/`. El `vercel.json` de esta carpeta ya está configurado para Vite.

### Frontend en Vercel con backend local (ngrok)

Si el backend corre en tu máquina y lo expones con **ngrok**:

1. Levanta el backend: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` (desde la raíz del proyecto).
2. Crea el túnel (elige una):
   - Opción A (recomendado, Docker Compose): configura `NGROK_AUTHTOKEN` y `NGROK_URL` en `.env` (raíz) y levanta: `docker compose --profile tunnels up -d ngrok`
   - Opción B (ngrok CLI): `ngrok http 8000 --url charmaine-endoperidial-creepingly.ngrok-free.app`
3. En Vercel → **Settings** → **Environment Variables**: define `VITE_API_URL` = `https://charmaine-endoperidial-creepingly.ngrok-free.app` (con `https://`; sin esquema las peticiones pueden dar 404).
4. Redeploy el frontend.

El frontend envía la cabecera `ngrok-skip-browser-warning: true` en todas las peticiones al backend para evitar la página de aviso de ngrok. Mientras ngrok y el backend estén en marcha, el chat desplegado en Vercel usará tu backend local.

## 📦 Build local (opción simple)

Genera el build:

```bash
npm run build
```

El output queda en `dist/`. Puedes servirlo con cualquier hosting estático (Nginx, GitHub Pages, etc.).  
Si despliegas el frontend, configura **`VITE_API_URL`** en el entorno de build para apuntar al backend desplegado.

## 🧪 Pagos de prueba (Stripe)

Para validar el flujo E2E del pago desde el propio frontend (botón "Pago de prueba"):

- En el **backend** (entorno): `TEST_PAYMENTS_ENABLED=true` (solo en desarrollo).
- En el **frontend** (Vercel o `.env` local): `VITE_ENABLE_TEST_PAYMENTS=true`.

El botón crea un checkout de Stripe (modo test) de bajo importe y abre el pago en una pestaña nueva. Al completar el pago, esa pestaña se cierra automáticamente (best effort) y la confirmación aparece en la pestaña del chat.

## 🔒 Seguridad

Este frontend no gestiona autenticación por defecto. Si expones el backend públicamente, considera:

- Autenticación/autorizar requests (API key/JWT)
- Limitar `allow_origins` en CORS

## 📄 Licencia

Pendiente de definir.
