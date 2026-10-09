from __future__ import annotations

import asyncio
import os
import socket
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static, TextArea

from h4sh.core.reporter import export
from h4sh.core.store import EvidenceStore
from h4sh.modules.network import PROFILES, scan
from h4sh.modules.osint import lookup
from h4sh.modules.web import audit

ROOT = Path(__file__).resolve().parent.parent


class H4shApp(App[None]):
    TITLE = "H4SH // CTOS DIAGNOSTICS"
    CSS_PATH = ROOT / "config" / "styles.tcss"
    BINDINGS = [("d", "show('dashboard')", "Dashboard"), ("o", "show('osint')", "OSINT"), ("w", "show('web')", "Web"), ("n", "show('network')", "Network"), ("r", "export_report", "Report")]

    def __init__(self) -> None:
        super().__init__()
        self.store = EvidenceStore(ROOT / "logs")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="shell"):
            with Container(id="nav"):
                yield Static("H4SH\nAUTHORIZED DIAGNOSTICS", id="brand")
                yield Button("Dashboard", id="nav-dashboard", classes="nav")
                yield Button("OSINT / DNS", id="nav-osint", classes="nav")
                yield Button("Web / TLS", id="nav-web", classes="nav")
                yield Button("Network", id="nav-network", classes="nav")
                yield Button("Export report", id="export", variant="success")
            with VerticalScroll(id="main"):
                yield Static(id="view-title")
                yield Static(id="view-subtitle")
                yield Container(id="workspace")
        yield Footer()

    async def on_mount(self) -> None:
        await self.action_show("dashboard")

    async def action_show(self, view: str) -> None:
        workspace = self.query_one("#workspace", Container)
        # Recent Textual releases remove children asynchronously. Awaiting the
        # operation prevents stale widgets (and duplicate IDs) between views.
        await workspace.remove_children()
        titles = {"dashboard": ("SYSTEM OVERVIEW", "Status local e escopo operacional."), "osint": ("OSINT / DNS", "Consulta pública e passiva de hostname/IP."), "web": ("WEB / TLS POSTURE", "Verificação de cabeçalhos e certificado de uma URL."), "network": ("NETWORK INVENTORY", "Use somente em ativos autorizados. Nmap é executado sem shell.")}
        self.query_one("#view-title", Static).update(titles[view][0])
        self.query_one("#view-subtitle", Static).update(titles[view][1])
        if view == "dashboard":
            await workspace.mount(Static(self._dashboard(), classes="result"))
        elif view == "osint":
            await workspace.mount(Input(placeholder="example.org ou 203.0.113.10", id="osint-target"), Button("Consultar registros", id="run-osint", variant="primary"), TextArea(id="result", read_only=True))
        elif view == "web":
            await workspace.mount(Input(placeholder="https://example.org", id="web-target"), Button("Auditar postura web", id="run-web", variant="primary"), TextArea(id="result", read_only=True))
        else:
            await workspace.mount(Input(placeholder="Hostname ou IP autorizado", id="network-target"), Select(((profile, profile) for profile in PROFILES), value="Fast scan", id="scan-profile"), Button("Executar inventário", id="run-network", variant="warning"), TextArea(id="result", read_only=True))

    def _dashboard(self) -> str:
        return f"""[ H4SH STATUS ]
HOST: {socket.gethostname()}
LOCAL IP: {self._local_ip()}
TIME: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}
EVENTS LOGGED: {len(self.store.session())}
MODE: authorized diagnostics / touch enabled

Tap a module on the left or use D / O / W / N."""

    @staticmethod
    def _local_ip() -> str:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "unavailable"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button = event.button.id or ""
        if button.startswith("nav-"):
            await self.action_show(button.removeprefix("nav-"))
        elif button == "export":
            self.action_export_report()
        elif button == "run-osint":
            await self._execute("OSINT/DNS", "osint-target", lookup)
        elif button == "run-web":
            await self._execute("Web/TLS", "web-target", audit)
        elif button == "run-network":
            profile = self.query_one("#scan-profile", Select).value
            await self._execute("Network", "network-target", lambda target: scan(target, str(profile)))

    async def _execute(self, module: str, input_id: str, operation) -> None:
        target = self.query_one(f"#{input_id}", Input).value
        area = self.query_one("#result", TextArea)
        area.text = "Executando… a interface permanece responsiva.\n"
        try:
            result = await operation(target)
            self.store.add(module, target, result)
            import json
            area.text = json.dumps(result, ensure_ascii=False, indent=2)
            self.notify("Resultado registrado localmente.", severity="information")
        except Exception as exc:
            area.text = f"Erro: {exc}"
            self.notify(str(exc), severity="error")

    def action_export_report(self) -> None:
        paths = export(self.store.session(), ROOT / "reports")
        self.notify("Relatórios criados: " + ", ".join(path.name for path in paths), severity="information", timeout=8)
