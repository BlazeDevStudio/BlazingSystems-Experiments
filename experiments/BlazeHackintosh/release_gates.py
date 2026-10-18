"""Fail-closed production readiness report for BlazeHackintosh.

Never publish production assets solely because tests, a partial EFI candidate,
or an alpha GitHub Release exists. All required gates need supporting evidence.
"""
from __future__ import annotations
import ipaddress
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "Production" / "RELEASE-GATES.json"
REQUIRED_IDS = frozenset({
    "research-reconciliation",
    "hardware-detection",
    "hardware-db-25",
    "adaptive-efi",
    "smbios-local",
    "efi-generator",
    "ocvalidate",
    "component-auth",
    "installer-online",
    "installer-offline",
    "windows-gui",
    "usb-preparation",
    "efi-zip",
    "esp-img",
    "usb-img",
    "linux-recovery",
    "efi-migration",
    "multiboot",
    "legacy-apple",
    "experimental-pc",
    "boot-diagnostics",
    "hardware-acceptance",
    "release-security",
    "docs-per-folder",
    "ci-build",
    "production-release",
})

ALLOWED = {"verified", "in_progress", "blocked", "unstarted"}

_HOST_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", re.I)


def _valid_evidence_url(value: object) -> bool:
    """Validate public HTTPS URL syntax only; do not fetch or authenticate evidence."""
    if not isinstance(value, str) or not value or len(value) > 2048:
        return False
    if any(ord(c) < 33 or ord(c) > 126 for c in value):
        return False
    try:
        p = urlsplit(value)
        if p.scheme != "https" or not p.netloc or not p.path or p.fragment:
            return False
        if p.username is not None or p.password is not None or p.port not in (None, 443):
            return False
        host = p.hostname
        if not host or host.endswith(".") or host == "localhost":
            return False
        if host.endswith((".localhost", ".local", ".internal", ".test", ".invalid")):
            return False
        try:
            ipaddress.ip_address(host)
            return False
        except ValueError:
            pass
        return len(host.split(".")) >= 2 and all(_HOST_LABEL.fullmatch(label) for label in host.split("."))
    except (ValueError, TypeError):
        return False


def readiness(path: str | Path = DEFAULT) -> dict:
    file = Path(path)
    if file.is_symlink() or not file.is_file() or file.stat().st_size > 1024*1024:
        raise ValueError("Release gate manifest missing or unsafe")
    try:
        doc = json.loads(file.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Malformed release gate manifest") from exc
    if not isinstance(doc, dict) or doc.get("schema_version") != 1:
        raise ValueError("Invalid release-gate schema")
    gates = doc.get("gates")
    if not isinstance(gates, list) or len(gates) < 20:
        raise ValueError("Incomplete production acceptance checklist")
    ids, blockers, checked = set(), [], 0
    for item in gates:
        if not isinstance(item, dict):
            raise ValueError("Invalid release gate entry")
        key, desc = item.get("id"), item.get("description")
        status, evidence, required = item.get("status"), item.get("evidence"), item.get("required")
        if not isinstance(key, str) or not key or key in ids:
            raise ValueError("Duplicate/empty release gate identifier")
        ids.add(key)
        if not isinstance(desc, str) or not desc.strip() or status not in ALLOWED or required is not True:
            raise ValueError("Invalid release gate details")
        if not isinstance(evidence, list) or any(not _valid_evidence_url(u) for u in evidence):
            raise ValueError("Evidence URLs must be valid public HTTPS URLs")
        if status == "verified":
            if not evidence:
                raise ValueError("Verified release gate requires evidence")
            checked += 1
        else:
            blockers.append({"id": key, "status": status, "description": desc})
    if ids != REQUIRED_IDS:
        raise ValueError("Missing or unrecognized mandatory production release gates")
    return {"production_ready": len(blockers) == 0, "gates_total": len(gates),
            "gates_verified": checked, "remaining": len(blockers), "blockers": blockers,
            "notice": "A production-ready result requires independent review of all evidence; this automated checklist alone cannot prove physical boot."}
