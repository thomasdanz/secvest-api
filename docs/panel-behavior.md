# Panel behaviour from the ABUS manuals

Background from the official manuals that explains what the API shows. Paraphrased; section numbers refer to the German user manual 3.01.21 ("BDA"), the installer manual 3.01.31 ("INST") and the iOS app quick guide ("APP"). Nothing here is verified against the API unless stated.

## Zones

- **Numbering** (BDA, technical data): up to 48 wireless zones (Z201 onwards) and up to 4 wired zones on the panel (Z301–Z304; with 4-wire wiring Z301A/Z301T and Z302A/Z302T for alarm and tamper). There are also up to 6 IP (camera) zones, Z101–Z106 (seen in the installer web interface), and HyMo zones, whose numbering isn't documented.
- **Zone type** is set by the installer. The relevant ones here:
  - *Ein/Ausgang* (entry/exit): alarms only after the entry delay; closing it can end the exit delay. Typical for the front door.
  - *Eingangsweg* (entry route): no alarm while an entry delay is running, otherwise immediate alarm.
  - *Normal Alarm*, *24 h*, *Technik*, *Feuer*, *Überfall*, *Sabotage* and others.
- **Zone properties**, also set by the installer (INST, zone properties):
  - *Ausblendbar* (omittable): the user may omit the zone before arming. This is the API's `omittable` — checked against the installer web interface, where exactly the zones with this property report `omittable: true`.
  - *Ausblendbar Zwangsaktiv*: the zone is omitted automatically if it is open when arming.
  - *Intern überwacht* (monitored when armed internally). This is most likely the API's `inner`: the web interface's zone list shows it for all 19 zones of the test panel, which all have `inner: true`, so the comparison can't tell them apart. *Ausblendbar* matched `omittable` for all 19, including the two that aren't omittable.
- **Omitting** (BDA 10.3): an omitted zone isn't monitored while armed and is **included again automatically at the next disarm**. The omission therefore lasts for one arming cycle. Confirmed via the API.
- **Omitting is per zone, not per partition.** *Ausblendbar* is a zone property set by the installer (INST, zone properties), and omitting excludes the detector as such (BDA 10.3). The API matches: one `omitted` per zone, and the log writes "Zone … ausgeblendet" without a partition. The partition in the request path (`/system/partitions-{n}/zones-{z}/`) only routes the request and decides the rights.
- **A zone can belong to several partitions** (INST: "Wenn ein Melder mehreren Teilbereichen zugeordnet ist, …"; zones of type *Nur Logbuch* explicitly). Which partition's disarm includes an omitted shared zone again is not documented and untested (the test panel has no shared zones).

## Arming

- **What prevents arming** (BDA 8.14):
  - open intrusion zones, except entry-route zones
  - a triggered panic detector
  - system, component or zone tamper
  - communication faults that would prevent alarm transmission
  - supervision faults of wireless components

  Faults that are allowed can be overridden by the user. This matches `prevents-set` in `/faults/`: only blocking faults have it set.
