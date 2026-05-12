from __future__ import annotations

from html import escape

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.config import CAMPAIGN_BRIEF
from app.deps import store_dep
from app.storage.tables import TableStore

router = APIRouter(prefix="/api/console", tags=["console-flow"])


@router.get("/flow.svg")
def flow_svg(mode: str = Query("runtime", pattern="^(design|runtime)$"), store: TableStore = Depends(store_dep)) -> Response:
    nodes = CAMPAIGN_BRIEF["flow_graph"]["nodes"]
    outputs = store.list_campaign("step_output", limit=10000)
    metrics = {n["id"]: sum(1 for o in outputs if o.get("step_id") == n["id"]) for n in nodes}
    width = 980
    height = 120 + len(nodes) * 90
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<style>text{font-family:Arial,sans-serif}.node{fill:#fff;stroke:#E8832A;stroke-width:2}.edge{stroke:#94a3b8;stroke-width:2}</style>']
    x = 320
    for i, node in enumerate(nodes):
        y = 40 + i * 90
        if i:
            parts.append(f'<line class="edge" x1="{x+170}" y1="{y-40}" x2="{x+170}" y2="{y}"/>')
        parts.append(f'<rect class="node" x="{x}" y="{y}" width="340" height="58" rx="10"/>')
        parts.append(f'<text x="{x+18}" y="{y+25}" font-size="15" font-weight="700">{escape(node.get("label", node["id"]))}</text>')
        caption = node.get("type", "") if mode == "design" else f'{node.get("type", "")} · sent {metrics.get(node["id"], 0)}'
        parts.append(f'<text x="{x+18}" y="{y+45}" font-size="12" fill="#475569">{escape(caption)}</text>')
    parts.append("</svg>")
    return Response("".join(parts), media_type="image/svg+xml")
