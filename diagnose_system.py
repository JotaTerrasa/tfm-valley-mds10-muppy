#!/usr/bin/env python3
"""
Diagnóstico completo del sistema de agentes
Ejecuta: python diagnose_system.py
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

def check_dependencies():
    """Verificar dependencias críticas"""
    critical_deps = [
        'fastapi', 'uvicorn', 'redis', 'pydantic',
        'langchain', 'langgraph', 'requests'
    ]

    missing = []
    for dep in critical_deps:
        try:
            __import__(dep.replace('-', '_'))
        except ImportError:
            missing.append(dep)

    if missing:
        print(f"❌ Dependencias faltantes: {', '.join(missing)}")
        return False

    print("✅ Dependencias OK")
    return True

def main():
    print("🔍 Diagnóstico Completo del Sistema de Agentes Mapfre")
    print("=" * 60)

    checks = [
        ("Dependencias", check_dependencies),
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
        print("   - Ejecuta tests regularmente: python test_api.py")
    else:
        print("⚠️  Sistema con problemas - revisa errores arriba")
        print("\n🔧 Acciones recomendadas:")
        print("   - Corrige las configuraciones faltantes")
        print("   - Reinicia servicios necesarios")
        print("   - Revisa la documentación de troubleshooting")
        print("   - Ejecuta: python verify_installation.py")

if __name__ == "__main__":
    main()