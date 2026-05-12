from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["events"])


async def stream():
    while True:
        yield f"event: ping\ndata: {json.dumps({'ok': True})}\n\n"
        await asyncio.sleep(15)


@router.get("/events")
def events() -> StreamingResponse:
    return StreamingResponse(stream(), media_type="text/event-stream")
