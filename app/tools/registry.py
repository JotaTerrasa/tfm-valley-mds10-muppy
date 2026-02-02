# Placeholder para herramientas de seguros
# Las herramientas se implementarán según necesidades específicas

def get_tool_by_name(tool_name: str):
    """
    Busca y devuelve una herramienta del registro por su nombre.
    """
    from .insurance_tools import (
        get_insurance_products,
        get_cross_sell_suggestions,
        calculate_quote,
        create_payment_link,
        save_insurance_lead,
        get_policy_summary,
        get_billing_details,
        create_claim_ticket,
        get_claim_status,
        request_policy_change,
        update_contact_details
    )
    
    TOOL_REGISTRY = {
        "get_insurance_products": get_insurance_products,
        "get_cross_sell_suggestions": get_cross_sell_suggestions,
        "calculate_quote": calculate_quote,
        "create_payment_link": create_payment_link,
        "save_insurance_lead": save_insurance_lead,
        "get_policy_summary": get_policy_summary,
        "get_billing_details": get_billing_details,
        "create_claim_ticket": create_claim_ticket,
        "get_claim_status": get_claim_status,
        "request_policy_change": request_policy_change,
        "update_contact_details": update_contact_details,
    }
    
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Herramienta '{tool_name}' no encontrada en el registro. "
                         f"Asegúrate de que está definida en tools/registry.py")
    return TOOL_REGISTRY[tool_name]
