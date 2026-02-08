# Comandos rápidos – Dónde está cada cosa

Para que Cursor (o cualquier persona) sepa cómo levantar el proyecto y las pruebas sin buscar.

---

## Levantar el backend

**Ubicación del script:** `scripts/run/start-backend.ps1`

```powershell
.\scripts\run\start-backend.ps1
```

Alternativa con .bat (desde CMD o doble clic): `scripts\run\start-backend.bat`

El backend queda en **http://localhost:8000**. Health: `GET http://localhost:8000/health`.

---

## Levantar el stress test (500 usuarios)

**Ubicación del script:** `scripts/run/run-stress.ps1`

Requisito: **backend ya en marcha** (arrancar antes con el script de arriba).

```powershell
.\scripts\run\run-stress.ps1
```

O con Locust en modo UI: `locust -f load_tests/locustfile.py --host=http://localhost:8000` y abrir http://localhost:8089.

---

## Resumen

| Qué quiero hacer | Script |
|------------------|--------|
| Levantar el backend | `scripts/run/start-backend.ps1` |
| Stress test (backend ya corriendo) | `scripts/run/run-stress.ps1` |
| Sincronizar repo con Sergio | `scripts/git/sync-con-sergio.sh` |
| Convertir PDFs de data/ a MD | `python scripts/data/convert_to_md.py` |

Todos los scripts están dentro de **scripts/**; ver [scripts/README.md](../scripts/README.md) para la estructura completa.
