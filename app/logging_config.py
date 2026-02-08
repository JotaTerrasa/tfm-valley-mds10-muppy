"""
Logging con correlación a trazas (request_id, trace_id, span_id).
Permite cruzar logs con Arize AX Tracing Projects y agregadores de logs.
"""
import logging
import json
import os
from contextvars import ContextVar
from typing import Any, Dict

# ContextVar para propagar request_id en toda la petición (async-safe)
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_trace_context() -> Dict[str, str]:
    """Obtiene trace_id y span_id del span actual de OpenTelemetry (si existe)."""
    out: Dict[str, str] = {}
    try:
        from opentelemetry import trace
        span = trace.get_current_span()
        if span.is_recording():
            ctx = span.get_span_context()
            if ctx.trace_id != 0:
                out["trace_id"] = format(ctx.trace_id, "032x")
            if ctx.span_id != 0:
                out["span_id"] = format(ctx.span_id, "016x")
    except Exception:
        pass
    return out


class TraceCorrelationFilter(logging.Filter):
    """
    Añade request_id, trace_id y span_id a cada LogRecord
    para correlacionar logs con trazas en Arize y con X-Request-ID.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        rid = request_id_ctx.get()
        setattr(record, "request_id", rid or "")
        ctx = get_trace_context()
        setattr(record, "trace_id", ctx.get("trace_id", ""))
        setattr(record, "span_id", ctx.get("span_id", ""))
        return True


class JsonLogFormatter(logging.Formatter):
    """
    Formato JSON (una línea por evento) para ingest en agregadores
    o para correlacionar por request_id/trace_id.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_dict: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if getattr(record, "request_id", None):
            log_dict["request_id"] = record.request_id
        if getattr(record, "trace_id", None):
            log_dict["trace_id"] = record.trace_id
        if getattr(record, "span_id", None):
            log_dict["span_id"] = record.span_id
        if record.exc_info:
            log_dict["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_dict, ensure_ascii=False)


def setup_correlation_logging(
    use_json: bool | None = None,
    level: str | int = logging.INFO,
) -> None:
    """
    Configura el logging de la app: filtro de correlación y opcionalmente formato JSON.
    Llamar una vez al arranque (p. ej. en startup de FastAPI).

    Args:
        use_json: True = formato JSON, False = formato legible. Si None, se usa env LOG_FORMAT=json.
        level: Nivel de logging (default INFO).
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Evitar duplicar el filtro si se llama varias veces
    for f in root.filters:
        if isinstance(f, TraceCorrelationFilter):
            return

    root.addFilter(TraceCorrelationFilter())

    if not root.handlers:
        h = logging.StreamHandler()
        h.setLevel(level)
        root.addHandler(h)

    if use_json is None:
        use_json = os.getenv("LOG_FORMAT", "").strip().lower() == "json"

    if use_json:
        for h in root.handlers:
            h.setFormatter(JsonLogFormatter())
    else:
        # Formato legible; añade request_id y trace_id al inicio cuando existan
        class HumanFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                prefix = ""
                if getattr(record, "request_id", None):
                    prefix = f"[{record.request_id}] "
                if getattr(record, "trace_id", None):
                    tid = record.trace_id[:16] + "..." if len(record.trace_id) > 16 else record.trace_id
                    prefix += f"[trace={tid}] "
                base = super().format(record)
                if prefix:
                    base = prefix + base
                return base
        for h in root.handlers:
            if not isinstance(h.formatter, JsonLogFormatter):
                h.setFormatter(HumanFormatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))
    return


def set_request_id(request_id: str | None) -> None:
    """Fija el request_id en el contexto de la petición (llamar desde middleware)."""
    request_id_ctx.set(request_id)


def clear_request_id() -> None:
    """Limpia el request_id del contexto (llamar al finalizar la petición)."""
    request_id_ctx.set(None)
