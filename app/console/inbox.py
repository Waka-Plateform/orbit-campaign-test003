from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from app.deps import store_dep
from app.storage.tables import TableStore, utc_now

router = APIRouter(prefix="/api/console/inbox", tags=["console-inbox"])


@router.get("/{channel}")
def inbox(channel: str, store: TableStore = Depends(store_dep)) -> dict:
    rows = [r for r in store.list_campaign("inbox", limit=1000) if r.get("channel") == channel]
    return {"channel": channel, "messages": rows}


@router.post("/{msg_id}/reply")
async def reply(msg_id: str, request: Request, store: TableStore = Depends(store_dep)) -> dict:
    body = await request.json()
    text = str(body.get("body", ""))
    if not text:
        raise HTTPException(status_code=400, detail="body is required")
    reply_id = str(uuid.uuid4())
    store.upsert("events", {"RowKey": reply_id, "event_type": "inbox_reply", "msg_id": msg_id, "body": text, "created_at": utc_now()})
    return {"ok": True, "reply_id": reply_id}
