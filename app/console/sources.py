from __future__ import annotations

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.config import ARTIFACTS, Settings
from app.deps import settings_dep

router = APIRouter(prefix="/api/console/sources", tags=["console-sources"])


def blob_service(settings: Settings) -> BlobServiceClient:
    return BlobServiceClient(account_url=f"https://{settings.storage_account_name}.blob.core.windows.net", credential=DefaultAzureCredential(exclude_interactive_browser_credential=True))


@router.get("")
def list_sources() -> dict:
    return {"items": [{"id": artifact_id, **meta} for artifact_id, meta in ARTIFACTS.items()]}


@router.get("/{source_id}")
def get_source(source_id: str, settings: Settings = Depends(settings_dep)) -> dict:
    meta = ARTIFACTS.get(source_id)
    if not meta:
        raise HTTPException(status_code=404, detail="source not found")
    content = blob_service(settings).get_blob_client(settings.artifacts_container, meta["blob_path"]).download_blob().readall().decode("utf-8")
    return {"id": source_id, **meta, "content": content}


@router.patch("/{source_id}")
async def patch_source(source_id: str, request: Request, settings: Settings = Depends(settings_dep)) -> dict:
    meta = ARTIFACTS.get(source_id)
    if not meta:
        raise HTTPException(status_code=404, detail="source not found")
    body = await request.json()
    content = str(body.get("content", ""))
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    blob_service(settings).get_blob_client(settings.artifacts_container, meta["blob_path"]).upload_blob(content.encode("utf-8"), overwrite=True, content_settings=ContentSettings(content_type="text/html" if meta["channel"] == "email" else "text/plain"))
    return {"ok": True, "id": source_id}


@router.get("/{source_id}/history")
def history(source_id: str, settings: Settings = Depends(settings_dep)) -> dict:
    meta = ARTIFACTS.get(source_id)
    if not meta:
        raise HTTPException(status_code=404, detail="source not found")
    versions = blob_service(settings).get_container_client(settings.artifacts_container).list_blobs(name_starts_with=meta["blob_path"], include=["versions"])
    return {"id": source_id, "versions": [{"name": v.name, "version_id": getattr(v, "version_id", None), "last_modified": str(v.last_modified)} for v in versions]}


@router.post("/{source_id}/test")
def test_source(source_id: str) -> dict:
    if source_id not in ARTIFACTS:
        raise HTTPException(status_code=404, detail="source not found")
    return {"ok": True, "source_id": source_id, "message": "test dispatch accepted for current user"}
