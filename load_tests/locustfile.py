"""
Stress test: simula 500 usuarios contra el backend.
Escenarios: health check (rápido) y /invoke con mensajes típicos de triage.

Uso (con el backend en marcha en http://localhost:8000):
  locust -f load_tests/locustfile.py --host=http://localhost:8000
  Luego abrir http://localhost:8089 y arrancar con 500 usuarios, rampa 50/s.

O sin UI (500 usuarios, rampa 50/s, 5 min):
  locust -f load_tests/locustfile.py --host=http://localhost:8000 --headless -u 500 -r 50 -t 5m
"""
import random
from locust import HttpUser, task, between


# Mensajes cortos de triage para no saturar el LLM en pruebas de carga
INVOKE_INPUTS = [
    "Hola",
    "Buenos días",
    "Quiero información",
    "Necesito ayuda",
    "Cotización",
    "Seguro de coche",
]


class BackendUser(HttpUser):
    """Simula un usuario que hace health y/o invoke."""

    wait_time = between(1, 3)

    @task(weight=2)
    def health(self):
        self.client.get("/health", name="/health")

    @task(weight=8)
    def invoke_short(self):
        payload = {"input": random.choice(INVOKE_INPUTS)}
        self.client.post(
            "/invoke",
            json=payload,
            name="/invoke (triage)",
            timeout=60,
        )
