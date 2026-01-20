from .generative_strategy import GenerativeStrategy
from .state_machine_strategy import StateMachineStrategy

STRATEGY_REGISTRY = {
    "generative": GenerativeStrategy,
    "state_machine": StateMachineStrategy,
}

def get_strategy(strategy_name: str):
    """
    Busca y devuelve la clase de la estrategia solicitada.
    Si no la encuentra, devuelve la estrategia por defecto.
    """
    return STRATEGY_REGISTRY.get(strategy_name, GenerativeStrategy)
