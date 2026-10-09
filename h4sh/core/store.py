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
            con.execute("CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, at TEXT NOT NULL, module TEXT NOT NULL, target TEXT NOT NULL, result TEXT NOT NULL, case_name TEXT NOT NULL DEFAULT 'Sessão padrão')")
            columns = {row[1] for row in con.execute("PRAGMA table_info(events)")}
            if "case_name" not in columns:
                con.execute("ALTER TABLE events ADD COLUMN case_name TEXT NOT NULL DEFAULT 'Sessão padrão'")
            con.execute("INSERT OR IGNORE INTO cases(name, created_at) VALUES(?, ?)", ("Sessão padrão", datetime.now(timezone.utc).isoformat()))
            con.commit()
        finally:
            con.close()

    def add(self, module: str, target: str, result: dict, case_name: str = "Sessão padrão") -> None:
        con = sqlite3.connect(self.db)
        try:
            con.execute("INSERT OR IGNORE INTO cases(name, created_at) VALUES(?, ?)", (case_name, datetime.now(timezone.utc).isoformat()))
            con.execute("INSERT INTO events(at,module,target,result,case_name) VALUES(?,?,?,?,?)", (datetime.now(timezone.utc).isoformat(), module, target, json.dumps(result, ensure_ascii=False), case_name))
            con.commit()
        finally:
            con.close()

    def session(self, case_name: str | None = None) -> list[dict]:
        con = sqlite3.connect(self.db)
        try:
            if case_name:
                rows = con.execute("SELECT at,module,target,result,case_name FROM events WHERE case_name=? ORDER BY id DESC LIMIT 500", (case_name,)).fetchall()
            else:
                rows = con.execute("SELECT at,module,target,result,case_name FROM events ORDER BY id DESC LIMIT 500").fetchall()
        finally:
            con.close()
        return [{"timestamp": at, "module": module, "target": target, "result": json.loads(result), "case": saved_case} for at, module, target, result, saved_case in rows]

    def create_case(self, name: str) -> str:
        clean = " ".join(name.split())
        if not 2 <= len(clean) <= 80:
            raise ValueError("O caso deve ter entre 2 e 80 caracteres.")
        con = sqlite3.connect(self.db)
        try:
            con.execute("INSERT OR IGNORE INTO cases(name, created_at) VALUES(?, ?)", (clean, datetime.now(timezone.utc).isoformat()))
            con.commit()
        finally:
            con.close()
        return clean

    def cases(self) -> list[str]:
        con = sqlite3.connect(self.db)
        try:
            return [row[0] for row in con.execute("SELECT name FROM cases ORDER BY created_at DESC").fetchall()]
        finally:
            con.close()
