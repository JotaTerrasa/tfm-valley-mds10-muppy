# Conectar el backend a Arize AX (Tracing Projects)

El proyecto usa **Arize OTEL** para enviar trazas a **Arize AX**. Así el proyecto y las trazas aparecen en la pantalla **Tracing Projects** del dashboard.

## Variables en `.env`

En la raíz del proyecto, en tu `.env`:

```env
ARIZE_SPACE_ID=U3BhY2U6OTMyOk1tZm8=
ARIZE_PROJECT_NAME=mapfre-muppy
ARIZE_API_KEY=tu-api-key-de-arize
# Si tu dashboard es EU (app.eu-west-1a.arize.com), usa el endpoint EU:
ARIZE_COLLECTOR_ENDPOINT=https://otlp.eu-west-1a.arize.com/v1
```

- **ARIZE_SPACE_ID**: ID de tu Space en Arize (p. ej. "TFM Mapfre").
- **ARIZE_PROJECT_NAME**: nombre del proyecto que verás en Tracing Projects.
- **ARIZE_API_KEY**: API key desde Settings → API Keys en Arize.
- **ARIZE_COLLECTOR_ENDPOINT** (opcional): Si entras en Arize por **app.eu-west-1a.arize.com** (EU), define esta variable con la URL de arriba. Si tu cuenta es US (app.arize.com), no la pongas para usar el endpoint por defecto `otlp.arize.com`.

Reinicia el backend después de guardar. Las trazas se enviarán a Arize AX y verás el proyecto en **Observe → Tracing Projects**.

---

## (Opcional) Arize Phoenix Cloud

Si en su lugar quisieras usar **Phoenix OTEL** (endpoint Phoenix Cloud):

## 1. Crear cuenta y espacio en Arize

1. Entra en [Arize Phoenix](https://app.phoenix.arize.com) y crea una cuenta si no la tienes.
2. Crea un **Space** (o usa uno existente) y anota el **nombre del space** (slug que aparece en la URL, p. ej. `mi-org/mi-proyecto` o similar).
3. En **Settings → API Keys** crea una **API Key** y cópiala.

## 2. Variables de entorno en `.env`

En la raíz del proyecto, en tu archivo `.env`, añade o descomenta:

```env
PHOENIX_ENABLED=true
PHOENIX_PROJECT_NAME=mapfre-muppy
PHOENIX_COLLECTOR_ENDPOINT=https://app.phoenix.arize.com/s/TU_SPACE_NAME
PHOENIX_API_KEY=tu-api-key-de-arize
```

- **TU_SPACE_NAME**: sustituir por el slug de tu Space en Arize (lo ves en la URL del dashboard).
- **PHOENIX_API_KEY**: la API key que generaste en Settings.
- **PHOENIX_PROJECT_NAME**: nombre del proyecto que verás en Phoenix (puedes usar `mapfre-muppy` u otro).

## 3. Reiniciar el backend

Tras guardar el `.env`, reinicia el backend:

```powershell
.\scripts\run\start-backend.ps1
```

o:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 4. Comprobar en Arize

1. Genera algo de tráfico (por ejemplo, envía mensajes en el chat del front).
2. En [app.phoenix.arize.com](https://app.phoenix.arize.com) abre tu Space y el proyecto `PHOENIX_PROJECT_NAME`.
3. Deberías ver trazas de las llamadas a Gemini, agentes y herramientas.

## Solo Phoenix local (sin Arize Cloud)

Si quieres trazas solo en local (sin enviar a Arize):

- Deja **PHOENIX_COLLECTOR_ENDPOINT** y **PHOENIX_API_KEY** sin definir o comentadas.
- Con **PHOENIX_ENABLED=true** las trazas se envían al colector por defecto (localhost:4317). Para verlas necesitas levantar Phoenix en local (p. ej. `phoenix serve`).

## Referencia

- [Setup OTEL - Phoenix](https://docs.arize.com/phoenix/tracing/how-to-tracing/setup-tracing/setup-using-phoenix-otel)
- [API Keys - Phoenix](https://docs.arize.com/phoenix/settings/api-keys)
- [Environments - Phoenix](https://docs.arize.com/phoenix/environments)
