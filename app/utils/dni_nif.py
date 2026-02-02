"""
Validación de DNI/NIF/NIE según el algoritmo oficial español (Ministerio del Interior).
Módulo 23: Letra = Número_DNI % 23, secuencia TRWAGMYFPDXBNJZSQVHLCKE (excl. I, O, U, Ñ).
"""
import re

# Secuencia oficial: resto 0-22 → letra (excluye I, O, U, Ñ)
DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"


def _normalize_dni_input(value: str) -> str:
    """Elimina espacios, puntos, guiones y pasa letra a mayúscula."""
    if not value or not isinstance(value, str):
        return ""
    s = value.strip().upper()
    s = re.sub(r"[\s.\-]", "", s)
    return s


def is_valid_dni(value: str) -> bool:
    """
    Valida DNI español: 8 dígitos + 1 letra.
    Letra correcta = DNI_LETTERS[numero % 23].
    """
    s = _normalize_dni_input(value)
    if not re.match(r"^\d{8}[A-Z]$", s):
        return False
    num = int(s[:8])
    letter = s[8]
    return DNI_LETTERS[num % 23] == letter


def is_valid_nie(value: str) -> bool:
    """
    Valida NIE (extranjeros): X/Y/Z + 7 dígitos + 1 letra.
    Se reemplaza X→0, Y→1, Z→2 y se aplica el mismo módulo 23.
    """
    s = _normalize_dni_input(value)
    if not re.match(r"^[XYZ]\d{7}[A-Z]$", s):
        return False
    prefix = s[0]
    num_str = s[1:8]
    prefix_digit = {"X": "0", "Y": "1", "Z": "2"}[prefix]
    num = int(prefix_digit + num_str)
    letter = s[8]
    return DNI_LETTERS[num % 23] == letter


def is_valid_nif(value: str, id_type: str = "dni") -> bool:
    """
    Valida NIF según tipo: dni, nie o pasaporte.
    Para pasaporte se acepta formato típico 3 letras + 6 dígitos (sin algoritmo módulo 23).
    """
    if not value or not value.strip():
        return False
    id_type = (id_type or "dni").lower()
    if id_type == "dni":
        return is_valid_dni(value)
    if id_type == "nie":
        return is_valid_nie(value)
    if id_type == "pasaporte":
        return bool(re.match(r"^[A-Za-z]{2,3}[0-9]{6}$", _normalize_dni_input(value)))
    return False
