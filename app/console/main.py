from __future__ import annotations

import os
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.config import CAMPAIGN_BRIEF, Settings
from app.deps import settings_dep, store_dep
from app.storage.tables import TableStore, load_repo_tree

router = APIRouter(prefix="/api/console/main", tags=["console-main"])


@router.get("")
async def main_console(settings: Settings = Depends(settings_dep), store: TableStore = Depends(store_dep)) -> dict:
    contacts = store.query("contacts", filter_expr=f"PartitionKey eq '{settings.campaign_id}'", limit=10000) or store.query("prospects", limit=10000)
    outputs = store.list_campaign("step_output", limit=10000)
    events = store.list_campaign("events", limit=10000)
    sent_email = sum(1 for r in outputs if r.get("channel") == "email")
    sent_sms = sum(1 for r in outputs if r.get("channel") == "sms")
    opened_email = len({e.get("contact_id") for e in events if e.get("event_type") == "email_opened"})
    opened_sms = len({e.get("contact_id") for e in events if e.get("event_type") in {"sms_opened", "sms_clicked", "sms_delivered"}})
    total = len(contacts) or 3484
    processed = len({r.get("contact_id") for r in outputs})
    status_rows = store.query("campaignstate", filter_expr=f"PartitionKey eq '{settings.campaign_id}' and RowKey eq 'status'", limit=1)
    status = str(status_rows[0].get("status")) if status_rows else "draft"
    return {
        "campaign": {"id": settings.campaign_id, "name": settings.campaign_name, "slug": settings.campaign_slug, "objective": CAMPAIGN_BRIEF["objective"], "status": status, "go_live_at": None, "duration_planned_seconds": 518400, "duration_elapsed_seconds": 0},
        "kpi_ops": {"volume_target": {"value": total, "label": "Volume cible"}, "volume_processed": {"value": processed, "label": "Volume traité"}, "volume_open": {"value": max(total - processed, 0), "label": "Touchés non clôturés"}, "file_closure_rate": {"value": processed / total if total else 0, "target": 1.0, "label": "Taux de clôture", "viz": "gauge"}, "campaign_duration": {"elapsed_seconds": 0, "planned_seconds": 518400, "label": "Temps écoulé", "viz": "progress"}, "kpi_business_primary": dict(CAMPAIGN_BRIEF["success_metrics"][0], value=len({* [e.get('contact_id') for e in events if e.get('event_type') in {'email_opened','sms_opened','sms_clicked'}]}) / total if total else 0)},
        "audiences": [{"id": "aud_all_prospects", "name": "Toute la base prospects", "count_current": total}],
        "volume_by_channel": [{"channel": "email", "sent": sent_email, "delivered": sent_email, "opened": opened_email}, {"channel": "sms", "sent": sent_sms, "delivered": opened_sms, "clicked": opened_sms}],
        "azure_resources": {"resource_group": settings.resource_group, "container_app": settings.container_app_name, "container_app_url": settings.container_app_url, "key_vault": settings.key_vault_name, "storage_account": settings.storage_account_name, "managed_identity": settings.managed_identity_name, "github_repo": settings.github_repo},
    }


@router.get("/files")
async def files(settings: Settings = Depends(settings_dep)) -> dict:
    return {"repo": settings.github_repo, "tree": await load_repo_tree(os.getcwd())}


@router.get("/files/content", response_class=PlainTextResponse)
def file_content(path: str = Query(...)) -> str:
    root = os.getcwd()
    full_path = os.path.abspath(os.path.join(root, path))
    if not full_path.startswith(root) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="file not found")
    with open(full_path, "r", encoding="utf-8") as handle:
        return handle.read()
