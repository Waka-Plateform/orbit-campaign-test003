from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/channels/email", tags=["channels-email"])


@router.get("/status")
def status() -> dict:
    return {"channel": "email", "enabled": True, "provider": "acs"}
