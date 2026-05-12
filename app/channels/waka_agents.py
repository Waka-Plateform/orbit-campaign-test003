from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.channels._selection import load_selection, options_payload, persist_selection, validate_selection
from app.config import AGENTS, Settings
from app.deps import console_actor, settings_dep, store_dep
from app.storage.tables import TableStore

router = APIRouter(prefix="/api/channels/waka-agents", tags=["channels-waka-agents"])


@router.get("/status")
def status(settings: Settings = Depends(settings_dep), store: TableStore = Depends(store_dep)) -> dict:
    return {"channel": "agents_waka", "enabled": True, "agents": AGENTS, "selected": load_selection("waka-agents", settings, store)}


@router.get("/options")
def options(settings: Settings = Depends(settings_dep), store: TableStore = Depends(store_dep)) -> dict:
    return options_payload("waka-agents", settings, store)


@router.post("/select")
async def select(request: Request, actor: str = Depends(console_actor), settings: Settings = Depends(settings_dep), store: TableStore = Depends(store_dep)) -> dict:
    payload = await request.json()
    selected = validate_selection("waka-agents", payload)
    return persist_selection("waka-agents", selected, settings, store, actor)
