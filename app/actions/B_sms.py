from __future__ import annotations

import uuid
from typing import Any

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

from app.config import ARTIFACTS, Settings
from app.integrations.acs_sms import AcsSmsClient
from app.storage.tables import TableStore, utc_now


def load_artifact(settings: Settings) -> str:
    endpoint = f"https://{settings.storage_account_name}.blob.core.windows.net"
    service = BlobServiceClient(account_url=endpoint, credential=DefaultAzureCredential(exclude_interactive_browser_credential=True))
    blob = service.get_blob_client(container=settings.artifacts_container, blob=ARTIFACTS["art_sms_B"]["blob_path"])
    return blob.download_blob().readall().decode("utf-8")


def render_sms(raw: str, settings: Settings, contact_id: str, output_id: str) -> str:
    base_url = settings.public_base_url.rstrip("/") or f"https://{settings.container_app_name}.orangepond-00000000.francecentral.azurecontainerapps.io"
    short_url = f"{base_url}/track/click/B?contact_id={contact_id}&output_id={output_id}&url={settings.legal_url}"
    agents_url = f"{base_url}/track/click/B?contact_id={contact_id}&output_id={output_id}&url=agents:all"
    return raw.replace("{short_url}", short_url).replace("{agents_url}", agents_url).replace("{stop_number}", settings.stop_number)


def execute(contact: dict[str, Any], settings: Settings, store: TableStore, sms_client: AcsSmsClient) -> dict[str, Any]:
    phone = contact.get("phone") or contact.get("Phone Number") or contact.get("phone_number")
    if not phone:
        raise ValueError(f"Contact {contact.get('contact_id') or contact.get('RowKey')} has no phone number")
    contact_id = str(contact.get("contact_id") or contact.get("RowKey"))
    output_id = str(uuid.uuid4())
    body = render_sms(load_artifact(settings), settings, contact_id, output_id)
    message_id = sms_client.send(str(phone), body, output_id)
    entity = {"PartitionKey": settings.campaign_id, "RowKey": output_id, "contact_id": contact_id, "step_id": "B", "channel": "sms", "status": "sent", "provider_message_id": message_id, "sent_at": utc_now()}
    store.upsert("step_output", entity)
    store.upsert("events", {"PartitionKey": settings.campaign_id, "RowKey": f"{utc_now()}-{output_id}", "contact_id": contact_id, "step_id": "B", "channel": "sms", "event_type": "sent", "created_at": utc_now()})
    return entity
