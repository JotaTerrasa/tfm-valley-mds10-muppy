# Stress test – 500 usuarios

Pruebas de carga con **Locust** contra el backend: simula 500 usuarios que hacen health checks y llamadas a `/invoke`.

## Requisitos

- Backend en marcha (ej. `.\scripts\run\start-backend.ps1`).
- Python con Locust instalado:

```bash
pip install locust
```

O desde la raíz del proyecto:

```bash
pip install -r requirements.txt
```

## Uso

### Modo UI (recomendado la primera vez)

1. Arranca el backend en otro terminal.
2. Ejecuta Locust:

```bash
locust -f load_tests/locustfile.py --host=http://localhost:8000
```

3. Abre en el navegador: **http://localhost:8089**.
4. Configura:
   - **Number of users:** 500  
   - **Ramp up (users/s):** 50 (subida en ~10 s hasta 500).  
   - **Run time:** 2m o 5m (o sin límite y parar a mano).
5. Pulsa "Start swarming". Verás RPS, latencias (mediana, P95, P99), fallos y gráficas.

### Modo headless (CI o terminal)

Sin interfaz web, todo por línea de comandos:

Desde la raíz del proyecto (con backend en marcha):

```powershell
.\scripts\run\run-stress.ps1
```

O con Locust directamente:

```bash
locust -f load_tests/locustfile.py --host=http://localhost:8000 --headless -u 500 -r 50 -t 5m
```

- `-u 500`: 500 usuarios concurrentes.  
- `-r 50`: rampa de 50 usuarios por segundo hasta 500.  
- `-t 5m`: duración 5 minutos.

Al final Locust imprime un resumen: total de peticiones, RPS, latencias (median, P95, P99), % de fallos.  
Estos datos alimentan las **métricas core** 1, 2, 3 y 6 (ver `docs/METRICAS_CORE.md`).

## Escenarios en el locustfile

- **Health (peso 2):** GET `/health` — comprueba que el servicio responde.
- **Invoke (peso 8):** POST `/invoke` con mensajes cortos de triage (Hola, Cotización, etc.) — cada usuario abre una sesión nueva (sin `session_id`).

Así ~80 % de las peticiones son `/invoke` y ~20 % `/health`. Puedes cambiar los pesos en `locustfile.py` (atributo `weight` en cada `@task`).

## Dónde apuntar el host

Por defecto `--host=http://localhost:8000`. Para otro entorno:

```bash
locust -f load_tests/locustfile.py --host=https://tu-backend.ejemplo.com ...
```

## Relación con las métricas core

Tras una corrida de stress test puedes obtener:

| Métrica        | Dónde verla en Locust / informe |
|----------------|----------------------------------|
| Latencia P50   | Median (ms) en el resumen        |
| Latencia P95   | 95% (ms)                         |
| Tasa de error  | Failures / Total requests        |
| Throughput (RPS)| Requests/s (RPS)               |

Guarda el informe o exporta CSV/HTML si Locust está configurado para ello, para comparar antes/después de cambios.
