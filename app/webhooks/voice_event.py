from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.deps import store_dep
from app.storage.tables import TableStore, utc_now

router = APIRouter(prefix="/webhooks/voice", tags=["webhooks-voice"])


@router.post("/event")
async def voice_event(request: Request, store: TableStore = Depends(store_dep)) -> dict:
    payload = await request.json()
    store.upsert("events", {"RowKey": f"{utc_now()}-voice", "channel": "voice", "event_type": "voice_event", "payload": payload, "created_at": utc_now()})
    return {"ok": True}
