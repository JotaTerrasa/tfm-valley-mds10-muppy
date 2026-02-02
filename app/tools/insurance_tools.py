"""
Herramientas específicas para el agente de seguros.
Estas son implementaciones placeholder que deben ser adaptadas según las necesidades reales.
"""
from typing import Dict, Any, List
import json

def get_insurance_products(insurance_type: str) -> List[Dict[str, Any]]:
    """
    Obtiene los productos de seguro disponibles para un tipo específico.
    
    Args:
        insurance_type: Tipo de seguro ("auto", "hogar", "vida", "salud")
    
    Returns:
        Lista de productos disponibles
    """
    # TODO: Implementar conexión real con catálogo de productos
    print(f"--- [Insurance Tools] Obteniendo productos para: {insurance_type} ---")
    
    # Datos de ejemplo
    mock_products = {
        "auto": [
            {
                "product_id": "auto_basico",
                "name": "Seguro de Auto Básico",
                "coverage_level": "básico",
                "annual_premium": 300.0,
                "description": "Cobertura básica de responsabilidad civil"
            },
            {
                "product_id": "auto_completo",
                "name": "Seguro de Auto Completo",
                "coverage_level": "completo",
                "annual_premium": 600.0,
                "description": "Cobertura completa con asistencia en carretera"
            }
        ],
        "hogar": [
            {
                "product_id": "hogar_basico",
                "name": "Seguro de Hogar Básico",
                "coverage_level": "básico",
                "annual_premium": 200.0,
                "description": "Protección básica del hogar"
            }
        ]
    }
    
    return mock_products.get(insurance_type, [])


def get_cross_sell_suggestions(primary_policy_type: str) -> List[Dict[str, Any]]:
    """
    Sugiere productos complementarios para ventas cruzadas según la póliza principal del cliente.
    Estructura compatible con CrossSellOffer (Pydantic).

    Args:
        primary_policy_type: Tipo de póliza actual ("auto", "hogar", "moto", "vida", "salud")

    Returns:
        Lista de ofertas sugeridas con product_id, product_type, coverage_level, annual_premium, monthly_premium, reason
    """
    print(f"--- [Insurance Tools] Sugerencias cross-sell para póliza: {primary_policy_type} ---")

    # Reglas de cross-sell: qué sugerir según la póliza principal
    suggestions_map = {
        "auto": [
            {"product_id": "hogar_basico", "product_type": "hogar", "coverage_level": "básico", "annual_premium": 180.0, "monthly_premium": 15.0, "reason": "Protege tu hogar con un descuento por tener ya auto con Mapfre"},
            {"product_id": "vida_basico", "product_type": "vida", "coverage_level": "básico", "annual_premium": 120.0, "monthly_premium": 10.0, "reason": "Protección para tu familia con condiciones preferentes"},
        ],
        "hogar": [
            {"product_id": "auto_basico", "product_type": "auto", "coverage_level": "terceros", "annual_premium": 280.0, "monthly_premium": 23.33, "reason": "Descuento por tener hogar con nosotros"},
            {"product_id": "vida_basico", "product_type": "vida", "coverage_level": "básico", "annual_premium": 120.0, "monthly_premium": 10.0, "reason": "Protección familiar complementaria"},
        ],
        "moto": [
            {"product_id": "auto_basico", "product_type": "auto", "coverage_level": "terceros", "annual_premium": 280.0, "monthly_premium": 23.33, "reason": "Si tienes coche, descuento por multi-póliza"},
            {"product_id": "hogar_basico", "product_type": "hogar", "coverage_level": "básico", "annual_premium": 180.0, "monthly_premium": 15.0, "reason": "Protección del hogar con ventaja por ser cliente"},
        ],
        "vida": [
            {"product_id": "hogar_basico", "product_type": "hogar", "coverage_level": "básico", "annual_premium": 180.0, "monthly_premium": 15.0, "reason": "Complementa la protección de tu familia"},
            {"product_id": "salud_basico", "product_type": "salud", "coverage_level": "básico", "annual_premium": 350.0, "monthly_premium": 29.17, "reason": "Cobertura de salud con condiciones preferentes"},
        ],
        "salud": [
            {"product_id": "vida_basico", "product_type": "vida", "coverage_level": "básico", "annual_premium": 120.0, "monthly_premium": 10.0, "reason": "Protección adicional para tu familia"},
        ],
    }
    primary = primary_policy_type.lower().strip()
    return suggestions_map.get(primary, [])


