# Panel behaviour from the ABUS manuals

Background from the official manuals that explains what the API shows. Paraphrased; section numbers refer to the German user manual 3.01.21 ("BDA"), the installer manual 3.01.31 ("INST") and the iOS app quick guide ("APP"). Nothing here is verified against the API unless stated.

## Zones

- **Numbering** (BDA, technical data): up to 48 wireless zones (Z201 onwards) and up to 4 wired zones on the panel (Z301–Z304; with 4-wire wiring Z301A/Z301T and Z302A/Z302T for alarm and tamper). There are also up to 6 IP (camera) zones and HyMo zones, whose numbering isn't documented.
- **Zone type** is set by the installer. The relevant ones here:
  - *Ein/Ausgang* (entry/exit): alarms only after the entry delay; closing it can end the exit delay. Typical for the front door.
  - *Eingangsweg* (entry route): no alarm while an entry delay is running, otherwise immediate alarm.
  - *Normal Alarm*, *24 h*, *Technik*, *Feuer*, *Überfall*, *Sabotage* and others.
- **Zone properties**, also set by the installer (INST, zone properties):
  - *Ausblendbar* (omittable): the user may omit the zone before arming. This is most likely the API's `omittable`.
  - *Ausblendbar Zwangsaktiv*: the zone is omitted automatically if it is open when arming.
  - *Intern überwacht* (monitored when armed internally). This is most likely the API's `inner`.
- **Omitting** (BDA 10.3): an omitted zone isn't monitored while armed and is **included again automatically at the next disarm**. The omission therefore lasts for one arming cycle.

## Arming

- **What prevents arming** (BDA 8.14):
  - open intrusion zones, except entry-route zones
  - a triggered panic detector
  - system, component or zone tamper
  - communication faults that would prevent alarm transmission
  - supervision faults of wireless components

  Faults that are allowed can be overridden by the user. This matches `prevents-set` in `/faults/`: only blocking faults have it set.
- **Why open entry doors are no fault:** A door of type Ein/Ausgang may be open when arming, because the user leaves through it during the exit delay. That fits the observation that open non-omittable doors don't show up in `/faults/`.
- **Exit and entry delay** (BDA 8.13): 40 s exit delay by default when arming at the keypad; the entry delay gives time to disarm after opening the front door. Through the API the new state was reported immediately. Whether a remote arm skips the delay or the API just doesn't show it is open.
- **Web interface** (BDA 13.3): arming with an open zone "doesn't happen, the lock stays open" — consistent with the API answering 200 and keeping the old state.

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

- **Capacity** (BDA 10.8): at most 600 entries, oldest overwritten first. The unfiltered `/logs/` response had exactly 600 entries.
- **Message texts:** The installer manual has an appendix listing every log message text with its meaning ("Logbuch Einträge").

## App and push

- **Blocking logins** (APP): the app can't connect while an installer **or a user** is logged in at the panel. The API answers `403 {"state":"installer"}` for the installer; whether a logged-in user gives a different `state` is open.
- **Push** (APP): Push notifications have to be enabled per device by an administrator in the web interface (Configuration → Push notifications). So the panel keeps a list of app devices, which fits the `device` header.
- **Outputs** (BDA 12.2, 10.4): The app can switch outputs of type "user defined". How is open, because the test panel has none.
