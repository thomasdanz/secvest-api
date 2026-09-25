# secvest-api

Reverse-engineered documentation of the REST API that the official app uses to talk to the **ABUS Secvest Touch (FUAA50500)** alarm panel. The goal is a complete OpenAPI specification that home-automation integrations can build on.

Only facts about the interface are recorded — no firmware, app binaries or decompiled code are part of this repository.

Not in scope: the API behind the panel's web interface (`sec_*.cgi`, `*.cgx`), which is a different interface.

> **Disclaimer:** This is an unofficial community project, not affiliated with or endorsed by ABUS. The panel is security equipment — use this at your own risk, never load-test it, and be careful with anything that arms, disarms or switches outputs.

## Layout

| Path | Content |
|---|---|
| `openapi.yaml` | The specification; grows with every finding |
| `fixtures/` | Redacted example responses, named after method and path (`GET_system_partitions-1_zones.json`); further examples of the same request get `.example2`, `.example3`, …; request bodies end in `.request.json`, error responses carry the status code (`GET_system.403.json`) |
| `docs/app-behavior.md` | How the official app uses the API (screens, polling, timing) |
| `docs/panel-behavior.md` | Background from the ABUS manuals: zone types, arming, alarms, reset |
| `scripts/redact.py` | Redacts raw captures and checks fixtures before a commit |
| `captures/` | Raw captures, **not versioned** |

## Evidence levels

Every operation carries `x-evidence`, and `x-sources` where it comes from third-party code:

- `verified` — observed on a real panel, the redacted response is in `fixtures/`
- `source` — taken from third-party code, docs, the panel firmware's strings or a static analysis of the official Android app (`x-sources` says which) ([node-red-contrib-secvest](https://github.com/yreiser/node-red-contrib-secvest), [homebridge-secvest](https://github.com/chris1705/homebridge-secvest), [PySecvest](https://github.com/chris1705/PySecvest)), not checked yet
- `assumption` — educated guess

What is still unknown is listed in `x-open-questions`, on the operation it belongs to or at the top of the spec.

## Redaction

Nothing that identifies an installation goes into git: host names, IP and MAC addresses, serial numbers, user codes, phone numbers, SIP accounts, zone or user names.

1. Copy `redact.example.json` to `redact.local.json` (gitignored) and list the installation-specific strings with neutral placeholders. Keep the mapping fixed (e.g. always the same room number for the same room), so fixtures stay comparable.
2. Keep raw responses in `captures/`, then redact them into `fixtures/`:
   ```bash
   scripts/redact.py captures/GET_system_partitions.json fixtures/GET_system_partitions.json
   ```
3. Before every commit:
   ```bash
   scripts/redact.py --check fixtures openapi.yaml
   ```

Built-in rules replace IPv4, MAC and e-mail addresses and blank out values of sensitive-looking JSON keys (`serial`, `code`, `pin`, `username`, `phone`, `sip`, …). Always review a fixture by eye as well — the rules can't know every field.

## License

[MIT](LICENSE)
