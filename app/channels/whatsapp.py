from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/channels/whatsapp", tags=["channels-whatsapp"])


@router.get("/status")
def status() -> dict:
    return {"channel": "whatsapp", "enabled": False}