- **Arming via the API with an entry door open** (tested with entry/exit door 219): `set` is silently ignored (200, stays unset, no tone), `partset` gets 409 with the door as a blocking fault. At the keypad the exit time covers this case; the API has none.
- **Why open entry doors are no fault:** A door of type Ein/Ausgang may be open when arming, because the user leaves through it during the exit delay. Confirmed on the test panel: both entry/exit doors (zones 216 and 219) are of type Ein/Ausgang and don't show up in `/faults/` when open.
- **Installer web interface** (Komponenten → Funk Zonen) lists per zone its number, name, partitions, type and properties, and status columns for battery low, omitted, supervision fault, tamper, open and signal strength (RSSI). The API's zone object only carries `state` and `omitted` of these. A normal user and an administrator don't see this list in the web interface's menus (tested), but a normal user's session gets it when requesting it directly (captured, see openapi-webui.yaml); see "Users and rights".
- **Signal strength** (INST, installer mode → Test → Signalstärken): a level from 0 to 9 (0 below −101 dBm, then steps of 3 dB, 9 at −77 dBm or more; above 3 is recommended). Shown as two numbers: the level of the last received signal, and in parentheses the lowest level since the last reset of the readings; the panel records them all the time. From firmware 2.00.00 the web interface has two columns, "Direkt" (the component's own signal) and "Repeater" (the signal repeated by a repeater). The user menu's test (BDA 10.7) shows a level only for the remote control or emergency transmitter just pressed.
- **Tamper** ("Sabotage", INST glossary): every component is monitored for tampering, usually by a lid contact (opening the detector) and a wall-removal contact; opening a detector or cutting a cable always raises an alarm, also during the walk test (BDA 10.7.1). Housings are opened by the installer for maintenance only.
- **Supervision** (INST glossary, security settings): wireless components report to the panel about every 4 minutes (zone property *Supervision*, on by default since 3.01.16). After more than 20 minutes without contact the panel logs "RF Warnung" and refuses arming, which a user may override ("RF Warnung übergangen"); presumably the fault field `is-rf-warning` of the REST API. After more than 2 hours it is a supervision fault, which always prevents arming; what else happens is set by the installer (no reaction, fault, or tamper alarm). Which of the two the web interface's supervision column shows is untested.
- **RF repeater** (INST, Komponenten → RF Repeater): up to 4 repeaters, each repeating at most 10 components. Which detectors, keypads, door locks, sirens, indoor sounders and hybrid modules a repeater repeats is chosen by the installer per repeater ("Repeat Melder" etc.); remote controls and emergency transmitters in range are always repeated. "Repeat Zentrale" decides whether the panel's own messages (keypad status, sirens, outputs, …) are repeated. The repeater's signal strength page shows, per component, the level at which the repeater receives it, and the levels between panel and repeater in both directions.
- **Exit and entry delay** (BDA 8.13): 40 s exit delay by default when arming at the keypad; the entry delay gives time to disarm after opening the front door.
- **Exit time in practice** (tested on the test panel, delayed arming with 15 s exit time):

  | Armed via | partset | set |
  |---|---|---|
  | App or API | immediately | immediately, no exit time |
  | Keypad | immediately | 15 s of exit tones, then armed |

  While the exit time runs after arming at the keypad, the API keeps reporting `unset` and switches to `set` only when it is over. The API has no "arming" state.
- **Partition settings** (INST, partitions), separately for full arming, internal arming, disarmed and panic:
  - *Exit mode*: delayed arming (after the exit time, with warning tones), silent arming (same without tones), immediate arming, arming when the last entry/exit door closes (no fixed time), arming by a lock contact at the door, or ending the exit via a dedicated button zone.
  - *Exit time* and *entry time*: 10–120 s each. The test panel uses delayed arming with 15 s exit and 25 s entry time.
    - The exit time is how long the user has to leave through an entry/exit door after starting to arm. Exceeding it is an alarm type of its own.
    - The entry time starts when an entry/exit door opens while armed; the user has to disarm within it or an intrusion alarm follows. Entry-route zones don't alarm while it runs.
  - *Alarm reaction*: internal only, sirens, sirens + reporting to an alarm receiving centre, or flash variants; plus a siren delay and the external siren duration.
  - The *internal arming* tab has its own exit mode, exit and entry time and alarm reaction. It also has **"Ein/Aus bei Intern als"**, which decides how entry/exit doors behave when armed internally: still as entry/exit (with entry time) or as *Normal Alarm* (immediate alarm when opened).
  - Test panel settings:

    | | Full arming (set) | Internal arming (partset) |
    |---|---|---|
    | Exit mode | delayed, 15 s | immediate |
    | Entry time | 25 s | 40 s |
    | Alarm reaction | sirens + reporting to a receiving centre | sirens only |
    | Entry/exit doors when internal | – | stay entry/exit |

  - With immediate internal arming there is no exit time to leave through an open door, which is presumably why an open entry/exit door blocks partset with 409. Full arming via the API also skips the exit time, but there the request is silently ignored instead.
- **Entry time in detail** (BDA 8.13, INST):
  - Opening an entry/exit door while armed starts the entry time with a pulsed tone, and the log records "Eing gest. Z<zone>".
  - The user has to disarm before it runs out, otherwise an intrusion alarm follows. Closing the door again doesn't stop it; only the special exit mode with a lock contact allows re-locking before the entry time has started.
  - Entry-route zones may trigger during the entry time. Any other zone counts as leaving the entry route: depending on the setting "Eingang Alarm Verzögerung" either an immediate full alarm, or 30 s of internal alarm first (log "Eing. Weg verlass. Z…" / "Eingang Abweichung Z…").
  - Tested for set and partset via the API: opening entry/exit door 219 after arming started the entry time (pulsed tone until disarmed), no new fault appeared in `/faults/` meanwhile, and disarming with `unset` within the entry time ended it without an alarm.
  - The log records "Eing gest. Z219" a few seconds after arming, when the door was opened, for set and partset alike. The zone is only in the text. During the entry time `/alarms/` stays `[]` and `/faults/` shows nothing new (checked); the partition state stays `set`/`partset` (checked). So this log entry is the only way for a client to notice it; since log requests take about 6 s, that is slow compared to a 25 s entry time.
- **Web interface** (BDA 13.3): arming with an open zone doesn't happen, the lock stays open. The API answers such a request with `409 Conflict` and the list of blocking faults.

## Alarms

- **Alarm types** (BDA 9.1): tamper, intrusion, panic, technical, fire, care/medical emergency, entry delay exceeded, exit delay exceeded.
- **Signalling** depends on the arming state and configuration: internal, local, external or silent alarm.
- **/alarms/ format** (firmware inference): there is no dedicated alarm serializer; the shared event serializer used for /faults/ is the only one emitting these keys, so an /alarms/ entry most likely has the same shape as a fault entry, of which the app reads only id/type/affects-partition. Not confirmed during a real alarm.
- **Alarm states in the API** (confirmed by the firmware's partition serializer, and by a test alarm recorded by another project): the partition `state` is built from the arm state plus two flags (alarm active, alarm acknowledged), giving `set`/`partset`/`unset`, their hyphenated `*-alarm` variants and `acknowledged`. The alarm is therefore visible in `state`; `/faults/` stays empty during an alarm. A bare `alarm` string is never written.
- **After an alarm** (BDA 9, 13.3):
  1. Disarm.
  2. Acknowledge the alarm ("quittieren").
  3. Reset the panel ("rücksetzen").

  Only then can the panel be armed again. If the reset is skipped, it is requested again at the next arming.
- **Via the app**, an alarm is acknowledged by setting the partition state to `acknowledged` (Android app, not tried). The app has no call for the reset.
- **Via the web interface** (BDA 13): acknowledge by selecting the red (alarmed) partition and confirming; then reset with the "!" symbol that appears in the partition, again confirmed. At the keypad, the reset is requested after disarming; if skipped, it is asked for again at the next arming (BDA 9).
- **Who may reset** is configured by the installer (INST, "Benutzer Rückstellung"), separately for zone alarms, zone tamper and system tamper. If the user may not, the installer has to reset. Tamper alarms often need the installer. `prevents-reset` in `/faults/` presumably marks faults that block the reset.
- **Remote control by phone** (BDA 11.4) has commands for disarm, arm, arm internally, silence sirens, **reset**, status query and switching outputs by their 3-digit number. The API may offer equivalents.
- **Alarm transmission** (BDA 9.2): phone call (analogue or VoIP), alarm receiving centre, e-mail with the alarm text, SMS, push to the app. A phone alarm call is acknowledged with DTMF 5 (end this call, continue the chain) or 9 (stop the whole call chain).

## Push notifications (firmware)

The firmware contains what looks like the payload the panel sends for push notifications (`system-name`, `mac`, `event`, `is-fault`, `is-restore`, `zone`, `zone-name`, `user`, `username`, `text`, `timestamp`, `sia`, `group`, …) and a list of event categories (`fire`, `medical`, `burg`, `technical`, `tamper`, `set-unset`, `part-set`, `reset`, `exit-timeout`, `omit`, `rf-supervision`, `rf-jamming`, `rf-battery-psu`, `panel-battery`, `panel-mains`, `faults`, `installer-mode`, `user-code-change`, `time-date-reset`, `camera-supervision`, …). Push is delivered through ABUS, not through the local API, so this is background only.

## Users and rights

- **User levels** (BDA 10.1): *Normaler Benutzer* (normal user) and *Administrator*, plus a duress code user ("Bedrohungscode", disarms seemingly normally but raises a silent alarm). A normal user can't manage other users and doesn't see some menus (e.g. contacts, info, panel restart); an administrator also has access to the system configuration.
- **Partition rights** are set per user: arming/disarming permission for each of the four partitions (BDA 10.1, step 6).
- **Web interface menus by level:** a normal user and an administrator see neither the components (e.g. Funk Zonen) nor the signal strengths in the web interface (tested with both). The manuals show them only in the installer's menu. The main page carries the menus of every level and only hides those of the other levels (captured, see openapi-webui.yaml). A level 4 user (software updates) sees only their name, code and the panel upgrade (INST). The panel doesn't check the level for reading, though: a normal user's session got the wireless zone list and its data, signal strengths included, when requesting it directly (captured 2026-10-10, see openapi-webui.yaml).
- **Installer code** (INST, Errichter Code): enters installer mode and performs an installer reset, but **cannot arm or disarm** the panel. It can't use the REST API either: requests with the installer's credentials get the same `401` as wrong credentials (tested).
- **Who may reset after an alarm** is set by the installer in "Benutzer Rückstellung", separately for zone alarms, zone tamper and system tamper (INST). If disabled, only the installer can reset. Disabling zone and system tamper reset is required for INCERT approval.
- **In the API, reads don't depend on the user** (tested with a normal user allowed to operate only partition 1): the responses match an administrator's — all partitions, unfiltered faults and log.
- **Commands do** (tested with the same user, rights changed to partition 2 only): omitting or including a zone of partition 1 gives the empty 403, the same answer as for a zone that isn't omittable. Setting partition 1's state gives the empty 403 as well — set, partset and even unset (tested with the open zones omitted by an administrator). Only when zones are open, set and partset answer the same 409 with those zones as for an authorised user: blocking faults are evaluated first, so that answer doesn't reveal the missing rights. By the same order, an open entry/exit door presumably makes `set` a silent no-op for such a user as well, instead of the 403 (inferred, not tested with an open entry/exit door).
- **A normal user with rights for the partition** omits and includes zones, arms (set and partset) and disarms exactly like an administrator; omitting an open zone removes its fault (checked with zone 209). The log records the actions with the user's slot number.
- **A partition without zones** can't be armed: set and partset give 409 with an empty list; unset answers 200.

## Failed logins

- Failed logins at the web interface raise a **"Webserver Code Sabotage"** alarm (confirmed on the test panel: an internal alarm with the internal sounders). Wrong codes at the keypad give "Zentrale Code Sabotage". The threshold isn't documented; two failed web logins in a row (an administrator whose password contained `&`, see below) raised no alarm, so it is more than two. A failed web login is answered with the login page again (session id `0`, a red error text) and leaves no log entry (seen once, 2026-10-10), so failed web logins can't be seen in the log.
- A single request to the REST API with wrong credentials (401) did not raise an alarm, and neither did three 401s in a row (with the installer's credentials). They didn't leave a log entry either. Whether more 401s count towards code tamper is unknown; this was deliberately not tested further, to avoid triggering an alarm.
- **`&` in the password:** an administrator whose remote password ("Fern-Passwort") contains `&` could no longer log in at the web interface, while the app and the REST API accepted it (tested). Presumably the web server decodes the login form before splitting it at `&`. Passwords with `_`, `!`, `-`, `*`, digits and letters work at the web interface (seen with other users); umlauts are untested. A client of the web interface should refuse such a password instead of sending a login that is bound to fail and counts towards code tamper.
- Therefore: never retry automatically after a 401 or a failed web login.

## Log

- **Capacity** (BDA 10.8): at most 600 entries, oldest overwritten first. The unfiltered `/logs/` response had exactly 600 entries. "Oldest" means oldest written, not the smallest timestamp, since timestamps aren't monotonic (e.g. after a restart before the clock is set).
- **Timestamps** are local wall-clock time encoded as Unix seconds, so they are off by the UTC offset if read as real Unix time. Recorded pair (2026-10-03): a disarm answered with `Date: Sat, 03 Oct 2026 18:25:01 GMT` wrote an entry with timestamp `1791059101`, which read as UTC is 20:25:01, the local time in CEST.
- **Partition numbers in log events** are zero-based (`"0"` = partition 1), while the text counts from 1 ("TB 1").
- **Arming** is logged the same way whether it comes from the keypad, the app or the API. An arming despite a pending warning also logs "Übergehen" (override; installer manual, log messages: "B--TB # Übergehen" = the user armed despite a warning). Arming from the app or the API is a form of quick arming ("Schnellaktiv"), which passes over warnings without asking but logs them. So most recorded armings have the entry: they were made while a repeater reported a low battery. After its battery had been replaced, arming partition 1 with partset through the API with three omitted zones logged none (2026-10-03). An omitted zone is logged when the partition is armed with it and again ("… ok") when it is included at disarm. Rejected attempts (409, 403 for missing rights) leave no entry, and neither does disarming a partition that is already unset or a failed API login (401).
- **Web interface sessions** write "Ben<nnn> Log in (Web)" at the login and "Ben<nnn> Log out(Web)" at the logout, nothing else (seen for a normal user, 2026-10-10); "Anmelden"/"Abmelden" from the manual's list didn't appear.
- **Message texts:** The installer manual has an appendix listing every log message text with its meaning ("Logbuch Einträge").

## App and push

- **Blocking logins** (APP): according to the guide the app can't connect while an installer **or a user** is logged in at the panel. Tested: only the installer locks the API (`403 {"state":"installer"}`), logged in at the keypad or at the web interface; with a normal user logged in at the keypad or at the web interface (also the same user as the API requests) the API works as usual.
- **Push** (APP): Push notifications have to be enabled per device by an administrator in the web interface (Configuration → Push Mitteilungen). The list shows number, device name, user, an access checkbox ("Zugriff") and a delete button. The app adds an entry via `PUT /register/` whenever the panel's connection settings are saved in the app; new entries start without access. None of the manuals describes the page itself.
- **Outputs** (BDA 12.2, 10.4): The app can switch outputs of type "user defined". How is open, because the test panel has none.
