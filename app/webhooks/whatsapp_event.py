from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.deps import store_dep
from app.storage.tables import TableStore, utc_now

router = APIRouter(prefix="/webhooks/whatsapp", tags=["webhooks-whatsapp"])


@router.post("/event")
async def whatsapp_event(request: Request, store: TableStore = Depends(store_dep)) -> dict:
    payload = await request.json()
    store.upsert("events", {"RowKey": f"{utc_now()}-whatsapp", "channel": "whatsapp", "event_type": "whatsapp_event", "payload": payload, "created_at": utc_now()})
    return {"ok": True}
