from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

from app.config import ARTIFACTS, Settings
from app.integrations.acs_email import AcsEmailClient
from app.storage.tables import TableStore, utc_now

TOKEN_RE = re.compile(r"{{\s*([^}]+)\s*}}")


def render_template(raw: str, contact: dict[str, Any], links: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        token = match.group(1).strip()
        if token == "tracking_open_url":
            return links["tracking_open_url"]
        if token == "unsubscribe_url":
            return links["unsubscribe_url"]
        if token.startswith("tracking_click_url("):
            target = token.removeprefix("tracking_click_url(").removesuffix(")").strip("'\"")
            return links["click_base"] + target
        return str(contact.get(token, ""))
    return TOKEN_RE.sub(replace, raw)


def load_artifact(settings: Settings) -> str:
    endpoint = f"https://{settings.storage_account_name}.blob.core.windows.net"
    service = BlobServiceClient(account_url=endpoint, credential=DefaultAzureCredential(exclude_interactive_browser_credential=True))
    blob = service.get_blob_client(container=settings.artifacts_container, blob=ARTIFACTS["art_email_A"]["blob_path"])
    return blob.download_blob().readall().decode("utf-8")


def execute(contact: dict[str, Any], settings: Settings, store: TableStore, email_client: AcsEmailClient) -> dict[str, Any]:
    email = contact.get("email") or contact.get("Email Address") or contact.get("email_address")
    if not email:
        raise ValueError(f"Contact {contact.get('contact_id') or contact.get('RowKey')} has no email")
    contact_id = str(contact.get("contact_id") or contact.get("RowKey"))
    output_id = str(uuid.uuid4())
    base_url = settings.public_base_url.rstrip("/") or f"https://{settings.container_app_name}.orangepond-00000000.francecentral.azurecontainerapps.io"
    links = {
        "tracking_open_url": f"{base_url}/track/open/A?contact_id={contact_id}&output_id={output_id}",
        "unsubscribe_url": f"{base_url}/unsubscribe/{contact_id}",
        "click_base": f"{base_url}/track/click/A?contact_id={contact_id}&output_id={output_id}&url=",
    }
    html = render_template(load_artifact(settings), contact, links)
    message_id = email_client.send_html(str(email), ARTIFACTS["art_email_A"]["subject"], html, output_id)
    entity = {"PartitionKey": settings.campaign_id, "RowKey": output_id, "contact_id": contact_id, "step_id": "A", "channel": "email", "status": "sent", "provider_message_id": message_id, "sent_at": utc_now()}
    store.upsert("step_output", entity)
    store.upsert("events", {"PartitionKey": settings.campaign_id, "RowKey": f"{utc_now()}-{output_id}", "contact_id": contact_id, "step_id": "A", "channel": "email", "event_type": "sent", "created_at": utc_now()})
    return entity
