# Registro central de herramientas de seguros
# Todas las herramientas deben estar registradas aquí para ser accesibles por los agentes

def get_tool_by_name(tool_name: str):
    """
    Busca y devuelve una herramienta del registro por su nombre.
    
    Herramientas disponibles:
    - get_insurance_products: Obtiene productos por tipo de seguro
    - calculate_quote: Calcula cotización
    - create_payment_link: Crea link de pago
    - save_insurance_lead: Guarda lead
    - search_insurance_info: Busca en la base de conocimientos con Metadata Filtering
    - get_policy_summary: Resumen de póliza
    - get_billing_details: Detalles de facturación
    - create_claim_ticket: Crea ticket de reclamación
    - get_claim_status: Estado de reclamación
    - request_policy_change: Solicita cambio de póliza
    - update_contact_details: Actualiza datos de contacto
    """
    from .insurance_tools import (
        get_insurance_products,
        get_cross_sell_suggestions,
        calculate_quote,
        create_payment_link,
        save_insurance_lead,
        search_insurance_info,
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
        "search_insurance_info": search_insurance_info,
        "get_policy_summary": get_policy_summary,
        "get_billing_details": get_billing_details,
        "create_claim_ticket": create_claim_ticket,
        "get_claim_status": get_claim_status,
        "request_policy_change": request_policy_change,
        "update_contact_details": update_contact_details,
    }
    
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Herramienta '{tool_name}' no encontrada en el registro. "
                         f"Disponibles: {list(TOOL_REGISTRY.keys())}")
    return TOOL_REGISTRY[tool_name]


def get_all_tools():
    """Devuelve todas las herramientas disponibles."""
    from .insurance_tools import (
        get_insurance_products,
        calculate_quote,
        create_payment_link,
        save_insurance_lead,
        search_insurance_info,
        get_policy_summary,
        get_billing_details,
        create_claim_ticket,
        get_claim_status,
        request_policy_change,
        update_contact_details
    )
    
    return {
        "get_insurance_products": get_insurance_products,
        "calculate_quote": calculate_quote,
        "create_payment_link": create_payment_link,
        "save_insurance_lead": save_insurance_lead,
        "search_insurance_info": search_insurance_info,
        "get_policy_summary": get_policy_summary,
        "get_billing_details": get_billing_details,
        "create_claim_ticket": create_claim_ticket,
        "get_claim_status": get_claim_status,
        "request_policy_change": request_policy_change,
        "update_contact_details": update_contact_details,
    }
