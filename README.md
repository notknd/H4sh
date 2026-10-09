# H4sh

H4sh is a touch-friendly, terminal-native diagnostics console for Termux.
It focuses on authorized asset inventory, public DNS/IP lookup, HTTP/TLS posture
checks, auditable local case files, and session reports.

## Termux quick start

```sh
pkg update && pkg install python nmap
git clone https://github.com/notknd/H4sh.git && cd H4sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Textual uses the terminal mouse protocol when the terminal supports it. In
Termux, taps normally become mouse clicks; keyboard controls remain available.

## Scope and safety

Only assess systems you own or have express permission to test. H4sh never
passes user input to a shell: commands are invoked as argument lists, targets
are validated as hostnames/IP addresses, and every activity is logged locally.

## Controls

- Select a module from the left navigation.
- Enter an IP address, hostname, or HTTPS URL, then press the action button.
- Network profiles invoke a locally installed `nmap`; absence is shown clearly.
- Use **Export report** to create JSON, Markdown, and HTML reports in `reports/`.

## CTOS-inspired intelligence modules

- **Case file & timeline** — local SQLite evidence, separated by case.
- **Geo IP** — approximate network city/ASN data and an OpenStreetMap link.
- **Phone validation** — local E.164 validation and formatting only; it does not
  identify an owner or locate a phone.
- **Public entities** — candidate entities from Wikidata, with source links.
- **RDAP & relations** — public registration data and a compact passive graph of
  DNS, IP, ASN, and registration relationships.

These features are limited to public sources and authorized investigations.
Geo IP is inherently approximate. Do not use the public OpenStreetMap Nominatim
service for bulk queries; respect its attribution and rate-limit policy.

## Project layout

- `h4sh/app.py` — Textual touch/keyboard UI
- `h4sh/core/` — validation, non-shell process runner, evidence store, reports
- `h4sh/modules/` — DNS/IP, web/TLS, public-entity, RDAP, phone, and Nmap adapters

