# Panel behaviour from the ABUS manuals

Background from the official manuals that explains what the API shows. Paraphrased; section numbers refer to the German user manual 3.01.21 ("BDA"), the installer manual 3.01.31 ("INST") and the iOS app quick guide ("APP"). Nothing here is verified against the API unless stated.

## Zones

- **Numbering** (BDA, technical data): up to 48 wireless zones (Z201 onwards) and up to 4 wired zones on the panel (Z301–Z304; with 4-wire wiring Z301A/Z301T and Z302A/Z302T for alarm and tamper). There are also up to 6 IP (camera) zones and HyMo zones, whose numbering isn't documented.
- **Zone type** is set by the installer. The relevant ones here:
  - *Ein/Ausgang* (entry/exit): alarms only after the entry delay; closing it can end the exit delay. Typical for the front door.
  - *Eingangsweg* (entry route): no alarm while an entry delay is running, otherwise immediate alarm.
  - *Normal Alarm*, *24 h*, *Technik*, *Feuer*, *Überfall*, *Sabotage* and others.
- **Zone properties**, also set by the installer (INST, zone properties):
  - *Ausblendbar* (omittable): the user may omit the zone before arming. This is the API's `omittable` — checked against the installer web interface, where exactly the zones with this property report `omittable: true`.
  - *Ausblendbar Zwangsaktiv*: the zone is omitted automatically if it is open when arming.
  - *Intern überwacht* (monitored when armed internally). This is most likely the API's `inner`.
- **Omitting** (BDA 10.3): an omitted zone isn't monitored while armed and is **included again automatically at the next disarm**. The omission therefore lasts for one arming cycle. Confirmed via the API.

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
- **Installer web interface** (Komponenten → Funk Zonen) lists per zone its number, name, partitions, type and properties, and status columns for battery low, omitted, supervision fault, tamper, open and signal strength (RSSI). The API's zone object only carries `state` and `omitted` of these.
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
- **Web interface** (BDA 13.3): arming with an open zone doesn't happen, the lock stays open. The API answers such a request with `409 Conflict` and the list of blocking faults.

## Alarms

- **Alarm types** (BDA 9.1): tamper, intrusion, panic, technical, fire, care/medical emergency, entry delay exceeded, exit delay exceeded.
- **Signalling** depends on the arming state and configuration: internal, local, external or silent alarm.
- **After an alarm** (BDA 9, 13.3):
  1. Disarm.
  2. Acknowledge the alarm ("quittieren").
  3. Reset the panel ("rücksetzen").

  Only then can the panel be armed again. If the reset is skipped, it is requested again at the next arming.
- **Who may reset** is configured by the installer (INST, "Benutzer Rückstellung"), separately for zone alarms, zone tamper and system tamper. If the user may not, the installer has to reset. Tamper alarms often need the installer. `prevents-reset` in `/faults/` presumably marks faults that block the reset.
- **Remote control by phone** (BDA 11.4) has commands for disarm, arm, arm internally, silence sirens, **reset**, status query and switching outputs by their 3-digit number. The API may offer equivalents.
- **Alarm transmission** (BDA 9.2): phone call (analogue or VoIP), alarm receiving centre, e-mail with the alarm text, SMS, push to the app. A phone alarm call is acknowledged with DTMF 5 (end this call, continue the chain) or 9 (stop the whole call chain).

## Log

- **Capacity** (BDA 10.8): at most 600 entries, oldest overwritten first. The unfiltered `/logs/` response had exactly 600 entries. "Oldest" means oldest written, not the smallest timestamp, since timestamps aren't monotonic (e.g. after a restart before the clock is set).
- **Timestamps** are local wall-clock time encoded as Unix seconds, so they are off by the UTC offset if read as real Unix time.
- **Arming** is logged the same way whether it comes from the keypad, the app or the API. Every arming also logs an "Übergehen" (override) entry. An omitted zone is logged when the partition is armed with it and again ("… ok") when it is included at disarm. Rejected attempts (409) leave no entry.
- **Message texts:** The installer manual has an appendix listing every log message text with its meaning ("Logbuch Einträge").

## App and push

- **Blocking logins** (APP): according to the guide the app can't connect while an installer **or a user** is logged in at the panel. Tested: only the installer locks the API (`403 {"state":"installer"}`); with a normal user logged in at the keypad the API works as usual.
- **Push** (APP): Push notifications have to be enabled per device by an administrator in the web interface (Configuration → Push Mitteilungen). The list shows number, device name, user, an access checkbox ("Zugriff") and a delete button. The app adds an entry via `PUT /register/` whenever the panel's connection settings are saved in the app; new entries start without access. None of the manuals describes the page itself.
- **Outputs** (BDA 12.2, 10.4): The app can switch outputs of type "user defined". How is open, because the test panel has none.
