import hashlib
import hmac
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


def build_whatsapp_session_id(phone_number: str) -> str:
    cleaned = "".join(ch for ch in (phone_number or "") if ch.isdigit())
    return f"wa:{cleaned}" if cleaned else "wa:unknown"


def verify_whatsapp_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    """
    Valida la firma X-Hub-Signature-256 enviada por Meta.
    Si no hay WHATSAPP_WEBHOOK_SECRET configurado, no bloquea la petición.
    """
    secret = os.getenv("WHATSAPP_WEBHOOK_SECRET", "").strip()
    if not secret:
        logger.warning("--- [WhatsApp] WHATSAPP_WEBHOOK_SECRET no configurado. Se omite validación de firma. ---")
        return True

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    incoming_digest = signature_header.split("=", 1)[1].strip()
    expected_digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(incoming_digest, expected_digest)


def extract_whatsapp_messages(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extrae mensajes entrantes tipo texto desde el payload del webhook de Meta.
    """
    extracted: List[Dict[str, Any]] = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                message_type = message.get("type")
                text_body = ""
                if message_type == "text":
                    text_body = (message.get("text") or {}).get("body", "")
                elif message_type == "interactive":
                    interactive = message.get("interactive") or {}
                    button_reply = (interactive.get("button_reply") or {}).get("title")
                    list_reply = (interactive.get("list_reply") or {}).get("title")
                    text_body = button_reply or list_reply or ""

                if not text_body:
                    continue

                extracted.append(
                    {
                        "from": message.get("from", ""),
                        "message_id": message.get("id"),
                        "text": text_body.strip(),
                        "timestamp": message.get("timestamp"),
                        "phone_number_id": value.get("metadata", {}).get("phone_number_id"),
                    }
                )

    return extracted


async def send_whatsapp_text(to_number: str, text: str) -> None:
    token = os.getenv("WHATSAPP_API_TOKEN", "").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    api_version = os.getenv("WHATSAPP_API_VERSION", "v21.0").strip() or "v21.0"

    if not token or not phone_number_id:
        raise RuntimeError("WHATSAPP_API_TOKEN o WHATSAPP_PHONE_NUMBER_ID no configurados")

    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text[:4096] if text else " "},
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code >= 400:
        logger.error("--- [WhatsApp] Error enviando mensaje: %s - %s ---", response.status_code, response.text)
        raise RuntimeError(f"Error enviando WhatsApp ({response.status_code})")
