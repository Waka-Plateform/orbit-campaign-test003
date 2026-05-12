from __future__ import annotations

from fastapi import APIRouter

from app.config import AGENTS

router = APIRouter(prefix="/api/channels/waka-agents", tags=["channels-waka-agents"])


@router.get("/status")
def status() -> dict:
    return {"channel": "agents_waka", "enabled": True, "agents": AGENTS}
