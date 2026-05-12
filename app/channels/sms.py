from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/channels/sms", tags=["channels-sms"])


@router.get("/status")
def status() -> dict:
    return {"channel": "sms", "enabled": True, "provider": "acs"}
