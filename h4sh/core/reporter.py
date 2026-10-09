from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path


def export(events: list[dict], folder: Path) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = folder / f"h4sh-{stamp}.json"
    md_path = folder / f"h4sh-{stamp}.md"
    html_path = folder / f"h4sh-{stamp}.html"
    payload = json.dumps(events, ensure_ascii=False, indent=2)
    json_path.write_text(payload, encoding="utf-8")
    markdown = "# H4sh — relatório de sessão\n\n" + "\n".join(f"## {e['module']} · {e['target']}\n\n- Horário (UTC): {e['timestamp']}\n\n```json\n{json.dumps(e['result'], ensure_ascii=False, indent=2)}\n```" for e in events)
    md_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(f"<!doctype html><meta charset='utf-8'><title>H4sh report</title><style>body{{background:#071014;color:#c9f6ff;font-family:monospace;margin:2rem}}pre{{white-space:pre-wrap;background:#0d1d23;padding:1rem;border-left:3px solid #19d3da}}</style><h1>H4sh — relatório de sessão</h1><pre>{html.escape(payload)}</pre>", encoding="utf-8")
    return [json_path, md_path, html_path]
