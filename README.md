# secvest-api

Reverse Engineering der REST-Schnittstelle der **ABUS Secvest Touch (FUAA50500)**, die auch die offizielle App nutzt. Ziel ist eine vollständige OpenAPI-Spezifikation als Grundlage für eine Home-Assistant-Anbindung.

**Nicht im Umfang:** die Schnittstelle der Web-Oberfläche (`sec_*.cgi`, `*.cgx`) – das ist eine andere API.

## Aufbau

| Pfad | Inhalt |
|---|---|
| `openapi.yaml` | Spezifikation, wächst mit jeder Erkenntnis |
| `fixtures/` | geschwärzte Beispielantworten, benannt nach Methode und Pfad |
| `captures/` | Rohmitschnitte, **nicht versioniert** (gitignored) |

## Belastbarkeit

Jede Operation trägt `x-evidence`:

- `verified` – an der eigenen Anlage abgefragt, Antwort liegt in `fixtures/`
- `source` – aus fremdem Code/Doku (node-red-contrib-secvest, homebridge-secvest, PySecvest), nicht geprüft
- `assumption` – Vermutung

## Regeln

- Keine Zugangsdaten, Seriennummern oder Benutzercodes im Repo; Fixtures vor dem Commit schwärzen.
- Lesende Anfragen (GET) sind unkritisch. Alles, was schalten kann (PUT/POST/DELETE), nur einzeln und bewusst.
- Keine Lasttests – die Zentrale ist Sicherheitsinfrastruktur.
