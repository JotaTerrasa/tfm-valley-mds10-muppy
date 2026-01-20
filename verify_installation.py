#!/usr/bin/env python3
"""
Script de verificación de instalación para el Sistema de Agentes Mapfre
Ejecuta: python verify_installation.py
"""

import sys
import os
from pathlib import Path
import subprocess

def check_python_version():
    """Verificar versión de Python"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Se requiere 3.8+")
        return False

def check_requirements():
    """Verificar que todas las dependencias están instaladas"""
    required_packages = [
        'fastapi', 'uvicorn', 'redis', 'pydantic', 'langchain', 'langgraph'
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package}")

    return len(missing) == 0

def check_env_file():
    """Verificar archivo .env"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ Archivo .env no encontrado")
        return False

    required_vars = ['API_KEY_SECRET', 'REDIS_URL']
    missing_vars = []

    try:
        with open(env_path, 'r') as f:
            content = f.read()

        for var in required_vars:
            if var not in content:
                missing_vars.append(var)

        if missing_vars:
            print(f"❌ Variables faltantes en .env: {', '.join(missing_vars)}")
            return False

        print("✅ Archivo .env configurado")
        return True
    except Exception as e:
        print(f"❌ Error leyendo .env: {e}")
        return False

def check_redis():
    """Verificar conexión con Redis"""
    try:
        import redis
        client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        client.ping()
        print("✅ Redis conectado")
        return True
    except Exception as e:
        print(f"❌ Redis no disponible: {e}")
        print("   Asegúrate de que Redis esté ejecutándose")
        return False

def check_app_import():
    """Verificar que se puede importar la aplicación"""
    try:
        # Agregar directorio raíz al path
        sys.path.insert(0, os.getcwd())
        import app.main
        print("✅ Aplicación importable")
        return True
    except Exception as e:
        print(f"❌ Error importando aplicación: {e}")
        return False

def main():
    print("🔍 Verificando instalación del Sistema de Agentes Mapfre...\n")

    checks = [
        ("🐍 Versión de Python", check_python_version),
        ("📦 Dependencias", check_requirements),
        ("⚙️  Archivo .env", check_env_file),
        ("💾 Redis", check_redis),
        ("🚀 Aplicación", check_app_import),
    ]

    results = []
    for name, check_func in checks:
        print(f"{name}:")
        result = check_func()
        results.append(result)
        print()

    if all(results):
        print("🎉 ¡Instalación completa y correcta!")
        print("\nPuedes ejecutar:")
        print("  uvicorn app.main:app --reload")
        print("\nY probar en: http://localhost:8000")
        print("\n📖 Consulta el README.md para más detalles")
    else:
        print("❌ Hay problemas en la instalación")
        print("\n🔧 Revisa los errores arriba y consulta el README.md")
        print("   Sección: 'Instalación y Configuración'")
        sys.exit(1)

if __name__ == "__main__":
    main()