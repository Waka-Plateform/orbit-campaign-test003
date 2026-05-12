from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.deps import store_dep
from app.storage.tables import TableStore, utc_now

router = APIRouter(prefix="/webhooks/sms", tags=["webhooks-sms"])


@router.post("/event")
async def sms_event(request: Request, store: TableStore = Depends(store_dep)) -> dict:
    payload = await request.json()
    items = payload if isinstance(payload, list) else [payload]
    for item in items:
        data = item.get("data", item) if isinstance(item, dict) else {}
        event_type = str(data.get("deliveryStatus", item.get("eventType", "sms_event"))).lower()
        normalized = "sms_delivered" if "delivered" in event_type else "sms_undelivered" if "failed" in event_type or "undelivered" in event_type else "sms_event"
        store.upsert("events", {"RowKey": f"{utc_now()}-{data.get('messageId', '')}", "channel": "sms", "event_type": normalized, "payload": data, "created_at": utc_now()})
    return {"ok": True, "count": len(items)}
