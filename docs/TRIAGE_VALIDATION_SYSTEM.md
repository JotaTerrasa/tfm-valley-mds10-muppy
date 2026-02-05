# Sistema de Validación y Bloqueo Inteligente del Triage Agent

## 📋 Descripción General

El sistema de Triage ha sido reforzado con un mecanismo de **bloqueo inteligente** que diferencia entre dos tipos de flujos de usuario:

### FLUJO 1: Usuarios NO clientes (Cotización/Contratación)
- **Requiere**: Solo `tipo_seguro`
- **No requiere**: `cliente_id` (son potenciales clientes nuevos)
- **Agentes destino**: `quote_agent`, `contract_agent`

### FLUJO 2: Clientes existentes (Soporte/Asistencia)
- **Requiere**: `cliente_id` + `tipo_seguro`
- **Validación estricta**: Ambos datos son obligatorios INTELIGENTE** que:

- Diferencia entre dos flujos: NO clientes vs Clientes existentes
- Para **cotizar/contratar**: Solo requiere `tipo_seguro`
- Para **soporte**: Requiere `cliente_id` + `tipo_seguro`
- Solicita educadamente los datos faltantes según el flujo
- Reconoce datos en cualquier orden o formato

**Campos JSON añadidos:**
```json
{
  "cliente_id": "DNI/NIE/nombre o null",
  "tipo_seguro": "auto|moto|hogar|vida|salud o null",
  "datos_completos": false,
  "requiere_cliente_id": false,
  "intent": "cotizar|contratar|soporte|consultar"ier orden o formato

**Campos JSON añadidos:**
```json
{
  "cliente_id": "DNI/NIE/nombre o null",
  "tipo_seguro": "auto|moto|hogar|vida|salud o null",
  "datos_completos": false,
  "next_agent": null
}
```

### 2. Esquema de Datos Actualizado (`structured_outputs.py`)

La clase `AgentState` incluye nuevos campos:

```python
class AgentStpara el sistema de bloqueo inteligente del Triage
    cliente_id: Optional[str] = None
    tipo_seguro: Optional[str] = None
    datos_completos: bool = False  # Validación dinámica según intent
    requiere_cliente_id: bool = False  # True para soporte, False para cotizaro del Triage
    cliente_id: Optional[str] = None
    tipo_seguro: Optional[str] = None
    datos_completos: bool = False  # Guardrail flag
    Inteligente en el Router (`state_machine_strategy.py`)

El método `entry_point_router` implementa validación diferenciada por tipo de intent:

```python
def entry_point_router(self, state: GraphState) -> str:
    # ... código de routing ...
    
    # GUARDRAIL INTELIGENTE: Validación según flujo
    if next_agent and next_agent != default_node:
        
        # FLUJO 1: Cotizar/Contratar - Solo requiere tipo_seguro
        if intent in ["cotizar", "contratar"]:
            if not tipo_seguro:
                # BLOQUEAR transición
                return default_node
        
        # FLUJO 2: Soporte - Requiere cliente_id + tipo_seguro
        elif intent == "soporte" or requiere_cliente_id:
            if not cliente_id or not tipo_seguro:
                # BLOQUEAR transición
                return default_node
    
    FLUJO 1: Usuario NO cliente (Cotización)

```
Usuario: "Quiero información sobre seguros de auto"
→ Triage detecta: intent="cotizar", tipo_seguro="auto"
→ Validación: Solo necesita tipo_seguro ✓
→ Respuesta: "Te conecto con nuestro agente de cotizaciones"
→ Estado: datos_completos=true, deriva a quote_agent
```

### FLUJO 2: Cliente existente (Soporte) - Falta identificación

```
Usuario: "Tengo un problema con mi seguro de auto"
→ Triage detecta: intent="soporte", tipo_seguro="auto", cliente_id=null
→ Validación: Necesita cliente_id ✗
→ Respuesta: "Necesito tu DNI o nombre completo para ayudarte"
→ Estado: Permanece en triage, datos_completos=false
```

### FLUJO 2: Cliente completa identificación

```
Usuario (siguiente mensaje): "Mi DNI es 12345678A"
→ Triage detecta: cliente_id="12345678A", tipo_seguro="auto"
→ Validación: Tiene ambos datos ✓
→ Respuesta: "Perfecto, te conecto con soporte"
→ Estado: datos_completos=true, deriva a support_agent
```

### FLUJO 1: Contratación (NO requiere cliente_id)

```
Usuario: "Quiero contratar un seguro de hogar"
→ Triage detecta: intent="contratar", tipo_seguro="hogar"
→ Validación: Solo necesita tipo_seguro ✓
→ Respuesta: "Te conecto con contratación"
→ Estado: datos_completos=true, deriva a contrace correspondiente"
→ Estado: datos_completos=true, permite transición
```

### Caso 4: Usuario da ambos datos de inicio
```
Usuario: "Hola, soy Juan Pérez DNI 12345678A, tengo un problema con mi seguro de auto"
→ Triage detecta: cliente_id="12345678A", tipo_seguro="auto"
→ Respuesta: "Te conecto con soporte"
→ Estado: datos_completos=true, deriva a support_agent
```

## ⚙️ Características Técnicas

### Doble Capa de Validación

1. **Capa LLM**: El prompt instruye al modelo a no asignar `next_agent` sin datos
2. **Capa de Código (Guardrail)**: El router valida programáticamente antes de permitir transiciones

Esta arquitectura de doble validación garantiza que:
- Incluso si el LLM comete un error, el código lo bloqueará
- Los datos se mantienen consistentes en el contexto
- No hay forma de "saltarse" la validación

### Manejo de Contexto

El sistema mantiene el contexto entre mensajes:
```python
# Si en mensaje 1 el usuario da tipo_seguro
tipo_seguro = "auto"

