from __future__ import annotations

from urllib.parse import unquote

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse

from app.config import AGENTS, Settings
from app.deps import settings_dep, store_dep
from app.storage.tables import TableStore, utc_now

router = APIRouter(tags=["tracking-click"])


def resolve_target(raw: str, settings: Settings) -> str:
    target = unquote(raw)
    if target == "agents:all":
        return f"{settings.agents_base_url}?text={AGENTS['text']}&voice={AGENTS['voice']}&avatar={AGENTS['avatar']}"
    if target.startswith("web_text_session:"):
        return f"{settings.agents_base_url}/text/{AGENTS['text']}"
    if target.startswith("web_voice_session:"):
        return f"{settings.agents_base_url}/voice/{AGENTS['voice']}"
    if target.startswith("web_avatar_session:"):
        return f"{settings.agents_base_url}/avatar/{AGENTS['avatar']}"
    if target.startswith("https://") or target.startswith("http://"):
        return target
    raise ValueError(f"Unsupported click target {raw}")


@router.get("/track/click/{step_id}")
def track_click(step_id: str, contact_id: str = Query(...), url: str = Query(...), output_id: str | None = None, settings: Settings = Depends(settings_dep), store: TableStore = Depends(store_dep)) -> RedirectResponse:
    target = resolve_target(url, settings)
    store.upsert("events", {"RowKey": f"{utc_now()}-{contact_id}-{step_id}", "contact_id": contact_id, "step_id": step_id, "channel": "email" if step_id == "A" else "sms", "event_type": "clicked", "output_id": output_id or "", "target_url": target, "created_at": utc_now()})
    return RedirectResponse(target, status_code=302)
