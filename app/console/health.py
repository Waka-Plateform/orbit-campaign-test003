from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import Settings
from app.deps import settings_dep

router = APIRouter()


@router.get("/health")
def health(settings: Settings = Depends(settings_dep)) -> dict:
    return {"ok": True, "service": settings.service_name, "campaign_id": settings.campaign_id}
