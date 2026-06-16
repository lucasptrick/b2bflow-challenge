import os
import logging
import requests
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL e SUPABASE_KEY devem estar definidos no .env")

    return create_client(url, key)


def fetch_contacts(supabase: Client, limit: int = 3) -> list[dict]:
    response = (
        supabase.table("contacts")
        .select("name, phone")
        .limit(limit)
        .execute()
    )
    return response.data


def send_whatsapp_message(phone: str, name: str) -> bool:
    instance_id = os.getenv("ZAPI_INSTANCE_ID")
    token = os.getenv("ZAPI_TOKEN")
    client_token = os.getenv("ZAPI_CLIENT_TOKEN")

    if not instance_id or not token or not client_token:
        raise ValueError("ZAPI_INSTANCE_ID, ZAPI_TOKEN e ZAPI_CLIENT_TOKEN devem estar definidos no .env")

    url = f"https://api.z-api.io/instances/{instance_id}/token/{token}/send-text"

    headers = {
        "Content-Type": "application/json",
        "Client-Token": client_token
    }

    payload = {
        "phone": phone,
        "message": f"Olá, {name} tudo bem com você?"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=10)

    if response.status_code == 200:
        logger.info(f"✅ Mensagem enviada para {name} ({phone})")
        return True
    else:
        logger.error(f"❌ Falha ao enviar para {name} ({phone}): {response.status_code} - {response.text}")
        return False


def main():
    logger.info("🚀 Iniciando envio de mensagens...")

    supabase = get_supabase_client()
    contacts = fetch_contacts(supabase, limit=3)

    if not contacts:
        logger.warning("Nenhum contato encontrado no banco de dados.")
        return

    logger.info(f"📋 {len(contacts)} contato(s) encontrado(s).")

    success_count = 0
    for contact in contacts:
        name = contact.get("name", "").strip()
        phone = contact.get("phone", "").strip()

        if not name or not phone:
            logger.warning(f"Contato com dados incompletos ignorado: {contact}")
            continue

        sent = send_whatsapp_message(phone, name)
        if sent:
            success_count += 1

    logger.info(f"> Envio concluído: {success_count}/{len(contacts)} mensagens enviadas.")


if __name__ == "__main__":
    main()
