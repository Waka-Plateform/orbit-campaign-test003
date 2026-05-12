from __future__ import annotations

from typing import Any

from app.storage.tables import infer_type

FILTER_OPS = {
    "string": ["equals", "not_equals", "contains", "not_contains", "starts_with", "ends_with", "is_empty", "is_not_empty"],
    "number": ["equals", "not_equals", "gt", "gte", "lt", "lte", "between"],
    "boolean": ["is_true", "is_false"],
    "date": ["equals", "before", "after", "between", "is_today", "is_last_n_days"],
    "enum": ["in", "not_in"],
    "array": ["contains", "not_contains", "size_gt", "size_lt", "is_empty"],
    "object": ["has_key", "path_equals"],
}

DEFAULT_FIELDS: dict[str, list[dict[str, Any]]] = {
    "contacts": [
        {"field": "contact_id", "type": "string", "filterable": True, "sortable": True, "default_visible": True},
        {"field": "email", "type": "string", "filterable": True, "sortable": True, "default_visible": True},
        {"field": "phone", "type": "string", "filterable": True, "sortable": True, "default_visible": True},
        {"field": "audience_ids", "type": "array", "filterable": True, "sortable": False, "default_visible": True},
        {"field": "created_at", "type": "date", "filterable": True, "sortable": True, "default_visible": True},
        {"field": "source_fields", "type": "object", "filterable": False, "sortable": False, "default_visible": False},
    ],
    "step_output": [
        {"field": "contact_id", "type": "string", "filterable": True, "sortable": True, "default_visible": True},
        {"field": "step_id", "type": "string", "filterable": True, "sortable": True, "default_visible": True},
        {"field": "channel", "type": "enum", "filterable": True, "sortable": True, "default_visible": True},
        {"field": "status", "type": "enum", "filterable": True, "sortable": True, "default_visible": True},
        {"field": "sent_at", "type": "date", "filterable": True, "sortable": True, "default_visible": True},
    ],
    "events": [
        {"field": "contact_id", "type": "string", "filterable": True, "sortable": True, "default_visible": True},
        {"field": "event_type", "type": "enum", "filterable": True, "sortable": True, "default_visible": True},
        {"field": "channel", "type": "enum", "filterable": True, "sortable": True, "default_visible": True},
        {"field": "created_at", "type": "date", "filterable": True, "sortable": True, "default_visible": True},
        {"field": "payload", "type": "object", "filterable": False, "sortable": False, "default_visible": False},
    ],
    "inbox": [
        {"field": "msg_id", "type": "string", "filterable": True, "sortable": True, "default_visible": True},
        {"field": "channel", "type": "enum", "filterable": True, "sortable": True, "default_visible": True},
        {"field": "from", "type": "string", "filterable": True, "sortable": True, "default_visible": True},
        {"field": "body", "type": "string", "filterable": True, "sortable": False, "default_visible": True},
        {"field": "received_at", "type": "date", "filterable": True, "sortable": True, "default_visible": True},
    ],
}


def schema_for(table: str, sample_rows: list[dict[str, Any]]) -> dict[str, Any]:
    fields = {field["field"]: field for field in DEFAULT_FIELDS.get(table, [])}
    for row in sample_rows:
        for key, value in row.items():
            if key in {"PartitionKey", "RowKey", "Timestamp", "etag"}:
                continue
            fields.setdefault(key, {"field": key, "type": infer_type(value), "filterable": infer_type(value) != "object", "sortable": infer_type(value) not in {"array", "object"}, "default_visible": len(fields) < 8})
    return {"table": table, "fields": list(fields.values()), "filter_ops": FILTER_OPS}