# Y en mensaje 2 da cliente_id
cliente_id = "12345678A"

# El sistema reconoce que ahora tiene ambos datos
datos_completos = True  # ✅ Permite continuar
```

### Flexibilidad en la Captura

El agente reconoce datos en múltiples formatos:
- **DNI/NIE**: "12345678A", "X1234567L", "mi DNI es 12345678A"
- **Nombres**: "Juan Pérez", "soy María García"
- **Tipos de seguro**: "auto", "coche", "automóvil", "hogar", "casa", "moto", "motocicleta"

## 🚨 Casos de Urgencia

Incluso en casos de urgencia, el sistema mantiene el bloqueo:

```
Usuario: "Necesito una grúa urgente!"
→ Triage detecta urgencia PERO cliente_id=null, tipo_seguro=null
→ Respuesta: "Entiendo la urgencia. Para ayudarte, necesito tu DNI y tipo de seguro"
→ Estado: NO deriva a support_agent hasta tener los datos
```

## 🧪 Testing

Para probar el sistema:

1. **Test de bloqueo inicial:**
   - Mensaje: "Hola"
   - Esperado: Solicita ambos datos, permanece en triage

2. **Test de captura parcial:**
   - Mensaje: "Quiero info de seguro de auto"
   - Esperado: Solicita cliente_id, permanece en triage

3. **Test de captura completa:**
   - Mensaje 1: "Seguro de auto"
   - Mensaje 2: "DNI 12345678A"
   - Esperado: Deriva al agente apropiado

4. **Test de urgencia sin datos:**
   - Mensaje: "Necesito grúa YA!"
   - Esperado: Solicita datos, NO deriva inmediatamente

## 📝 Logs y Debugging

El sistema genera logs detallados:
```
--- [GUARDRAIL] BLOQUEO: Intento de derivar a 'support_agent' sin datos completos. ---
    cliente_id: None, tipo_seguro: auto, datos_completos: False
--- [Router] BLOQUEADO por falta de datos. Permanece en: 'triage_node' ---
```

Esto facilita el debugging y monitoreo del comportamiento del sistema.

## 🔧 Configuración

No requiere configuración adicional. El sistema está integrado en:
- `/agents/triage_agent/triage_agent.prompt`
- `/app/schemas/structured_outputs.py`
- `/app/strategies/state_machine_strategy.py`

## ✅ Beneficios

1. **Seguridad**: No se procesan solicitudes sin identificación clara
2. **Trazabilidad**: Todas las interacciones están vinculadas a un cliente
3. **Mejor UX**: Solicitudes contextualizadas desde el inicio
4. **Prevención de errores**: Evita derivar casos sin información suficiente
5. **Cumplimiento**: Asegura captura de datos obligatorios según políticas
