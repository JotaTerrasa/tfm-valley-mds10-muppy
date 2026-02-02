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
- Backend de agentes ejecutándose en local (por defecto en `http://localhost:8000`)

## 🚀 Arranque rápido (solo frontend)

```bash
npm install
npm run dev
```

Luego abre `http://localhost:5173`.

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

Repositorio backend: `tfm-valley-mds10-muppy` (ruta local en tu máquina).

Pasos típicos:

```bash
# En la carpeta del backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> Nota: el backend requiere **Redis** y la variable `REDIS_URL` configurada.

## ⚙️ Configuración

Actualmente, la URL del backend está fija en:

- `src/App.jsx` → `const API_URL = 'http://localhost:8000'`

Si necesitas apuntar a otro host/puerto, cambia ese valor.

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

- Confirma que el backend responde: `GET http://localhost:8000/health`
- Verifica CORS en el backend (debe permitir `http://localhost:5173` o `*`)
- Asegúrate de que **Redis** está levantado y `REDIS_URL` está bien configurada (el backend no arranca si falta)

### El chat no muestra respuesta al iniciar

- El auto‑inicio llama a `/invoke` con `input: "Hola"`. Si el backend está caído, verás un mensaje de error.

## 📦 Deploy (opción simple)

Genera el build:

```bash
npm run build
```

El output queda en `dist/`. Puedes servirlo con cualquier hosting estático (Nginx, GitHub Pages, Vercel, etc.).  
Si despliegas el frontend, recuerda **ajustar `API_URL`** para apuntar al backend desplegado.

## 🔒 Seguridad

Este frontend no gestiona autenticación por defecto. Si expones el backend públicamente, considera:

- Autenticación/autorizar requests (API key/JWT)
- Limitar `allow_origins` en CORS

## 📄 Licencia

Pendiente de definir.
