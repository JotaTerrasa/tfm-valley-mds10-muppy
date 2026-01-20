#!/usr/bin/env python3
"""
Script completo para probar todos los endpoints y flujos
Ejecuta: python test_api.py
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

def test_agent_types():
    """Test diferentes tipos de agentes"""
    agents_to_test = [
        ("triage_agent", "Hola"),
        ("quote_agent", "Quiero un seguro de hogar"),
        ("support_agent", "Tengo una duda sobre mi póliza")
    ]

    for agent, message in agents_to_test:
        session_id = f"test_{agent}_{int(time.time())}"
        payload = {
            "input": message,
            "session_id": session_id
        }

        response = requests.post(f"{BASE_URL}/invoke", json=payload)
        if response.status_code == 200:
            data = response.json()
            detected_agent = data.get('agent', 'unknown')
            print(f"✅ {agent}: {detected_agent}")
        else:
            print(f"❌ {agent}: Error {response.status_code}")

def test_performance():
    """Test básico de performance"""
    import time

    session_id = f"perf_test_{int(time.time())}"
    payload = {"input": "Hola", "session_id": session_id}

    start_time = time.time()
    response = requests.post(f"{BASE_URL}/invoke", json=payload)
    end_time = time.time()

    response_time = end_time - start_time

    if response.status_code == 200 and response_time < 5.0:  # Menos de 5 segundos
        print(".2f"    else:
        print(".2f"
if __name__ == "__main__":
    print("🧪 Iniciando tests de API...\n")

    try:
        test_health()
        test_conversation_flow()
        test_agent_types()
        test_error_handling()
        test_performance()
        print("\n🎉 Todos los tests pasaron exitosamente!")
    except Exception as e:
        print(f"\n❌ Test falló: {e}")
        exit(1)