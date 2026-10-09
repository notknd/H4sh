from __future__ import annotations

import asyncio
import json
import socket
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, Select, Static, TextArea

from h4sh.core.privacy import mask_phone
from h4sh.core.reporter import export
from h4sh.core.store import EvidenceStore
from h4sh.modules.geoip import lookup as geo_lookup
from h4sh.modules.graph import build as graph_build
from h4sh.modules.network import PROFILES, scan
from h4sh.modules.osint import lookup as dns_lookup
from h4sh.modules.people import search as people_search
from h4sh.modules.phone import inspect as phone_inspect
from h4sh.modules.rdap import lookup as rdap_lookup
from h4sh.modules.web import audit

ROOT = Path(__file__).resolve().parent.parent


class H4shApp(App[None]):
    TITLE = "H4SH // CTOS DIAGNOSTICS"
    CSS_PATH = ROOT / "config" / "styles.tcss"
    BINDINGS = [
        ("d", "show('dashboard')", "Dashboard"), ("o", "show('osint')", "OSINT"),
        ("g", "show('geo')", "Geo"), ("p", "show('phone')", "Phone"),
        ("l", "show('timeline')", "Timeline"), ("r", "export_report", "Report"),
    ]
    VIEWS = {
        "dashboard": ("CTOS // SYSTEM OVERVIEW", "Telemetria da sessão e escopo autorizado."),
        "case": ("CASE FILE", "Evidências são locais, organizadas por caso."),
        "timeline": ("ACTIVITY TIMELINE", "Eventos da sessão ativa, em ordem cronológica."),
        "osint": ("OSINT / DNS", "Consulta pública e passiva de hostname/IP."),
        "geo": ("GEO IP", "Localização aproximada de rede; não rastreia dispositivos."),
        "phone": ("PHONE VALIDATION", "Validação local. Não identifica proprietário nem localiza pessoas."),
        "people": ("PUBLIC ENTITIES", "Pesquisa de entidades públicas no Wikidata; resultados são candidatos."),
        "rdap": ("RDAP REGISTRY", "Dados públicos de registro para domínio ou IP."),
        "graph": ("RELATION GRAPH", "Relações passivas entre alvo, DNS, ASN e RDAP."),
        "web": ("WEB / TLS POSTURE", "Verificação de cabeçalhos e certificado de uma URL."),
        "network": ("NETWORK INVENTORY", "Use somente em ativos autorizados. Nmap é executado sem shell."),
    }

    def __init__(self) -> None:
        super().__init__()
        self.store = EvidenceStore(ROOT / "logs")
        self.active_case = "Sessão padrão"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="shell"):
            with VerticalScroll(id="nav"):
                yield Static("H4SH\nAUTHORIZED DIAGNOSTICS", id="brand")
                for key, label in (
                    ("dashboard", "Dashboard"), ("case", "Case file"), ("timeline", "Timeline"),
                    ("osint", "OSINT / DNS"), ("geo", "Geo IP"), ("phone", "Phone"),
                    ("people", "Public entities"), ("rdap", "RDAP"), ("graph", "Relations"),
                    ("web", "Web / TLS"), ("network", "Network"),
                ):
                    yield Button(label, id=f"nav-{key}", classes="nav")
                yield Button("Export report", id="export", variant="success")
            with VerticalScroll(id="main"):
                yield Static(id="view-title")
                yield Static(id="view-subtitle")
                yield Static(id="case-status")
                yield Container(id="workspace")
        yield Footer()

    async def on_mount(self) -> None:
        await self._run_boot_sequence()
        await self.action_show("dashboard")

    async def _run_boot_sequence(self) -> None:
        """Render a deliberately fictional, Linux-style visual boot sequence."""
        workspace = self.query_one("#workspace", Container)
        self.query_one("#view-title", Static).update("H4SH // CTOS BOOT SEQUENCE")
        self.query_one("#view-subtitle", Static).update("SIMULATED STARTUP TELEMETRY — NOT A KERNEL LOG")
        self.query_one("#case-status", Static).update("NODE // INITIALIZING")
        console = Static("", id="boot-console", classes="boot")
        await workspace.mount(console)
        started = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        lines = [
            "[    0.000000] H4SH CTOS Runtime 0.2 — boot sequence initiated",
            "[    0.006241] firmware: diagnostic profile loaded [SIMULATED]",
            f"[    0.011320] clocksource: {started}",
            "[    0.019104] memory: constrained-terminal profile enabled",
            "[    0.031740] input: ANSI / VT100 touch-mouse event layer ready",
            "[    0.045918] storage: opening local SQLite evidence store",
            "[  OK  ] Mounted local-evidence.service",
            "[    0.064502] network: initializing authorized diagnostics policy",
            "[  OK  ] Reached target public-source-network.target",
            "[    0.086213] module: DNS passive resolver loaded",
            "[    0.101882] module: Geo IP approximation adapter loaded",
            "[    0.118436] module: RDAP public registry adapter loaded",
            "[    0.135701] module: Wikidata public-entity adapter loaded",
            "[    0.149381] module: local phone validation adapter loaded",
            "[  OK  ] Started CTOS relationship-graph service",
            "[  OK  ] Started touch-optimized Textual interface",
            "[ NOTICE ] Public sources only — authorization required for active checks",
            "[  DONE ] H4SH node online. Transferring control to dashboard…",
        ]
        rendered: list[str] = []
        for line in lines:
            rendered.append(line)
            console.update("\n".join(rendered))
            await asyncio.sleep(0.075)
        await asyncio.sleep(0.35)

    async def action_show(self, view: str) -> None:
        if view not in self.VIEWS:
            return
        workspace = self.query_one("#workspace", Container)
        await workspace.remove_children()
        title, subtitle = self.VIEWS[view]
        self.query_one("#view-title", Static).update(title)
        self.query_one("#view-subtitle", Static).update(subtitle)
        self.query_one("#case-status", Static).update(f"CASE // {self.active_case}")
        if view == "dashboard":
            await workspace.mount(Static(self._dashboard(), classes="result"))
        elif view == "case":
            await workspace.mount(
                Input(placeholder="Nome do caso (ex.: Auditoria example.org)", id="case-name"),
                Button("Criar / ativar caso", id="run-case", variant="primary"),
                TextArea(self._case_list(), id="result", read_only=True),
            )
        elif view == "timeline":
            await workspace.mount(TextArea(self._timeline(), id="result", read_only=True))
        elif view == "osint":
            await self._form(workspace, "example.org ou 203.0.113.10", "osint-target", "Consultar registros", "run-osint")
        elif view == "geo":
            await self._form(workspace, "Hostname ou IP público", "geo-target", "Consultar Geo IP", "run-geo")
        elif view == "phone":
            await self._form(workspace, "+55 11 99999-9999 (somente com consentimento)", "phone-target", "Validar número", "run-phone")
        elif view == "people":
            await self._form(workspace, "Nome de entidade pública", "people-target", "Buscar no Wikidata", "run-people")
        elif view == "rdap":
            await self._form(workspace, "example.org ou IP", "rdap-target", "Consultar registro público", "run-rdap")
        elif view == "graph":
            await self._form(workspace, "Hostname ou IP autorizado", "graph-target", "Mapear relações passivas", "run-graph")
        elif view == "web":
            await self._form(workspace, "https://example.org", "web-target", "Auditar postura web", "run-web")
        else:
            await workspace.mount(
                Input(placeholder="Hostname ou IP autorizado", id="network-target"),
                Select(((profile, profile) for profile in PROFILES), value="Fast scan", id="scan-profile"),
                Button("Executar inventário", id="run-network", variant="warning"),
                TextArea(id="result", read_only=True),
            )

    async def _form(self, workspace: Container, placeholder: str, input_id: str, label: str, button_id: str) -> None:
        await workspace.mount(Input(placeholder=placeholder, id=input_id), Button(label, id=button_id, variant="primary"), TextArea(id="result", read_only=True))

    def _dashboard(self) -> str:
        events = self.store.session(self.active_case)
        return f"""[ CTOS STATUS ]
CASE: {self.active_case}
HOST: {socket.gethostname()}
LOCAL IP: {self._local_ip()}
TIME: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}
EVIDENCE EVENTS: {len(events)}
MODE: authorized diagnostics / public sources / touch enabled

DATA LABELS
[PUBLIC SOURCE] dados abertos     [APPROXIMATE] Geo IP
[LOCAL ONLY] case files           [CONSENT] phone validation

Use the navigation panel or shortcuts D / O / G / P / L."""

    def _case_list(self) -> str:
        return "CASES\n" + "\n".join(f"{'▶' if name == self.active_case else ' '} {name}" for name in self.store.cases())

    def _timeline(self) -> str:
        events = self.store.session(self.active_case)
        if not events:
            return "Nenhuma evidência neste caso. Execute uma consulta para iniciar a timeline."
        return "\n\n".join(f"[{event['timestamp']}] {event['module']} :: {event['target']}" for event in events)

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
        elif button == "run-case":
            self.active_case = self.store.create_case(self.query_one("#case-name", Input).value)
            self.notify(f"Caso ativo: {self.active_case}")
            await self.action_show("case")
        elif button == "run-osint":
            await self._execute("OSINT/DNS", "osint-target", dns_lookup)
        elif button == "run-geo":
            await self._execute("Geo IP", "geo-target", geo_lookup)
        elif button == "run-phone":
            await self._execute("Phone validation", "phone-target", phone_inspect, stored_target=mask_phone)
        elif button == "run-people":
            await self._execute("Public entities", "people-target", people_search)
        elif button == "run-rdap":
            await self._execute("RDAP", "rdap-target", rdap_lookup)
        elif button == "run-graph":
            await self._execute("Relations", "graph-target", graph_build)
        elif button == "run-web":
            await self._execute("Web/TLS", "web-target", audit)
        elif button == "run-network":
            profile = self.query_one("#scan-profile", Select).value
            await self._execute("Network", "network-target", lambda target: scan(target, str(profile)))

    async def _execute(self, module: str, input_id: str, operation, stored_target=None) -> None:
        target = self.query_one(f"#{input_id}", Input).value
        area = self.query_one("#result", TextArea)
        area.text = "Executando… a interface permanece responsiva.\n"
        try:
            result = await operation(target)
            record = result
            if module == "Phone validation":
                record = {**result, "e164": mask_phone(result.get("e164") or ""), "international": mask_phone(result.get("international") or "")}
            self.store.add(module, stored_target(target) if stored_target else target, record, self.active_case)
            area.text = json.dumps(result, ensure_ascii=False, indent=2)
            self.notify("Resultado registrado no caso local.", severity="information")
        except Exception as exc:
            area.text = f"Erro: {exc}"
            self.notify(str(exc), severity="error")

    def action_export_report(self) -> None:
        paths = export(self.store.session(self.active_case), ROOT / "reports")
        self.notify("Relatórios criados: " + ", ".join(path.name for path in paths), severity="information", timeout=8)
