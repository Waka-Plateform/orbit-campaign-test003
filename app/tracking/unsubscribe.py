from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.deps import store_dep
from app.storage.tables import TableStore, utc_now

router = APIRouter(tags=["tracking-unsubscribe"])


@router.get("/unsubscribe/{contact_id}", response_class=HTMLResponse)
def unsubscribe(contact_id: str, store: TableStore = Depends(store_dep)) -> str:
    store.upsert("optout", {"RowKey": contact_id, "contact_id": contact_id, "channel": "all", "reason": "unsubscribe_link", "created_at": utc_now()})
    store.upsert("events", {"RowKey": f"{utc_now()}-{contact_id}", "contact_id": contact_id, "event_type": "unsubscribed", "created_at": utc_now()})
    return "<html><body><h1>Désinscription confirmée</h1><p>Votre demande a bien été prise en compte.</p></body></html>"