def calculate_quote(insurance_type: str, coverage_level: str, additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Calcula una cotización para un seguro. Redirige a la función específica según el tipo.
    
    Args:
        insurance_type: Tipo de seguro ("auto", "hogar", "moto")
        coverage_level: Nivel de cobertura
        additional_data: Datos adicionales (edad, ubicación, etc.)
    
    Returns:
        Diccionario con la cotización calculada
    """
    print(f"--- [Insurance Tools] Calculando cotización: {insurance_type}, {coverage_level} ---")
    
    if additional_data is None:
        additional_data = {}
    
    # Redirigir a la función específica según el tipo de seguro
    if insurance_type in ["auto", "coche"]:
        return calculate_quote_auto(coverage_level, additional_data)
    elif insurance_type == "hogar":
        return calculate_quote_hogar(coverage_level, additional_data)
    elif insurance_type == "moto":
        return calculate_quote_moto(coverage_level, additional_data)
    else:
        return {
            "error": f"Tipo de seguro '{insurance_type}' no soportado",
            "tipos_disponibles": ["auto", "hogar", "moto"]
        }


def calculate_quote_hogar(coverage_level: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula cotización para seguro de HOGAR.
    
    Factores considerados:
    - Tipo de vivienda (piso, casa, apartamento)
    - Metros cuadrados
    - Propietario vs alquiler
    - Código postal (zona)
    - Nivel de cobertura
    
    Args:
        coverage_level: "basica" o "completa"
        data: {
            "tipo_vivienda": "piso" | "casa" | "apartamento",
            "metros_cuadrados": int,
            "es_propietario": bool,
            "codigo_postal": str
        }
    """
    # Precios base según tipo de vivienda (€/año)
    precios_base = {
        "piso": 150,
        "casa": 220,
        "chalet": 220,
        "apartamento": 130
    }
    
    tipo_vivienda = data.get("tipo_vivienda", "piso").lower()
    metros = data.get("metros_cuadrados", 80)
    es_propietario = data.get("es_propietario", True)
    codigo_postal = data.get("codigo_postal", "00000")
    
    # 1. Precio base según tipo de vivienda
    precio = precios_base.get(tipo_vivienda, 150)
    
    # 2. Ajuste por metros cuadrados (+5€ por cada 10m²)
    precio += (metros // 10) * 5
    
    # 3. Ajuste por propiedad (alquiler = -20% porque no cubre continente)
    if not es_propietario:
        precio *= 0.80
    
    # 4. Ajuste por zona geográfica
    zonas_premium = ["28", "08", "48", "41"]  # Madrid, Barcelona, Bilbao, Sevilla
    if codigo_postal[:2] in zonas_premium:
        precio *= 1.15
    
    # 5. Ajuste por nivel de cobertura
    multiplicadores_cobertura = {
        "basica": 1.0,
        "básica": 1.0,
        "completa": 1.8,
        "todo_riesgo": 1.8
    }
    multiplicador = multiplicadores_cobertura.get(coverage_level.lower(), 1.0)
    precio_final = round(precio * multiplicador, 2)
    
    # Calcular desglose
    return {
        "insurance_type": "hogar",
        "coverage_level": coverage_level,
        "annual_premium": precio_final,
        "monthly_premium": round(precio_final / 12, 2),
        "currency": "EUR",
        "detalles": {
            "tipo_vivienda": tipo_vivienda,
            "metros_cuadrados": metros,
            "es_propietario": es_propietario,
            "codigo_postal": codigo_postal
        },
        "coberturas_incluidas": [
            "Incendio y explosión",
            "Daños por agua",
            "Robo y hurto",
            "Responsabilidad civil",
            "Asistencia en el hogar 24h"
        ] if coverage_level.lower() in ["completa", "todo_riesgo"] else [
            "Incendio y explosión",
            "Daños por agua",
            "Responsabilidad civil básica"
        ]
    }


def calculate_quote_auto(coverage_level: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula cotización para seguro de AUTO/COCHE.
    
    Factores considerados:
    - Edad del conductor
    - Antigüedad del vehículo
    - Código postal
    - Nivel de cobertura (terceros, terceros_ampliado, todo_riesgo)
    
    Args:
        coverage_level: "terceros" | "terceros_ampliado" | "todo_riesgo"
        data: {
            "marca": str,
            "modelo": str,
            "año_vehiculo": int,
            "fecha_nacimiento": str (YYYY-MM-DD),
            "codigo_postal": str
        }
    """
    from datetime import datetime
    
    # Precios base según cobertura (€/año)
    precios_base = {
        "terceros": 280,
        "terceros_ampliado": 420,
        "todo_riesgo": 650,
        "basico": 280,
        "básico": 280,
        "completo": 650
    }
    
    año_vehiculo = data.get("año_vehiculo", 2020)
    fecha_nacimiento = data.get("fecha_nacimiento", "1990-01-01")
    codigo_postal = data.get("codigo_postal", "00000")
    marca = data.get("marca", "").lower()
    
    # Calcular edad del conductor
    try:
        año_nacimiento = int(fecha_nacimiento.split("-")[0])
        edad_conductor = datetime.now().year - año_nacimiento
    except:
        edad_conductor = 35
    
    # 1. Precio base según cobertura
    precio = precios_base.get(coverage_level.lower(), 400)
    
    # 2. Ajuste por edad del conductor
    if edad_conductor < 25:
        precio *= 1.50  # Jóvenes +50%
    elif edad_conductor < 30:
        precio *= 1.20  # +20%
    elif edad_conductor > 65:
        precio *= 1.15  # Mayores +15%
    
    # 3. Ajuste por antigüedad del vehículo
    antiguedad = datetime.now().year - año_vehiculo
    if antiguedad > 15:
        precio *= 1.25  # Vehículos muy antiguos
    elif antiguedad > 10:
        precio *= 1.10
    elif antiguedad < 2:
        precio *= 1.05  # Vehículos nuevos (más valor)
    
    # 4. Ajuste por zona geográfica
    zonas_premium = ["28", "08", "48", "41", "46"]  # Madrid, Barcelona, Bilbao, Sevilla, Valencia
    if codigo_postal[:2] in zonas_premium:
        precio *= 1.12
    
    # 5. Ajuste por marca (algunas marcas más caras de reparar)
    marcas_premium = ["bmw", "mercedes", "audi", "porsche", "tesla"]
    if marca in marcas_premium:
        precio *= 1.20
    
    precio_final = round(precio, 2)
    
    return {
        "insurance_type": "auto",
        "coverage_level": coverage_level,
        "annual_premium": precio_final,
        "monthly_premium": round(precio_final / 12, 2),
        "currency": "EUR",
        "detalles": {
            "marca": data.get("marca", ""),
            "modelo": data.get("modelo", ""),
            "año_vehiculo": año_vehiculo,
            "edad_conductor": edad_conductor,
            "codigo_postal": codigo_postal
        },
        "coberturas_incluidas": _get_coberturas_auto(coverage_level)
    }


def _get_coberturas_auto(coverage_level: str) -> List[str]:
    """Devuelve las coberturas incluidas según el nivel."""
    coberturas = {
        "terceros": [
            "Responsabilidad civil obligatoria",
            "Responsabilidad civil voluntaria (50M€)",
            "Defensa jurídica",
            "Asistencia en viaje"
        ],
        "terceros_ampliado": [
            "Responsabilidad civil obligatoria",
            "Responsabilidad civil voluntaria (50M€)",
            "Defensa jurídica",
            "Asistencia en viaje",
            "Lunas",
            "Robo",
            "Incendio",
            "Fenómenos atmosféricos"
        ],
        "todo_riesgo": [
            "Responsabilidad civil obligatoria",
            "Responsabilidad civil voluntaria (50M€)",
            "Defensa jurídica",
            "Asistencia en viaje",
            "Lunas",
            "Robo",
            "Incendio",
            "Fenómenos atmosféricos",
            "Daños propios",
            "Vehículo de sustitución"
        ]
    }
    return coberturas.get(coverage_level.lower(), coberturas["terceros"])


def calculate_quote_moto(coverage_level: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula cotización para seguro de MOTO.
    
    Factores considerados:
    - Cilindrada
    - Edad del conductor
    - Antigüedad del vehículo
    - Código postal
    - Nivel de cobertura
    
    Args:
        coverage_level: "terceros" | "terceros_ampliado" | "todo_riesgo" | "basica" | "lider"
        data: {
            "marca": str,
            "modelo": str,
            "cilindrada": int (cc),
            "año_vehiculo": int,
            "fecha_nacimiento": str (YYYY-MM-DD),
            "codigo_postal": str
        }
    """
    from datetime import datetime
    
    # Precios base según cobertura (€/año)
    precios_base = {
        "terceros": 180,
        "basica": 180,
        "básica": 180,
        "terceros_ampliado": 280,
        "todo_riesgo": 450,
        "lider": 380,
        "líder": 380,
        "diez": 320,
        "completo": 450
    }
    
    cilindrada = data.get("cilindrada", 125)
    año_vehiculo = data.get("año_vehiculo", 2020)
    fecha_nacimiento = data.get("fecha_nacimiento", "1990-01-01")
    codigo_postal = data.get("codigo_postal", "00000")
    
    # Calcular edad del conductor
    try:
        año_nacimiento = int(fecha_nacimiento.split("-")[0])
        edad_conductor = datetime.now().year - año_nacimiento
    except:
        edad_conductor = 35
    
    # 1. Precio base según cobertura
    precio = precios_base.get(coverage_level.lower(), 250)
    
    # 2. Ajuste por cilindrada
    if cilindrada <= 125:
        precio *= 0.70  # Motos pequeñas -30%
    elif cilindrada <= 500:
        precio *= 1.0   # Base
    elif cilindrada <= 750:
        precio *= 1.30  # +30%
    else:
        precio *= 1.60  # Motos grandes +60%
    
    # 3. Ajuste por edad del conductor (motos más restrictivo)
    if edad_conductor < 25:
        precio *= 1.70  # Jóvenes +70%
    elif edad_conductor < 30:
        precio *= 1.30  # +30%
    elif edad_conductor > 60:
        precio *= 1.20  # Mayores +20%
    
    # 4. Ajuste por antigüedad del vehículo
    antiguedad = datetime.now().year - año_vehiculo
    if antiguedad > 12:
        precio *= 1.20
    elif antiguedad > 8:
        precio *= 1.10
    
    # 5. Ajuste por zona geográfica
    zonas_premium = ["28", "08", "48", "41", "46"]
    if codigo_postal[:2] in zonas_premium:
        precio *= 1.10
    
    precio_final = round(precio, 2)
    
    return {
        "insurance_type": "moto",
        "coverage_level": coverage_level,
        "annual_premium": precio_final,
        "monthly_premium": round(precio_final / 12, 2),
        "currency": "EUR",
        "detalles": {
            "marca": data.get("marca", ""),
            "modelo": data.get("modelo", ""),
            "cilindrada": cilindrada,
            "año_vehiculo": año_vehiculo,
            "edad_conductor": edad_conductor,
            "codigo_postal": codigo_postal
        },
        "coberturas_incluidas": _get_coberturas_moto(coverage_level)
    }


def _get_coberturas_moto(coverage_level: str) -> List[str]:
    """Devuelve las coberturas incluidas según el nivel para moto."""
    coberturas = {
        "terceros": [
            "Responsabilidad civil obligatoria (70M€ personas, 15M€ bienes)",
            "Defensa jurídica (600€)",
            "Asistencia en viaje"
        ],
        "basica": [
            "Responsabilidad civil obligatoria (70M€ personas, 15M€ bienes)",
            "RC suplementaria (50M€)",
            "Accidentes conductor (8.000€ fallecimiento)",
            "Defensa jurídica (600€)",
            "Asistencia en viaje"
        ],
        "terceros_ampliado": [
            "Responsabilidad civil obligatoria",
            "RC suplementaria (50M€)",
            "Accidentes conductor",
            "Defensa jurídica",
            "Asistencia en viaje",
            "Robo",
            "Incendio"
        ],
        "todo_riesgo": [
            "Responsabilidad civil obligatoria",
            "RC suplementaria (50M€)",
            "Accidentes conductor",
            "Defensa jurídica",
            "Asistencia en viaje",
            "Robo",
            "Incendio",
            "Daños propios",
            "Equipamiento"
        ]
    }
    return coberturas.get(coverage_level.lower(), coberturas.get("basica", []))

def create_payment_link(amount: float, session_id: str, description: str = "Pago de seguro") -> Dict[str, Any]:
    """
    Crea un link de pago para la contratación del seguro.
    
    Args:
        amount: Monto a pagar
        session_id: ID de sesión
        description: Descripción del pago
    
    Returns:
        Diccionario con el link de pago
    """
    # TODO: Implementar integración real con Stripe u otro proveedor de pagos
    print(f"--- [Insurance Tools] Creando link de pago: {amount} EUR para sesión {session_id} ---")
    
    return {
        "payment_link": f"https://payment.example.com/pay/{session_id}",
        "amount": amount,
        "currency": "EUR",
        "status": "pending"
    }

def save_insurance_lead(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Guarda un lead de seguro en la base de datos.
    
    Args:
        lead_data: Datos del lead a guardar
    
    Returns:
        Confirmación del guardado
    """
    # TODO: Implementar guardado real en Google Sheets
    print(f"--- [Insurance Tools] Guardando lead: {lead_data.get('id', 'unknown')} ---")
    
    return {
        "status": "saved",
        "lead_id": lead_data.get("id"),
        "timestamp": "2025-01-20T00:00:00Z"
    }

def search_insurance_info(query: str, insurance_type: str = None) -> str:
    """
    Busca información sobre seguros en la base de conocimientos.
    Usa esta herramienta cuando el cliente pregunte sobre:
    - Coberturas específicas de un seguro
    - Condiciones generales
    - Exclusiones o limitaciones
    - Documentación necesaria
    - Precios orientativos o modalidades
    
    Args:
        query: Pregunta o tema a buscar (ej: "coberturas todo riesgo coche")
        insurance_type: Tipo de seguro para filtrar ("coche", "hogar", "moto"). Opcional.
    
    Returns:
        Información relevante encontrada en los documentos de seguros.
    """
    from app.rag.vector_store import search_insurance_info as rag_search
    
    print(f"--- [Insurance Tools] Buscando info: '{query}' (tipo: {insurance_type}) ---")
    
    result = rag_search(query, insurance_type=insurance_type, k=3)
    return result

def get_policy_summary(policy_number: str, id_number: str = None) -> Dict[str, Any]:
    """
    Obtiene un resumen básico de una póliza existente.
    
    Args:
        policy_number: Número de póliza
        id_number: Documento de identidad opcional
    
    Returns:
        Resumen de póliza con datos básicos y coberturas
    """
    print(f"--- [Insurance Tools] Consultando póliza: {policy_number} ---")
    masked_id = (id_number[-4:] if id_number else "N/A")
    return {
        "policy_number": policy_number,
        "policy_status": "active",
        "insured_name": "Cliente Mapfre",
        "id_last_digits": masked_id,
        "coverage_summary": [
            "Responsabilidad civil",
            "Asistencia en carretera",
            "Defensa jurídica"
        ],
        "renewal_date": "2025-12-01",
        "payment_status": "al_corriente"
    }

def get_billing_details(policy_number: str) -> Dict[str, Any]:
    """
    Obtiene información de facturación de una póliza.
    
    Args:
        policy_number: Número de póliza
    
    Returns:
        Detalles de facturación y próximos pagos
    """
    print(f"--- [Insurance Tools] Consultando facturación de póliza: {policy_number} ---")
    return {
        "policy_number": policy_number,
        "next_payment_date": "2025-11-15",
        "amount_due": 45.90,
        "currency": "EUR",
        "payment_method": "domiciliación",
        "outstanding_balance": 0.0
    }

def create_claim_ticket(policy_number: str, description: str, incident_date: str = None) -> Dict[str, Any]:
    """
    Registra un siniestro nuevo.
    
    Args:
        policy_number: Número de póliza
        description: Descripción del siniestro
        incident_date: Fecha del incidente (opcional)
    
    Returns:
        Confirmación con número de siniestro
    """
    print(f"--- [Insurance Tools] Creando siniestro para póliza: {policy_number} ---")
    suffix = policy_number[-4:] if policy_number else "0000"
    claim_id = f"CLM-{suffix}-001"
    return {
        "claim_id": claim_id,
        "policy_number": policy_number,
        "status": "opened",
        "incident_date": incident_date or "2025-01-20",
        "next_steps": "Un gestor revisará el caso en las próximas 24 horas."
    }

def get_claim_status(claim_id: str) -> Dict[str, Any]:
    """
    Consulta el estado de un siniestro existente.
    
    Args:
        claim_id: Número de siniestro
    
    Returns:
        Estado y última actualización
    """
    print(f"--- [Insurance Tools] Consultando estado de siniestro: {claim_id} ---")
    return {
        "claim_id": claim_id,
        "status": "in_review",
        "last_update": "2025-01-22",
        "estimated_resolution": "2025-02-05"
    }

def request_policy_change(policy_number: str, change_type: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Registra una solicitud de cambio o cancelación de póliza.
    
    Args:
        policy_number: Número de póliza
        change_type: Tipo de cambio solicitado
        details: Detalles adicionales del cambio
    
    Returns:
        Confirmación de la solicitud
    """
    print(f"--- [Insurance Tools] Solicitud de cambio '{change_type}' para póliza: {policy_number} ---")
    return {
        "policy_number": policy_number,
        "change_type": change_type,
        "status": "received",
        "request_id": f"REQ-{policy_number[-4:] if policy_number else '0000'}"
    }

def update_contact_details(policy_number: str, email: str = None, phone_number: str = None, address: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Actualiza datos de contacto de una póliza.
    
    Args:
        policy_number: Número de póliza
        email: Email actualizado
        phone_number: Teléfono actualizado
        address: Dirección actualizada
    
    Returns:
        Confirmación de actualización
    """
    print(f"--- [Insurance Tools] Actualizando datos de contacto para póliza: {policy_number} ---")
    return {
        "policy_number": policy_number,
        "status": "updated",
        "updated_fields": {
            "email": email,
            "phone_number": phone_number,
            "address": address
        }
    }
