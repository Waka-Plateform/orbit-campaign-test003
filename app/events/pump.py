from __future__ import annotations

import structlog

from app.storage.tables import TableStore

log = structlog.get_logger()


async def poll_shared_mailbox(store: TableStore) -> dict:
    store.audit("shared_mailbox_poll")
    log.info("shared_mailbox_poll")
    return {"ok": True, "messages_imported": 0}
