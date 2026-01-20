from typing import Dict, Optional

def calculate_request_cost(token_usage: Dict, pricing_info: Optional[Dict] = None) -> float:
    """
    Calcula el coste de una petición basándose en el uso de tokens y la información de precios.
    
    Args:
        token_usage: Diccionario con 'input_tokens' y 'output_tokens'
        pricing_info: Diccionario con 'input_per_million' y 'output_per_million'
    
    Returns:
        Coste total en dólares
    """
    if not pricing_info:
        return 0.0
    
    input_tokens = token_usage.get("input_tokens", 0)
    output_tokens = token_usage.get("output_tokens", 0)
    
    input_per_million = pricing_info.get("input_per_million", 0)
    output_per_million = pricing_info.get("output_per_million", 0)
    
    input_cost = (input_tokens / 1_000_000) * input_per_million
    output_cost = (output_tokens / 1_000_000) * output_per_million
    
    return input_cost + output_cost
