from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.deps import store_dep
from app.storage.tables import TableStore, utc_now

router = APIRouter(tags=["tracking-open"])
PIXEL = bytes.fromhex("47494638396101000100800000ffffff00000021f90401000000002c00000000010001000002024401003b")


@router.get("/track/open/{step_id}")
def track_open(step_id: str, contact_id: str = Query(...), output_id: str | None = None, store: TableStore = Depends(store_dep)) -> Response:
    event_type = "email_opened" if step_id == "A" else "sms_opened"
    store.upsert("events", {"RowKey": f"{utc_now()}-{contact_id}-{step_id}", "contact_id": contact_id, "step_id": step_id, "channel": "email" if step_id == "A" else "sms", "event_type": event_type, "output_id": output_id or "", "created_at": utc_now()})
    return Response(content=PIXEL, media_type="image/gif", headers={"Cache-Control": "no-store"})
