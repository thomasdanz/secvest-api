#!/usr/bin/env python3
"""Redact captured Secvest responses before they go into fixtures/.

    redact.py IN [OUT]      redact one file (JSON or text), write OUT or stdout
    redact.py --check PATH  fail if any file still contains sensitive data

Rules come from two places:
  - built-in: private/public IPv4 addresses, MAC addresses, e-mail addresses,
    values of JSON keys that look sensitive (serial, mac, code, pin, ...)
  - redact.local.json (gitignored, see redact.example.json): installation
    specific strings such as host names, zone names, user names
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL_RULES = ROOT / "redact.local.json"

# matched against the parts of a key: "serialNumber", "sip_username", "ip-addr";
# plain "user" is left alone, the Secvest uses it for numeric user slots
SENSITIVE_KEY_PARTS = {
    "serial", "sn", "mac", "imei", "iccid", "imsi", "pin", "code", "pass",
    "password", "passwd", "username", "phone", "tel", "sip", "email",
    "mail", "token", "ssid", "secret", "ip", "host", "hostname", "addr", "address",
}
PATTERNS = [
    # IPv4 -> TEST-NET-1 (RFC 5737), keeps the shape of the value
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "192.0.2.1"),
    (re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"), "00:00:5E:00:53:00"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "user@example.com"),
]


def load_local_rules():
    if not LOCAL_RULES.exists():
        return {}
    rules = json.loads(LOCAL_RULES.read_text(encoding="utf-8"))
    # longest first, so "Kitchen window left" wins over "Kitchen"
    return dict(sorted(rules.get("replace", {}).items(), key=lambda kv: -len(kv[0])))


def is_sensitive_key(key):
    parts = re.split(r"[_\-\s.]+|(?<=[a-z])(?=[A-Z])", key)
    return any(part.lower() in SENSITIVE_KEY_PARTS for part in parts)


def redact_text(text, replacements):
    for secret, placeholder in replacements.items():
        text = text.replace(secret, placeholder)
    for pattern, placeholder in PATTERNS:
        text = pattern.sub(placeholder, text)
    return text


def redact_json(value, replacements, key=None):
    if isinstance(value, dict):
        return {k: redact_json(v, replacements, k) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_json(v, replacements, key) for v in value]
    if isinstance(value, str):
        if key and is_sensitive_key(key) and value:
            return "REDACTED"
        return redact_text(value, replacements)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        # e.g. a numeric user code; keep the type
        return 0 if key and is_sensitive_key(key) else value
    return value


def redact_file(path, replacements):
    raw = Path(path).read_text(encoding="utf-8")
    try:
        # the panel sometimes emits raw control characters inside strings
        data = json.loads(raw, strict=False)
    except json.JSONDecodeError:
        return redact_text(raw, replacements)
    return json.dumps(redact_json(data, replacements), indent=2, ensure_ascii=False) + "\n"


def check(paths, replacements):
    findings = []
    for path in paths:
        files = [p for p in Path(path).rglob("*") if p.is_file()] if Path(path).is_dir() else [Path(path)]
        for file in files:
            text = file.read_text(encoding="utf-8", errors="replace")
            for secret in replacements:
                if secret in text:
                    findings.append(f"{file}: contains a string from redact.local.json")
            for pattern, placeholder in PATTERNS:
                for match in pattern.findall(text):
                    if match != placeholder:
                        findings.append(f"{file}: {match}")
    for finding in findings:
        print(finding, file=sys.stderr)
    return 1 if findings else 0


def main(argv):
    replacements = load_local_rules()
    if len(argv) >= 2 and argv[0] == "--check":
        return check(argv[1:], replacements)
    if len(argv) not in (1, 2):
        print(__doc__, file=sys.stderr)
        return 2
    result = redact_file(argv[0], replacements)
    if len(argv) == 2:
        Path(argv[1]).write_text(result, encoding="utf-8")
    else:
        sys.stdout.write(result)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
