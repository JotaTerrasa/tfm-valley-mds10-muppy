# Plan de Pruebas E2E del Grafo (Ida y Vuelta)

Objetivo: validar que el flujo entre agentes funciona en avance y retroceso, que las correcciones del usuario no rompen el estado, y que pagos online siguen desactivados.

## Precondiciones

- Stack levantado con Docker:
  - `docker compose up -d`
- Backend accesible en `http://localhost:8000`
- Frontend accesible en `http://localhost:5173` (opcional para prueba manual UI)
- Login activo con usuario/password del `.env`

## Cómo validar cada caso

Puedes validar por:
- UI (chat en frontend), o
- API (`POST /invoke`) mirando `structured_data` en la respuesta.

Campos clave a revisar:
- `structured_data.route`
- `structured_data.active_agent_key`
- `structured_data.intent`
- `structured_data.next_agent` (si aparece)
- `structured_data.collected_data` (si hay captura de datos)
- `structured_data.payment_status` y `payment_link` (pagos desactivados)

---

## Bloque A - Triage y enrutado inicial

### Caso A1 - Saludo neutro
1. Usuario: `Hola`
2. Esperado:
   - `route = triage`
   - `active_agent_key = triage_agent`
   - No deriva a otro agente.

### Caso A2 - Cotización directa
1. Usuario: `Quiero cotizar un seguro de coche`
2. Esperado:
   - `intent = cotizar`
   - `route = cotizar`
   - `active_agent_key = quote_agent`

### Caso A3 - Soporte sin datos obligatorios
1. Usuario: `Tengo un problema con mi seguro`
2. Esperado:
   - `intent = soporte`
   - Permanece en `triage` hasta tener `cliente_id` y `tipo_seguro`
   - No deriva a `support_agent` todavía.

### Caso A4 - Soporte con datos completos
1. Usuario: `Soy Ana Pérez, DNI 12345678Z, problema con mi seguro de hogar`
2. Esperado:
   - `intent = soporte`
   - `route = soporte` (o ruta de soporte interna)
   - `active_agent_key = support_agent`

---

## Bloque B - Flujo quote_agent (avance y retroceso)

### Caso B1 - Captura progresiva sin salto de pasos
1. Inicia cotización (A2).
2. Responde datos uno a uno.
3. Esperado:
   - Pide información faltante de forma secuencial.
   - `collected_data` se va completando sin perder campos previos.

### Caso B2 - Corrección de dato
1. Tras dar un dato: `Mi código postal es 28001`
2. Corrige: `Perdona, es 28013`
3. Esperado:
   - Se usa el último valor (`28013`) en estado.
   - No se reinicia toda la conversación.

### Caso B3 - Retroceso explícito desde cotización
1. Usuario: `Volvamos atrás, quiero cambiar a seguro de hogar`
2. Esperado:
   - El flujo acepta la corrección y continúa sin error 500.
   - El estado refleja el cambio de intención/tipo de seguro.
   - No queda bloqueado en datos inválidos del paso anterior.

### Caso B4 - Handoff a contratación
1. Usuario: `Me interesa esta opción, quiero contratar`
2. Esperado:
   - Se marca transición (`next_agent = contract_agent` en ese turno)
   - Siguiente interacción entra en `contract_agent`.

---

## Bloque C - Flujo contract_agent (sin pago online)

### Caso C1 - Captura de datos de contratación
1. Completa nombre, fecha nac., email, teléfono, identificación y dirección.
2. Esperado:
   - `route` avanza de `data_capture` a `verification` cuando proceda.
   - `missing_fields` disminuye progresivamente.

### Caso C2 - Corrección en verificación
1. En resumen final de verificación: `El email está mal, cámbialo a ...`
2. Esperado:
   - Actualiza `collected_data.email`
   - Permite volver a confirmar sin romper estado.

### Caso C3 - Paso payment_node con pagos desactivados
1. Usuario: `Perfecto, quiero pagar ahora`
2. Esperado:
   - Mensaje indica que pago online no está disponible.
   - `payment_link = null` (o ausente, pero nunca URL nueva)
   - `payment_status = pending`
   - El flujo sigue a `final_summary`.

### Caso C4 - Finalización correcta sin cobro online
1. Esperado:
   - `route = final_summary`
   - `status = new` al cerrar
   - No aparece `payment_status = successful` generado por el agente.

---

