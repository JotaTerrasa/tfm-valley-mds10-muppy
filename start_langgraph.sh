#!/bin/bash

# Script para iniciar LangGraph Studio con variables de entorno cargadas

# Cambiar al directorio del proyecto
cd "$(dirname "$0")"

# Cargar variables de entorno desde .env
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activar entorno virtual si existe
if [ -d "langchain/bin" ]; then
    source langchain/bin/activate
fi

# Iniciar LangGraph Studio
langgraph dev
