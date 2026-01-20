# Placeholder para herramientas de seguros
# Las herramientas se implementarán según necesidades específicas

def get_tool_by_name(tool_name: str):
    """
    Busca y devuelve una herramienta del registro por su nombre.
    """
    from .insurance_tools import (
        get_insurance_products,
        calculate_quote,
        create_payment_link,
        save_insurance_lead
    )
    
    TOOL_REGISTRY = {
        "get_insurance_products": get_insurance_products,
        "calculate_quote": calculate_quote,
        "create_payment_link": create_payment_link,
        "save_insurance_lead": save_insurance_lead,
    }
    
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Herramienta '{tool_name}' no encontrada en el registro. "
                         f"Asegúrate de que está definida en tools/registry.py")
    return TOOL_REGISTRY[tool_name]
