from __future__ import annotations

from fastapi import APIRouter, Depends

from app.channels._selection import load_selection
from app.config import AGENTS, Settings
from app.deps import settings_dep, store_dep
from app.storage.tables import TableStore

router = APIRouter(prefix="/api/console/channels", tags=["console-channels"])


def channel_links(channel_key: str) -> dict[str, str]:
    return {
        "status": f"/api/channels/{channel_key}/status",
        "options": f"/api/channels/{channel_key}/options",
        "select": f"/api/channels/{channel_key}/select",
    }


@router.get("")
def channels(settings: Settings = Depends(settings_dep), store: TableStore = Depends(store_dep)) -> dict:
    return {
        "channels": {
            "email": {
                "enabled": True,
                "provider": "azure_communication_services",
                "sender": settings.email_sender_address,
                "reply_to": settings.email_reply_to,
                "selected": load_selection("email", settings, store),
                "links": channel_links("email"),
            },
            "sms": {
                "enabled": True,
                "provider": "azure_communication_services",
                "from": settings.sms_from,
                "selected": load_selection("sms", settings, store),
                "links": channel_links("sms"),
            },
            "whatsapp": {
                "enabled": False,
                "provider": "azure_communication_services",
                "selected": load_selection("whatsapp", settings, store),
                "links": channel_links("whatsapp"),
            },
            "voice": {
                "enabled": False,
                "provider": "compeak",
                "selected": load_selection("voice", settings, store),
                "links": channel_links("voice"),
            },
            "agents_waka": {
                "enabled": True,
                "provider": "waka",
                "agents": AGENTS,
                "selected": load_selection("waka-agents", settings, store),
                "links": channel_links("waka-agents"),
            },
        }
    }
