from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/channels/voice", tags=["channels-voice"])


@router.get("/status")
def status() -> dict:
    return {"channel": "voice", "enabled": False, "provider": "compeak"}
