from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.deps import store_dep
from app.storage.tables import TableStore, utc_now

router = APIRouter(prefix="/webhooks/email", tags=["webhooks-email"])


@router.post("/delivery")
async def email_delivery(request: Request, store: TableStore = Depends(store_dep)) -> dict:
    payload = await request.json()
    events = payload if isinstance(payload, list) else [payload]
    for item in events:
        data = item.get("data", item) if isinstance(item, dict) else {}
        event_type = str(item.get("eventType", data.get("event_type", "email_delivery"))) if isinstance(item, dict) else "email_delivery"
        store.upsert("events", {"RowKey": f"{utc_now()}-{data.get('messageId', '')}", "channel": "email", "event_type": event_type, "payload": data, "created_at": utc_now()})
        if "bounce" in event_type.lower():
            store.upsert("bounces", {"RowKey": f"{utc_now()}-{data.get('messageId', '')}", "channel": "email", "payload": data, "created_at": utc_now()})
    return {"ok": True, "count": len(events)}
