from __future__ import annotations

import json
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import store_dep
from app.storage.schemas import schema_for
from app.storage.tables import PUBLIC_TABLES, TableStore, apply_filters, paginate

router = APIRouter(prefix="/api/console/base", tags=["console-base"])


@router.get("/{table}")
def read_table(table: str, page: int = 1, per_page: int = 50, q: str | None = None, sort: str | None = None, filter: str | None = Query(default=None), store: TableStore = Depends(store_dep)) -> dict:
    if table not in PUBLIC_TABLES:
        raise HTTPException(status_code=404, detail="table not exposed")
    clauses = json.loads(unquote(filter)) if filter else []
    rows = store.list_campaign(table, limit=10000)
    filtered = apply_filters(rows, q, clauses, sort)
    page_rows, total = paginate(filtered, page, per_page)
    return {"table": table, "total": total, "page": page, "per_page": min(max(per_page, 1), 100), "rows": page_rows}


@router.get("/{table}/schema")
def read_schema(table: str, store: TableStore = Depends(store_dep)) -> dict:
    if table not in PUBLIC_TABLES:
        raise HTTPException(status_code=404, detail="table not exposed")
    return schema_for(table, store.list_campaign(table, limit=100))
