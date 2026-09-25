# Firmware reverse engineering

What the panel firmware answered where the live API and the app couldn't. Derived from firmware **v3.01.31** (FUAA50500). The firmware image itself is not in this repository.

## Target

- **Processor:** STM32, i.e. ARM Cortex-M, 32-bit, **little-endian**, Thumb-2 instructions.
- **Image:** the raw firmware `.bin` is **not encrypted** (entropy varies by region; a plain vector table at the start). It runs execute-in-place from flash, so it loads at base address **`0x08000000`** — the first word is the initial stack pointer (into RAM `0x2000_xxxx`), the second is the reset vector (into flash `0x080x_xxxx`); both only make sense read little-endian, which confirms the endianness.
- Keep firmware images and anything extracted from them out of the repository.

## Method that worked

String-anchored navigation was the productive approach:

1. Open **Window → Defined Strings**, filter for a known JSON key (`partitions`, `affects-partition`, `is-rf-warning`, an alarm state like `set-alarm`, …).
2. **Show References to** the string → jump into the function that emits it.
3. Read the decompiled function; the sequence of field-emitting calls with their key-string arguments gives the exact JSON structure.
4. Rename functions as they are identified so the graph stays readable.

The REST responses are built by a **shared serializer framework** with a format-flag parameter that switches JSON vs. the web interface's XML. Small helpers emit one field each (a number, a string, a byte/bool, an array) and open/close an object in either format. Once these helpers were named, every object serializer read cleanly.

Two space-saving tricks in the firmware are worth knowing: strings are reused by **suffix** (`"alarm"` is the tail of `"set-alarm"`, `"partition"`/`"zone"` are tails of `"affects-partition"`/`"affects-zone"`), which makes a reference search land on a neighbour; and single strings appear once and are shared.

Practical tip: query the strings in the REST region specifically rather than dumping the whole image; the focused lookups above answer the API questions directly.

## Results

Confirmed directly from the code (all folded into `openapi.yaml` and `docs/panel-behavior.md`):

- **Partition state** is built from the arm state plus two flags (alarm active, acknowledged), producing `set`/`partset`/`unset`, their hyphenated `*-alarm` variants and `acknowledged`. So an alarm shows up in the partition `state`; `/alarms/` is only needed for detail. `id` is 1-based (index + 1).
- **Camera** object field order, including that it carries the camera password.
- **Fault** entry serializer: `ui-string` and `affects-zone` are optional (`affects-zone` omitted when `0xffff`); `prevents-set`/`prevents-reset` are computed from the id.
- **Log** entry: `type` is `normal`/`trouble`/`alarm`; event fields `timestamp` always, `partition`/`zone`/`user`/`username`/`images` conditional.
- **Output** object has `ontime`/`offtime`/`days-of-week` beyond the app's fields.
- **`/alarms/` (inference):** there is no dedicated alarm serializer; the only function emitting these keys is the shared event serializer used for `/faults/`, so an alarm entry most likely has the same shape as a fault entry, of which the app reads a subset.

### Function map (v3.01.31, base 0x08000000)

| Address | Name | Role |
|---|---|---|
| `0x0803defa` | serialize_partition | one partition `{id,name,state,zones}` |
| `0x0803deb4` | serialize_partition_zones | the `zones` array of a partition |
| `0x0803e792` | serialize_camera | one camera |
| `0x0803e0c8` | serialize_event_entry | one fault/event entry (faults only) |
| `0x0803e1c8` | serialize_faults | the `/faults/` array (paged) |
| `0x0803ee20` | serialize_log_entry | one log entry with its events |
| `0x08089a2e` | get_partition_arm_state | 0x40=set, 0x60=partset, 0xc0=special, else unset |
| `0x0800909c` | partition_in_alarm | alarm-active flag |
| `0x0800a0cc` | partition_alarm_acknowledged | acknowledged flag |

These are the entry points to resume from; addresses are firmware-version specific.

## Limits and problems

- **The endpoint dispatch could not be reached.** The route handlers are invoked indirectly: there is no absolute pointer table to the endpoint name strings or to the handler functions (a full-image search for pointers to both found nothing), and the names are referenced in a way that is out of `adr` range. So `serialize_faults` has no discoverable callers, and the `/alarms/` handler was never located — hence the `/alarms/` format is inferred, not read.
- **Ghidra mis-analysed some data as code.** The contiguous endpoint-name blob was disassembled as instructions, so those names aren't defined strings and don't resolve as reference targets.
- **The decompiler lost register tracking** in places (many `extraout_r2`/`extraout_r3` variables). The number and order of emitted fields stays reliable (it comes from the key-string arguments), but the exact variable feeding a given field is not. Setting a called function's signature by hand recovers many of these.

