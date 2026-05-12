from __future__ import annotations

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings
from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import ARTIFACTS, Settings
from app.deps import console_actor, settings_dep, store_dep
from app.storage.tables import TableStore, utc_now

router = APIRouter(prefix="/api/console/sources", tags=["console-sources"])


def blob_service(settings: Settings) -> BlobServiceClient:
    return BlobServiceClient(
        account_url=f"https://{settings.storage_account_name}.blob.core.windows.net",
        credential=DefaultAzureCredential(exclude_interactive_browser_credential=True),
    )


def source_meta(source_id: str) -> dict:
    meta = ARTIFACTS.get(source_id)
    if not meta:
        raise HTTPException(status_code=404, detail="source not found")
    return meta


def public_source(source_id: str, meta: dict, include_content: bool = False, content: str | None = None) -> dict:
    payload = {
        "id": source_id,
        "action_id": meta.get("action_id"),
        "kind": meta.get("kind"),
        "channel": meta.get("channel"),
        "mode": meta.get("mode"),
        "subject": meta.get("subject"),
        "blob_path": meta.get("blob_path"),
        "editable": True,
        "content_type": "text/html" if meta.get("channel") == "email" else "text/plain",
    }
    if include_content:
        payload["content"] = content or ""
    return payload


@router.get("")
def list_sources() -> dict:
    return {"items": [public_source(artifact_id, meta) for artifact_id, meta in ARTIFACTS.items()]}


@router.get("/{id}")
def get_source(id: str, settings: Settings = Depends(settings_dep)) -> dict:
    meta = source_meta(id)
    try:
        content = blob_service(settings).get_blob_client(settings.artifacts_container, meta["blob_path"]).download_blob().readall().decode("utf-8")
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"source blob not found for {id}") from exc
    return public_source(id, meta, include_content=True, content=content)


@router.patch("/{id}")
async def patch_source(
    id: str,
    request: Request,
    actor: str = Depends(console_actor),
    settings: Settings = Depends(settings_dep),
    store: TableStore = Depends(store_dep),
) -> dict:
    meta = source_meta(id)
    body = await request.json()
    content = str(body.get("content", ""))
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    content_type = "text/html" if meta["channel"] == "email" else "text/plain"
    blob_service(settings).get_blob_client(settings.artifacts_container, meta["blob_path"]).upload_blob(
        content.encode("utf-8"),
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type),
    )
    store.audit("source.patch", actor=actor, payload={"source_id": id, "blob_path": meta["blob_path"]})
    return {"ok": True, "id": id, "updated_at": utc_now()}


@router.get("/{id}/history")
def history(id: str, settings: Settings = Depends(settings_dep)) -> dict:
    meta = source_meta(id)
    versions = blob_service(settings).get_container_client(settings.artifacts_container).list_blobs(
        name_starts_with=meta["blob_path"],
        include=["versions"],
    )
    return {
        "id": id,
        "versions": [
            {"name": version.name, "version_id": getattr(version, "version_id", None), "last_modified": str(version.last_modified)}
            for version in versions
        ],
    }


@router.post("/{id}/test")
def test_source(id: str, actor: str = Depends(console_actor), store: TableStore = Depends(store_dep)) -> dict:
    source_meta(id)
    store.audit("source.test", actor=actor, payload={"source_id": id})
    return {"ok": True, "id": id, "message": "test dispatch accepted for current user"}
