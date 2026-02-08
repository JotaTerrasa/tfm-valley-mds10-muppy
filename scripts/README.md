# Scripts del proyecto

Todos los scripts están en la carpeta `scripts/`. Los de **run/** pueden ejecutarse desde cualquier directorio (cambian automáticamente a la raíz del proyecto).

---

## Estructura

```
scripts/
├── README.md           # Este archivo
├── export_graph_png.py # Grafo global (PNG) → agents/global_graph.png
├── run/                # Levantar backend y pruebas de carga
│   ├── start-backend.ps1
│   ├── start-backend.bat
│   └── run-stress.ps1
├── git/                # Repositorio y sincronización
│   └── sync-con-sergio.sh
└── data/               # Conversión de datos
    └── convert_to_md.py
```

---

## Run: backend y stress test

| Script | Qué hace | Cómo ejecutar |
|--------|----------|----------------|
| **run/start-backend.ps1** | Arranca el backend FastAPI (puerto 8000) | `.\scripts\run\start-backend.ps1` |
| **run/start-backend.bat** | Igual, desde CMD o doble clic | `scripts\run\start-backend.bat` |
| **run/run-stress.ps1** | Stress test Locust (500 usuarios, 5 min). Backend debe estar en marcha. | `.\scripts\run\run-stress.ps1` |

Requisitos: `.venv` en la raíz del proyecto. Para stress test, Locust ya está en `requirements.txt`. Variables opcionales para run-stress: `STRESS_HOST`, `STRESS_USERS`, `STRESS_RATE`, `STRESS_TIME`.

---

## Git / repositorio

| Script | Qué hace | Cómo ejecutar |
|--------|----------|----------------|
| **git/sync-con-sergio.sh** | Sincroniza la rama Dev con el repo upstream (Sergio) | `./scripts/git/sync-con-sergio.sh` (Linux/macOS, desde la raíz) |

Requisitos: tener configurado el remote `upstream`. Ver [docs/SETUP_MI_REPO.md](../docs/SETUP_MI_REPO.md).

---

## Datos

| Script | Qué hace | Cómo ejecutar |
|--------|----------|----------------|
| **data/convert_to_md.py** | Convierte todos los PDFs en `data/` a Markdown | `python scripts/data/convert_to_md.py` (desde la raíz) |

Requisitos: `pip install pymupdf` (ya está en `requirements.txt`).

---

## Grafo (diagrama)

| Script | Qué hace | Cómo ejecutar |
|--------|----------|----------------|
| **export_graph_png.py** | Genera `agents/global_graph.png` con el grafo de orquestación (triage → quote/contract/support) | `python scripts/export_graph_png.py` (desde la raíz) |
