from __future__ import annotations

import json
from typing import Any

from azure.core.exceptions import ResourceNotFoundError
from fastapi import HTTPException, status

from app.config import AGENTS, Settings
from app.storage.tables import TableStore, utc_now

STATE_TABLE = "campaignstate"
CHANNEL_ROW_PREFIX = "channel:"

CHANNEL_SCHEMAS: dict[str, dict[str, Any]] = {
    "email": {
        "channel": "email",
        "enabled": True,
        "provider": "azure_communication_services",
        "required": [
            "email_subscription_id",
            "email_resource_group_name",
            "email_communication_service_id",
            "email_domain",
            "email_sender_username",
        ],
        "optional": ["email_display_name", "email_reply_to"],
    },
    "sms": {
        "channel": "sms",
        "enabled": True,
        "provider": "azure_communication_services",
        "required": [
            "sms_subscription_id",
            "sms_resource_group_name",
            "sms_communication_service_id",
            "sms_sender",
        ],
        "optional": [],
    },
    "whatsapp": {
        "channel": "whatsapp",
        "enabled": False,
        "provider": "azure_communication_services",
        "required": ["whatsapp_sender"],
        "optional": [],
    },
    "voice": {
        "channel": "voice",
        "enabled": False,
        "provider": "compeak",
        "required": ["compeak_token"],
        "optional": [],
    },
    "waka-agents": {
        "channel": "agents_waka",
        "enabled": True,
        "provider": "waka",
        "required": ["text_agent_id", "voice_agent_id", "avatar_agent_id"],
        "optional": [],
    },
}


def _row_key(channel_key: str) -> str:
    return f"{CHANNEL_ROW_PREFIX}{channel_key}"


def default_selection(channel_key: str, settings: Settings) -> dict[str, Any]:
    if channel_key == "email":
        return {
            "email_resource_group_name": "rg-orbit-platform",
            "email_communication_service_id": "orbit-acs",
            "email_domain": settings.email_sender_address.split("@", 1)[-1],
            "email_sender_username": settings.email_sender_address.split("@", 1)[0],
            "email_display_name": settings.email_sender_display_name,
            "email_reply_to": settings.email_reply_to,
        }
    if channel_key == "sms":
        return {
            "sms_resource_group_name": "rg-orbit-platform",
            "sms_communication_service_id": "orbit-acs",
            "sms_sender": settings.sms_from,
        }
    if channel_key == "whatsapp":
        return {"whatsapp_sender": ""}
    if channel_key == "voice":
        return {"compeak_token": "compeak-token"}
    if channel_key == "waka-agents":
        return {
            "text_agent_id": AGENTS["text"],
            "voice_agent_id": AGENTS["voice"],
            "avatar_agent_id": AGENTS["avatar"],
        }
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"unknown channel {channel_key}")


def load_selection(channel_key: str, settings: Settings, store: TableStore) -> dict[str, Any]:
    try:
        entity = store.get(STATE_TABLE, settings.campaign_id, _row_key(channel_key))
    except ResourceNotFoundError:
        return default_selection(channel_key, settings)
    selected_json = entity.get("selected_json")
    if not selected_json:
        return default_selection(channel_key, settings)
    selected = json.loads(str(selected_json))
    if not isinstance(selected, dict):
        raise RuntimeError(f"Invalid persisted channel selection for {channel_key}")
    return selected


def options_payload(channel_key: str, settings: Settings, store: TableStore) -> dict[str, Any]:
    schema = CHANNEL_SCHEMAS[channel_key]
    current = load_selection(channel_key, settings, store)
    return {
        "channel": schema["channel"],
        "channel_key": channel_key,
        "enabled": schema["enabled"],
        "provider": schema["provider"],
        "required_variables": schema["required"],
        "optional_variables": schema["optional"],
        "current": current,
        "options": build_options(channel_key, settings),
    }


def build_options(channel_key: str, settings: Settings) -> dict[str, list[dict[str, Any]]]:
    if channel_key == "email":
        return {
            "communication_services": [{"id": "orbit-acs", "name": "orbit-acs", "resource_group": "rg-orbit-platform"}],
            "domains": [{"id": settings.email_sender_address.split("@", 1)[-1], "name": settings.email_sender_address.split("@", 1)[-1]}],
            "senders": [{"id": settings.email_sender_address.split("@", 1)[0], "address": settings.email_sender_address, "display_name": settings.email_sender_display_name}],
        }
    if channel_key == "sms":
        return {
            "communication_services": [{"id": "orbit-acs", "name": "orbit-acs", "resource_group": "rg-orbit-platform"}],
            "senders": [{"id": settings.sms_from, "name": settings.sms_from}],
        }
    if channel_key == "waka-agents":
        return {
            "text_agents": [{"id": AGENTS["text"], "name": "Agent texte Waka"}],
            "voice_agents": [{"id": AGENTS["voice"], "name": "Agent voix Waka"}],
            "avatar_agents": [{"id": AGENTS["avatar"], "name": "Agent avatar Waka"}],
        }
    if channel_key == "whatsapp":
        return {"senders": []}
    if channel_key == "voice":
        return {"providers": [{"id": "compeak", "name": "Compeak"}]}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"unknown channel {channel_key}")


def validate_selection(channel_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    schema = CHANNEL_SCHEMAS[channel_key]
    selected = payload.get("selected", payload)
    if not isinstance(selected, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="selection body must be an object")
    missing = [field for field in schema["required"] if not str(selected.get(field, "")).strip()]
    if missing:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"missing": missing})
    allowed = set(schema["required"]) | set(schema["optional"])
    unknown = sorted(set(selected) - allowed)
    if unknown:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"unknown": unknown})
    return {key: selected[key] for key in selected if selected.get(key) is not None}


def persist_selection(channel_key: str, selected: dict[str, Any], settings: Settings, store: TableStore, actor: str) -> dict[str, Any]:
    entity = {
        "PartitionKey": settings.campaign_id,
        "RowKey": _row_key(channel_key),
        "kind": "channel_selection",
        "channel_key": channel_key,
        "channel": CHANNEL_SCHEMAS[channel_key]["channel"],
        "provider": CHANNEL_SCHEMAS[channel_key]["provider"],
        "selected_json": json.dumps(selected, ensure_ascii=False, sort_keys=True),
        "updated_by": actor,
        "updated_at": utc_now(),
    }
    store.upsert(STATE_TABLE, entity)
    store.audit("channel.select", actor=actor, payload={"channel_key": channel_key, "selected": selected})
    return {
        "ok": True,
        "channel": CHANNEL_SCHEMAS[channel_key]["channel"],
        "channel_key": channel_key,
        "selected": selected,
        "updated_at": entity["updated_at"],
    }
