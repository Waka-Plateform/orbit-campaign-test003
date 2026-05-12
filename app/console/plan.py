from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.actions._runner import CampaignRunner
from app.deps import store_dep
from app.storage.tables import TableStore

router = APIRouter(prefix="/api/console/plan", tags=["console-plan"])
runner: CampaignRunner | None = None


def set_runner(value: CampaignRunner) -> None:
    global runner
    runner = value


def get_runner() -> CampaignRunner:
    if runner is None:
        raise RuntimeError("Campaign runner is not initialized")
    return runner


def deep_merge(base: dict, patch: dict) -> dict:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


@router.get("")
def get_plan() -> dict:
    return get_runner().get_schedule()


@router.post("")
async def save_plan(request: Request) -> dict:
    body = await request.json()
    return get_runner().save_schedule(deep_merge(get_runner().get_schedule(), body))


@router.post("/start")
def start() -> dict:
    return {"ok": True, "new_status": get_runner().set_status("running")}


@router.post("/pause")
def pause() -> dict:
    return {"ok": True, "new_status": get_runner().set_status("paused")}


@router.post("/resume")
def resume() -> dict:
    return {"ok": True, "new_status": get_runner().set_status("running")}


@router.post("/stop")
def stop() -> dict:
    return {"ok": True, "new_status": get_runner().set_status("finished")}


@router.post("/tick")
async def tick() -> dict:
    return await get_runner().tick()
