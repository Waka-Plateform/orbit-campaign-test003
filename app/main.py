from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.actions._runner import CampaignRunner
from app.config import get_settings
from app.console import base, channels, dashboard, flow_svg, health, inbox, main, plan, sources, views
from app.deps import get_secret_provider_cached, get_store_cached
from app.events import sse
from app.integrations.acs_email import AcsEmailClient
from app.integrations.acs_sms import AcsSmsClient
from app.tracking import click, open, unsubscribe
from app.webhooks import agent_callback, email_delivery, sms_event, voice_event, whatsapp_event
from app.channels import email, sms, voice, whatsapp, waka_agents

structlog.configure(processors=[structlog.processors.TimeStamper(fmt="iso"), structlog.processors.JSONRenderer()])
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    store = get_store_cached()
    store.ensure_tables()
    secrets = get_secret_provider_cached()
    runner = CampaignRunner(settings, store, AcsEmailClient(settings, secrets), AcsSmsClient(settings, secrets))
    plan.set_runner(runner)
    if settings.scheduler_enabled:
        runner.start_background()
    log.info("campaign_app_started", campaign_id=settings.campaign_id)
    yield
    if settings.scheduler_enabled:
        await runner.stop_background()
    log.info("campaign_app_stopped", campaign_id=settings.campaign_id)


app = FastAPI(title="Orbit Campaign test003", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

for router in [
    health.router, views.router, main.router, base.router, plan.router, sources.router, channels.router,
    dashboard.router, inbox.router, flow_svg.router, open.router, click.router, unsubscribe.router,
    email_delivery.router, sms_event.router, whatsapp_event.router, voice_event.router, agent_callback.router,
    sse.router, email.router, sms.router, whatsapp.router, voice.router, waka_agents.router,
]:
    app.include_router(router)
