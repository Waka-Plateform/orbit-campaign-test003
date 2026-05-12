from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.deps import store_dep
from app.storage.tables import TableStore, utc_now

router = APIRouter(prefix="/webhooks/agent", tags=["webhooks-agent"])


@router.post("/{agent_id}")
async def agent_callback(agent_id: str, request: Request, store: TableStore = Depends(store_dep)) -> dict:
    payload = await request.json()
    store.upsert("events", {"RowKey": f"{utc_now()}-{agent_id}", "channel": "agents_waka", "event_type": "agent_callback", "agent_id": agent_id, "payload": payload, "created_at": utc_now()})
    return {"ok": True}
