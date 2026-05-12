from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.channels._selection import load_selection, options_payload, persist_selection, validate_selection
from app.config import Settings
from app.deps import console_actor, settings_dep, store_dep
from app.storage.tables import TableStore

router = APIRouter(prefix="/api/channels/voice", tags=["channels-voice"])


@router.get("/status")
def status(settings: Settings = Depends(settings_dep), store: TableStore = Depends(store_dep)) -> dict:
    return {"channel": "voice", "enabled": False, "provider": "compeak", "selected": load_selection("voice", settings, store)}


@router.get("/options")
def options(settings: Settings = Depends(settings_dep), store: TableStore = Depends(store_dep)) -> dict:
    return options_payload("voice", settings, store)


@router.post("/select")
async def select(request: Request, actor: str = Depends(console_actor), settings: Settings = Depends(settings_dep), store: TableStore = Depends(store_dep)) -> dict:
    payload = await request.json()
    selected = validate_selection("voice", payload)
    return persist_selection("voice", selected, settings, store, actor)
