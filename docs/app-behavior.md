# How the official app uses the API

Observed on the iOS app (build `Secvest/20240402`) by capturing its traffic behind a TLS-terminating reverse proxy while recording the screen. Nothing here was switched except omitting and re-including one zone.

## Screens

The app has two tabs, **Status** and **Logbuch** (log).

- **Status** shows a three-way switch for the partition (arm internally / disarm / arm), a readiness line ("… ist bereit zur Aktivierung"), a **Zonen** section and a **Störungen** (faults) section.
  - The zone section only lists zones that need attention, e.g. "209 ist offen". If all are fine it says "Alle Zonen störungsfrei."
  - Tapping an open zone opens a dialog with **Zone ausblenden** (omit zone). After omitting, the zone is listed as "209 ist ausgeblendet"; tapping it again offers to include it again.
- **Logbuch** lists log entries grouped by day, with a filter **Alle / Alarme / Störungen** (all / alarms / faults). Tapping an entry shows its details, including the user name.

## Requests

### Start-up

```text
GET /system/
GET /alarms/          ┐ in parallel
GET /faults/          ┘
GET /system/partitions/
GET /system/partitions-1/zones/   ┐
GET /system/partitions-2/zones/   │ in parallel, for all four partitions,
GET /system/partitions-3/zones/   │ even empty ones
GET /system/partitions-4/zones/   ┘
GET /cameras/         ┐ in parallel
GET /outputs/         ┘
```

### Polling while the app is open

About every **24 seconds**, on either tab:

```text
GET /alarms/ + GET /faults/        (parallel)
GET /system/partitions/
GET /system/partitions-{1..4}/zones/   (parallel)
```

`/system/` and `/system/partitions-{n}/` (single partition) are not polled.

### Log

Opening the Logbuch tab sends a single incremental request:

```text
GET /logs/?$filter=timestamp ge <newest known timestamp + 1>
```

The app keeps the log locally and only fetches newer entries. The Alle / Alarme / Störungen filter works on the local copy and sends no request.

### Omitting a zone

```text
PUT /system/partitions-1/zones-209/   {"omitted":"true"}    → zone object
GET /alarms/ + GET /faults/           (refresh right after)
PUT /system/partitions-1/zones-209/   {"omitted":"false"}   → zone object
GET /alarms/ + GET /faults/
```

Omitting the open zone removed its zone-open fault (`prevents-set: true`) from `/faults/`.

## Timing

Through the proxy, which keeps TLS sessions to the panel alive, most responses took **0.04–0.12 s**. When the app sent four or more requests at once, the extra ones took about **3.4 s**, which is presumably a new TLS handshake from the proxy to the panel. The first log request took **6.1 s**. A client should keep its requests sequential, or at least avoid bursts.
