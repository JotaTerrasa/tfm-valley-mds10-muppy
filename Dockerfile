# Backend Mapfre - FastAPI + RAG (ChromaDB + Ollama)
FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema para pymupdf y ChromaDB
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmupdf-dev \
    mupdf-tools \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY agents ./agents
COPY data ./data

# ChromaDB y .env se montan por volumen o env en runtime
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
