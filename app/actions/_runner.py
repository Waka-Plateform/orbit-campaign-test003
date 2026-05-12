from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import structlog

from app.actions import A_email, B_sms
from app.actions._scheduler import DEFAULT_SCHEDULE, batch_size_for, is_allowed_now
from app.config import CAMPAIGN_BRIEF, Settings
from app.integrations.acs_email import AcsEmailClient
from app.integrations.acs_sms import AcsSmsClient
from app.storage.tables import TableStore, utc_now

log = structlog.get_logger()


class CampaignRunner:
    def __init__(self, settings: Settings, store: TableStore, email_client: AcsEmailClient, sms_client: AcsSmsClient):
        self.settings = settings
        self.store = store
        self.email_client = email_client
        self.sms_client = sms_client
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    def start_background(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.loop())

    async def stop_background(self) -> None:
        self._stop.set()
        if self._task:
            await self._task

    async def loop(self) -> None:
        while not self._stop.is_set():
            try:
                await self.tick()
            except Exception as exc:
                log.error("runner_tick_failed", error=str(exc))
                self.store.audit("runner_tick_failed", payload={"error": str(exc)})
            await asyncio.sleep(self.settings.scheduler_interval_seconds)

    async def tick(self) -> dict:
        schedule = self.get_schedule()
        if not is_allowed_now(schedule):
            return {"ok": True, "deferred": True}
        status = self.get_status()
        if status not in {"running"}:
            return {"ok": True, "status": status}
        sent_email = self._send_email_batch(schedule)
        sent_sms = self._send_sms_batch(schedule)
        return {"ok": True, "email_sent": sent_email, "sms_sent": sent_sms}

    def get_schedule(self) -> dict:
        rows = self.store.query("campaignstate", filter_expr=f"PartitionKey eq '{self.settings.campaign_id}' and RowKey eq 'schedule'", limit=1)
        return rows[0].get("value") if rows and isinstance(rows[0].get("value"), dict) else DEFAULT_SCHEDULE.copy()

    def save_schedule(self, schedule: dict) -> dict:
        self.store.upsert("campaignstate", {"PartitionKey": self.settings.campaign_id, "RowKey": "schedule", "value": schedule, "updated_at": utc_now()})
        return schedule

    def get_status(self) -> str:
        rows = self.store.query("campaignstate", filter_expr=f"PartitionKey eq '{self.settings.campaign_id}' and RowKey eq 'status'", limit=1)
        return str(rows[0].get("status")) if rows else "draft"

    def set_status(self, status: str) -> str:
        self.store.upsert("campaignstate", {"PartitionKey": self.settings.campaign_id, "RowKey": "status", "status": status, "updated_at": utc_now()})
        self.store.audit(f"campaign_{status}")
        return status

    def _contacts(self, limit: int) -> list[dict]:
        contacts = self.store.query("contacts", filter_expr=f"PartitionKey eq '{self.settings.campaign_id}'", limit=limit)
        if contacts:
            return contacts
        return self.store.query("prospects", limit=limit)

    def _send_email_batch(self, schedule: dict) -> int:
        already = {r.get("contact_id") for r in self.store.query("step_output", filter_expr=f"PartitionKey eq '{self.settings.campaign_id}' and step_id eq 'A'", limit=10000)}
        candidates = [c for c in self._contacts(10000) if str(c.get("contact_id") or c.get("RowKey")) not in already]
        count = 0
        for contact in candidates[:batch_size_for(schedule, len(candidates))]:
            A_email.execute(contact, self.settings, self.store, self.email_client)
            count += 1
        return count

    def _send_sms_batch(self, schedule: dict) -> int:
        cutoff = datetime.now(UTC) - timedelta(hours=72)
        email_outputs = self.store.query("step_output", filter_expr=f"PartitionKey eq '{self.settings.campaign_id}' and step_id eq 'A'", limit=10000)
        opened = {e.get("contact_id") for e in self.store.query("events", filter_expr=f"PartitionKey eq '{self.settings.campaign_id}' and event_type eq 'email_opened'", limit=10000)}
        sms_sent = {r.get("contact_id") for r in self.store.query("step_output", filter_expr=f"PartitionKey eq '{self.settings.campaign_id}' and step_id eq 'B'", limit=10000)}
        contact_by_id = {str(c.get("contact_id") or c.get("RowKey")): c for c in self._contacts(10000)}
        due_ids: list[str] = []
        for row in email_outputs:
            sent_at = str(row.get("sent_at") or "")
            sent_dt = datetime.fromisoformat(sent_at.replace("Z", "+00:00")) if sent_at else datetime.now(UTC)
            cid = str(row.get("contact_id"))
            if sent_dt <= cutoff and cid not in opened and cid not in sms_sent:
                due_ids.append(cid)
        count = 0
        for cid in due_ids[:batch_size_for(schedule, len(due_ids))]:
            contact = contact_by_id.get(cid)
            if contact:
                B_sms.execute(contact, self.settings, self.store, self.sms_client)
                count += 1
        return count
