from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import re
import dateparser

from app.utils.dni_nif import is_valid_nif

class PartialAddress(BaseModel):
    """Dirección parcial para captura progresiva de datos."""
    street_address: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "ES"

class Address(PartialAddress):
    """Dirección completa para validación final."""
    street_address: str
    city: str
    state_province: str
    postal_code: str

class SelectedInsuranceProduct(BaseModel):
    """Producto de seguro seleccionado."""
    product_id: str
    product_type: str  # "auto", "hogar", "vida", "salud", etc.
    coverage_level: str
    price: float
    annual_premium: float

class PartialCollectedData(BaseModel):
    """Datos recopilados parcialmente durante la conversación."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    identification_type: Optional[str] = Field(pattern=r'^(dni|nie|pasaporte)$', default=None)
    identification_number: Optional[str] = None
    address: PartialAddress = Field(default_factory=PartialAddress)
    selected_insurance: Optional[SelectedInsuranceProduct] = None
    vehicle_info: Optional[Dict[str, Any]] = None  # Para seguros de auto
    property_info: Optional[Dict[str, Any]] = None  # Para seguros de hogar

    @field_validator('identification_type', mode='before')
    @classmethod
    def lowercase_identification_type(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.lower()
        return value

    @field_validator('date_of_birth', mode='before')
    @classmethod
    def parse_date_of_birth_flexibly(cls, value: Any) -> Any:
        """Acepta fechas en múltiples formatos."""
        if value is None or isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            candidate = value.strip()
            if not candidate:
                return None
            dt = dateparser.parse(
                candidate,
                languages=['es', 'en'],
                settings={
                    'DATE_ORDER': 'DMY',
                    'PREFER_DAY_OF_MONTH': 'first',
                    'REQUIRE_PARTS': ['day', 'month', 'year']
                }
            )
            if dt:
                return dt.date()
        return value

    @field_validator('date_of_birth')
    @classmethod
    def must_be_adult(cls, dob: Optional[date]) -> Optional[date]:
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                raise ValueError(f'El usuario debe ser mayor de edad (edad calculada: {age}).')
        return dob

    @model_validator(mode='after')
    def validate_identification_number(self) -> 'PartialCollectedData':
        id_type = self.identification_type
        id_number = self.identification_number

        if id_type and id_number:
            id_type = id_type.lower()
            if not is_valid_nif(id_number, id_type):
                raise ValueError(
                    f'El {id_type.upper()} "{id_number}" no es válido. '
                    'Debe cumplir el algoritmo oficial (DNI/NIE: módulo 23, letra según secuencia TRWAGMYFPDXBNJZSQVHLCKE).'
                )
        return self

class CollectedData(PartialCollectedData):
    """Datos completos recopilados para la contratación."""
    first_name: str
    last_name: str
    date_of_birth: date
    email: EmailStr
    phone_number: str
    identification_type: str = Field(pattern=r'^(dni|nie|pasaporte)$')
    identification_number: str
    address: Address
    selected_insurance: SelectedInsuranceProduct

class FinalAnswer(BaseModel):
    """Respuesta final cuando el proceso está completo."""
    id: str
    status: str = "new"
    ai_agent_id: str = "insurance_agent"
    ISO: str
    collected_data: CollectedData
    created_at: Optional[datetime] = None

class AgentState(BaseModel):
    """Estado del agente durante la conversación."""
    id: Optional[str] = None
    ai_agent_id: str = "insurance_agent"
    ISO: Optional[str] = None
    lang_lock: Optional[str] = None
    status: str = Field(pattern=r'^(incomplete|new)$')
    route: Optional[str] = None
    intent: Optional[str] = None  # "cotizar", "contratar", "consultar", "soporte"
    insurance_type: Optional[str] = None  # "auto", "hogar", "vida", "salud"
    collected_data: PartialCollectedData = Field(default_factory=PartialCollectedData)
    pending_field: Optional[str] = None
    invalid_reason: Optional[str] = None
    ready_for_commit: bool = False
    missing_fields: List[str] = []
    aborted: bool = False
    payment_link: Optional[str] = None
    payment_status: str = Field(pattern=r'^(pending|successful|failed)$', default='pending')
    user_profile: Optional[Dict[str, Any]] = None
    next_agent: Optional[str] = None  # Para transiciones entre agentes