## Bloque D - Soporte y cambios de ruta

### Caso D1 - Policy lookup
1. Usuario: `Quiero revisar mi póliza 12345`
2. Esperado:
   - Ruta a `policy_lookup` o soporte equivalente.
   - Si falta póliza, pide `policy_number`.

### Caso D2 - Cambio de tema en soporte
1. Tras estar en claims: `Mejor, necesito actualizar mi teléfono`
2. Esperado:
   - Cambia a `update_data` (o ruta equivalente).
   - No queda “anclado” en la ruta anterior.

### Caso D3 - Derivación humana
1. Usuario: `Quiero hablar con una persona`
2. Esperado:
   - `route = human_handoff`
   - Mensaje empático + solicitud de contacto si aplica.

---

## Bloque E - Cross-sell

### Caso E1 - Descubrimiento y oferta
1. Usuario: `Ya tengo coche con vosotros, ¿qué más me ofrecéis?`
2. Esperado:
   - `intent = cross_sell`
   - Avanza a descubrimiento/oferta.

### Caso E2 - Acepta oferta y vuelve a cotización
1. Usuario: `Me interesa la opción de hogar`
2. Esperado:
   - Transición a `quote_agent` cuando corresponda.
   - Sin mención a pago online.

---

## Criterios de aceptación globales

Se considera OK si:
- No hay errores 500 en ninguno de los casos.
- Las correcciones del usuario prevalecen sobre datos anteriores.
- Hay transición correcta entre agentes (triage -> quote/support/contract/cross_sell).
- El retroceso ("volver atrás", "cambiar") no rompe sesión.
- No se generan enlaces de pago ni confirmaciones de pago exitoso.
- El estado mantiene consistencia (`route`, `intent`, `active_agent_key`, `collected_data`).

## Comandos útiles (PowerShell)

Login:

```powershell
$login = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/auth/login" -Body @{username="TU_USUARIO";password="TU_PASSWORD"}
$token = $login.access_token
$headers = @{ Authorization = "Bearer $token" }
```

Invoke:

```powershell
$sid = "test-grafo-manual-1"
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/invoke" -Headers $headers -ContentType "application/json" -Body (@{input="Hola";session_id=$sid} | ConvertTo-Json)
```

---

## Resultado de ejecución (2026-02-15)

Estado final de validación manual end-to-end sobre entorno Docker local:

| Bloque | Estado | Observaciones |
|---|---|---|
| A - Triage | PASS | Enrutado correcto a cotizar/soporte/cross-sell y reinicio de flujo correcto. |
| B - Quote | PASS | Captura secuencial, cotización estable, retroceso y handoff a contratación correctos. |
| C - Contract | PASS | Captura + verificación correctas, pagos online bloqueados según requisito. |
| D - Soporte (policy lookup, billing, claims, policy_change, update_data, handoff) | PASS | Se aplicaron fixes de enrutado para evitar bucles en handoff y priorizar subflujos operativos. |
| E - Cross-sell | PASS | Oferta y transición a cotización correctas tras arreglar registro de tool de sugerencias. |

### Incidencias detectadas y corregidas durante la validación

1. **Error 500 al pasar a cotización** por validación de `additional_data` en tool-calls.
   - Mitigación: fallback robusto en estrategia para no romper request por schema de tools.
2. **Filtrado de salida interna** (`<tool_code>` o JSON en crudo visible al usuario).
   - Mitigación: limpieza de `tool_code` y extracción de JSON final sin mostrarlo al usuario.
3. **Latencia alta en cotización** por reconstrucción de índice RAG en cada consulta.
   - Mitigación: preservación de `documents_metadata.json` en `chroma_db` y ajuste de montaje Docker.
4. **Bucle en soporte hacia `human_handoff`** incluso con datos suficientes.
   - Mitigación: enrutado determinista por intención (claims/billing/policy_change/update/policy_lookup) y normalización `soporte -> support`.
5. **Fallo en cross-sell** (`'function' object has no attribute 'name'`).
   - Mitigación: `get_cross_sell_suggestions` registrado correctamente como `@tool`.

### Pendientes menores (UX, no bloqueantes)

- Reducir mensajes de “te conecto con soporte” en subflujos que ya pueden resolver directamente.
- Incluir `request_id` en texto al usuario para solicitudes de cambio de póliza (actualmente funcional, pero mejorable para trazabilidad).

