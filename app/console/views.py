from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")
SECTIONS = {"main", "base", "plan", "sources", "channels", "dashboard", "inbox"}


@router.get("/console")
def console_root() -> RedirectResponse:
    return RedirectResponse("/console/main", status_code=302)


@router.get("/console/{section}")
def console_section(section: str, request: Request):
    if section not in SECTIONS:
        section = "main"
    return templates.TemplateResponse(f"console/{section}.html", {"request": request, "section": section, "campaign_name": "test003"})
