"""
Compuerta de calidad (Quality Gate): exige un mínimo de precisión (p. ej. 90%)
antes de aceptar un cambio o desplegar. Útil en CI/CD.
"""
import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("QualityGate")

# Umbral por defecto: 90% de precisión mínima para aceptar el cambio
DEFAULT_PRECISION_THRESHOLD = 0.90


def run_evaluation():
    """
    Ejecuta el framework de evaluación (p. ej. Arize Phoenix, DeepEval).
    Debe devolver la métrica de precisión en el rango [0, 1].

    Returns:
        float: Precisión obtenida (0.0 a 1.0).
    """
    logger.info("Iniciando evaluación del chatbot...")

    # TODO: Conectar con resultados reales de Arize, DeepEval, etc.
    # Por ahora simulamos una métrica (cambiar para probar que falla el gate)
    current_precision = 0.95  # 95% en el ejemplo

    return current_precision


def check_threshold(score: float, threshold: float = DEFAULT_PRECISION_THRESHOLD) -> bool:
    """
    Compuerta de calidad: si la precisión no alcanza el umbral, falla el proceso.

    Args:
        score: Valor de la métrica (precisión) en [0, 1].
        threshold: Umbral mínimo requerido (p. ej. 0.90 = 90%).

    Returns:
        True si score >= threshold, False en caso contrario.
    """
    if not (0 <= score <= 1):
        raise ValueError(f"score debe estar entre 0 y 1, recibido: {score}")
    if not (0 <= threshold <= 1):
        raise ValueError(f"threshold debe estar entre 0 y 1, recibido: {threshold}")

    logger.info("Precisión obtenida: %.2f%%", score * 100)
    logger.info("Umbral requerido: %.2f%%", threshold * 100)

    if score >= threshold:
        logger.info("ÉXITO: El sistema cumple el estándar de calidad. Se acepta el cambio.")
        return True
    logger.error(
        "FALLO: La precisión (%.2f%%) es inferior al umbral (%.2f%%). Se bloquea el cambio.",
        score * 100,
        threshold * 100,
    )
    return False


def main() -> int:
    """Ejecuta la evaluación y la compuerta. Devuelve 0 si pasa, 1 si falla."""
    threshold = float(os.environ.get("QUALITY_PRECISION_THRESHOLD", DEFAULT_PRECISION_THRESHOLD))
    if not (0 <= threshold <= 1):
        logger.error("QUALITY_PRECISION_THRESHOLD debe estar entre 0 y 1. Usando %.2f.", DEFAULT_PRECISION_THRESHOLD)
        threshold = DEFAULT_PRECISION_THRESHOLD

    score = run_evaluation()
    passed = check_threshold(score, threshold=threshold)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())