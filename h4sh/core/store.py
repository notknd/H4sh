from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class EvidenceStore:
    def __init__(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self.db = root / "h4sh.sqlite3"
        con = sqlite3.connect(self.db)
        try:
            con.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, at TEXT NOT NULL, module TEXT NOT NULL, target TEXT NOT NULL, result TEXT NOT NULL)")
            con.commit()
        finally:
            con.close()

    def add(self, module: str, target: str, result: dict) -> None:
        con = sqlite3.connect(self.db)
        try:
            con.execute("INSERT INTO events(at,module,target,result) VALUES(?,?,?,?)", (datetime.now(timezone.utc).isoformat(), module, target, json.dumps(result, ensure_ascii=False)))
            con.commit()
        finally:
            con.close()

    def session(self) -> list[dict]:
        con = sqlite3.connect(self.db)
        try:
            rows = con.execute("SELECT at,module,target,result FROM events ORDER BY id DESC LIMIT 500").fetchall()
        finally:
            con.close()
        return [{"timestamp": at, "module": module, "target": target, "result": json.loads(result)} for at, module, target, result in rows]
