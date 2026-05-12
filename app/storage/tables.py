from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from typing import Any, Iterable

from azure.data.tables import TableClient, TableServiceClient, UpdateMode
from azure.identity import DefaultAzureCredential

from app.config import Settings

TABLE_NAMES = ["contacts", "stepoutput", "events", "inbox", "auditlog", "bounces", "optout", "conversions", "campaignstate", "prospects"]
PUBLIC_TABLES = {"contacts", "step_output", "events", "inbox", "audit_log", "bounces", "optout", "conversions"}
TABLE_MAP = {"step_output": "stepoutput", "audit_log": "auditlog"}
REVERSE_TABLE_MAP = {"stepoutput": "step_output", "auditlog": "audit_log"}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def normalize_table_name(name: str) -> str:
    normalized = TABLE_MAP.get(name, name)
    if normalized not in TABLE_NAMES:
        raise ValueError(f"Unknown table {name}")
    return normalized


class TableStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        endpoint = f"https://{settings.storage_account_name}.table.core.windows.net"
        credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        self.service = TableServiceClient(endpoint=endpoint, credential=credential)

    def ensure_tables(self) -> None:
        for table in TABLE_NAMES:
            self.service.create_table_if_not_exists(table_name=table)

    def table(self, name: str) -> TableClient:
        return self.service.get_table_client(normalize_table_name(name))

    def upsert(self, table: str, entity: dict[str, Any]) -> dict[str, Any]:
        normalized = normalize_table_name(table)
        entity = serialize_entity(entity)
        entity.setdefault("PartitionKey", self.settings.campaign_id)
        entity.setdefault("RowKey", str(uuid.uuid4()))
        entity.setdefault("updated_at", utc_now())
        self.table(normalized).upsert_entity(mode=UpdateMode.MERGE, entity=entity)
        return entity

    def get(self, table: str, partition_key: str, row_key: str) -> dict[str, Any]:
        return deserialize_entity(dict(self.table(table).get_entity(partition_key=partition_key, row_key=row_key)))

    def query(self, table: str, filter_expr: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        client = self.table(table)
        if filter_expr:
            iterator = client.query_entities(query_filter=filter_expr, results_per_page=limit or 100)
        else:
            iterator = client.list_entities(results_per_page=limit or 100)
        rows: list[dict[str, Any]] = []
        for entity in iterator:
            rows.append(deserialize_entity(dict(entity)))
            if limit and len(rows) >= limit:
                break
        return rows

    def list_campaign(self, table: str, limit: int = 1000) -> list[dict[str, Any]]:
        return self.query(table, filter_expr=f"PartitionKey eq '{self.settings.campaign_id}'", limit=limit)

    def audit(self, action: str, actor: str = "system", payload: dict[str, Any] | None = None) -> None:
        self.upsert("audit_log", {"PartitionKey": self.settings.campaign_id, "RowKey": f"{datetime.now(UTC).timestamp()}-{uuid.uuid4()}", "action": action, "actor": actor, "payload_json": json.dumps(payload or {}, ensure_ascii=False), "created_at": utc_now()})


def serialize_entity(entity: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in entity.items():
        if isinstance(value, (dict, list)):
            out[key] = json.dumps(value, ensure_ascii=False)
        elif isinstance(value, datetime):
            out[key] = value.isoformat()
        elif value is None:
            continue
        else:
            out[key] = value
    return out


def deserialize_entity(entity: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in entity.items():
        if key == "odata.metadata":
            continue
        if isinstance(value, str) and value and value[0] in "[{":
            try:
                out[key] = json.loads(value)
                continue
            except json.JSONDecodeError:
                pass
        out[key] = value
    return out


def infer_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, datetime):
        return "date"
    if isinstance(value, str):
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return "date"
        except ValueError:
            return "string"
    return "string"


def apply_filters(rows: list[dict[str, Any]], q: str | None, filters: list[dict[str, Any]] | None, sort: str | None) -> list[dict[str, Any]]:
    filtered = list(rows)
    if q:
        query = q.lower()
        filtered = [r for r in filtered if any(isinstance(v, str) and query in v.lower() for v in r.values())]
    for clause in filters or []:
        filtered = [r for r in filtered if match_clause(r, clause)]
    if sort:
        for spec in reversed([s.strip() for s in sort.split(",") if s.strip()]):
            field, _, direction = spec.partition(":")
            reverse = direction.lower() == "desc"
            filtered.sort(key=lambda row: row.get(field) is None or row.get(field), reverse=reverse)
    return filtered


def match_clause(row: dict[str, Any], clause: dict[str, Any]) -> bool:
    field = str(clause.get("field", ""))
    op = str(clause.get("op", "equals"))
    expected = clause.get("value")
    value = row.get(field)
    if op == "equals":
        return value == expected
    if op == "not_equals":
        return value != expected
    if op == "contains":
        if isinstance(value, list):
            return expected in value
        return str(expected).lower() in str(value or "").lower()
    if op == "not_contains":
        return str(expected).lower() not in str(value or "").lower()
    if op == "starts_with":
        return str(value or "").lower().startswith(str(expected).lower())
    if op == "ends_with":
        return str(value or "").lower().endswith(str(expected).lower())
    if op == "is_empty":
        return value in (None, "", [], {})
    if op == "is_not_empty":
        return value not in (None, "", [], {})
    if op in {"gt", "gte", "lt", "lte"}:
        if value is None:
            return False
        return {"gt": value > expected, "gte": value >= expected, "lt": value < expected, "lte": value <= expected}[op]
    if op == "in":
        return value in (expected or [])
    if op == "not_in":
        return value not in (expected or [])
    if op == "is_true":
        return value is True
    if op == "is_false":
        return value is False
    if op == "has_key":
        return isinstance(value, dict) and str(expected) in value
    return False


def paginate(rows: list[dict[str, Any]], page: int, per_page: int) -> tuple[list[dict[str, Any]], int]:
    safe_page = max(page, 1)
    safe_per_page = min(max(per_page, 1), 100)
    start = (safe_page - 1) * safe_per_page
    return rows[start:start + safe_per_page], len(rows)


async def load_repo_tree(root: str) -> list[dict[str, Any]]:
    categories = {
        "app/actions/": "actions", "app/channels/": "channels", "app/console/": "console", "app/tracking/": "tracking",
        "app/webhooks/": "webhooks", "app/events/": "events", "app/storage/": "storage", "app/integrations/": "integrations",
        "infra/": "infra", ".github/workflows/": "cicd",
    }
    tree: list[dict[str, Any]] = []
    for dirpath, _, filenames in os.walk(root):
        if ".git" in dirpath or "__pycache__" in dirpath:
            continue
        for name in filenames:
            path = os.path.relpath(os.path.join(dirpath, name), root).replace("\\", "/")
            if path.startswith((".venv/", "venv/")):
                continue
            category = "runtime" if path in {"app/main.py", "app/config.py"} else "other"
            for prefix, cat in categories.items():
                if path.startswith(prefix):
                    category = cat
                    break
            tree.append({"path": path, "type": "file", "size_bytes": os.path.getsize(os.path.join(root, path)), "category": category})
    return sorted(tree, key=lambda item: item["path"])
