from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import AGENTS, Settings
from app.deps import settings_dep

router = APIRouter(prefix="/api/console/channels", tags=["console-channels"])


@router.get("")
def channels(settings: Settings = Depends(settings_dep)) -> dict:
    return {"channels": {"email": {"enabled": True, "sender": settings.email_sender_address, "reply_to": settings.email_reply_to}, "sms": {"enabled": True, "from": settings.sms_from}, "whatsapp": {"enabled": False}, "voice": {"enabled": False}, "agents_waka": {"enabled": True, "agents": AGENTS}}}
