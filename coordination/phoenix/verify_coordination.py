#!/usr/bin/env python3
"""Offline, fail-closed checks for the Phoenix coordination contract.

Run: python3 coordination/phoenix/verify_coordination.py
No network access, dependencies, production writes or live device operations.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
ROLES = frozenset({
    "PHX-MASTER", "PHX-CORE", "PHX-RENTAL", "PHX-PISONET",
    "PHX-HARDWARE", "PHX-QA", "PHX-RELEASE",
})
REQUIRED_FILES = (
    "ARCHITECTURE_CONTRACTS.md", "ROLE_ASSIGNMENTS.md",
    "INTEGRATION_MATRIX.md", "AUDIT_SUMMARY.md",
    "REPOSITORY_ROUTING.md", "OWNERSHIP_ROUTES.json",
    "COMMUNICATION_EXAMPLE.json",
)
REQUIRED_KEYS = frozenset({
    "protocol", "message_id", "from", "to", "type", "priority",
    "task_id", "branch", "base_sha", "scope", "status",
    "evidence", "blockers", "next_action", "updated_utc",
})
TYPES = frozenset({"ASSIGN", "ACK", "PROGRESS", "BLOCKER", "REQUEST_REVIEW", "DONE", "DECISION"})
STATUSES = frozenset({"QUEUED", "IN_PROGRESS", "BLOCKED", "PR_READY", "VERIFIED", "MERGED"})


def safe_repo_path(value: object) -> bool:
    """Reject traversal, absolute paths and ambiguous Windows separators."""
    if (not isinstance(value, str) or not value or value.startswith("/") or "//" in value
            or "\\" in value or re.fullmatch(r"[A-Za-z0-9._/-]+", value) is None):
        return False
    return all(part not in ("", ".", "..") for part in value.rstrip("/").split("/"))


def validate_routes(data: object, repo_root: Path) -> list[str]:
    """Check real ownership (not merely role-name substrings in a document)."""
    errors: list[str] = []
    if not isinstance(data, dict) or data.get("schema") != "phoenix/ownership-routes/v1":
        return ["Unsupported ownership manifest schema"]
    if data.get("status") != "DRAFT_REVIEW_ONLY":
        errors.append("Manifest must remain explicitly draft/review-only")
    routes = data.get("routes")
    if not isinstance(routes, list) or not routes:
        return errors + ["Ownership routes must be a nonempty list"]

    seen_roles: set[str] = set()
    paths: list[tuple[str, str]] = []
    for index, route in enumerate(routes, start=1):
        if not isinstance(route, dict):
            errors.append(f"route {index}: not an object")
            continue
        role, source, target = route.get("role"), route.get("source"), route.get("target")
        # Master owns the coordination inbox and contracts, never runtime migration.
        if role == "PHX-MASTER" and (
            source != "coordination/phoenix/"
            or target is not None
            or route.get("kind") != "coordination-only"
        ):
            errors.append(
                f"route {index}: MASTER is coordination-only; no runtime source/destination"
            )
        # A draft routing inventory is not an executable migration authorization.
        if "copy_permitted" in route and route["copy_permitted"] is not False:
            errors.append(f"route {index}: DRAFT route cannot authorize copy")
        if not isinstance(role, str) or role not in ROLES:
            errors.append(f"route {index}: unknown role {role!r}")
        else:
            seen_roles.add(role)
        if not safe_repo_path(source):
            errors.append(f"route {index}: invalid source path {source!r}")
            continue
        path = repo_root / source.rstrip("/")
        if not path.exists():
            errors.append(f"route {index}: source does not exist at checkout: {source}")
        elif source.endswith("/") and not path.is_dir():
            errors.append(f"route {index}: source expected a directory: {source}")
        elif not source.endswith("/") and not path.is_file():
            errors.append(f"route {index}: source expected a file: {source}")
        if target is not None and not safe_repo_path(target):
            errors.append(f"route {index}: unsafe destination path {target!r}")
        if role != "PHX-MASTER" and target is None:
            errors.append(f"route {index}: non-MASTER route needs a proposed destination")
        for previous, previous_role in paths:
            a, b = source.rstrip("/").casefold(), previous.rstrip("/").casefold()
            if a == b or a.startswith(b + "/") or b.startswith(a + "/"):
                errors.append(
                    f"route {index}: overlapping ownership {source!r} ({role}) "
                    f"and {previous!r} ({previous_role})"
                )
        paths.append((source, str(role)))
    # Destination overlap is not necessarily an ownership collision, but is
    # dangerous for automated recursive migrations. Block unless the broader
    # path explicitly requires a manual per-file mapping and prohibits copying.
    claims = [
        route for route in routes
        if isinstance(route, dict) and safe_repo_path(route.get("target"))
    ]
    for index, a in enumerate(claims):
        a_path = a["target"].rstrip("/").casefold()
        for b in claims[:index]:
            b_path = b["target"].rstrip("/").casefold()
            if a_path == b_path:
                errors.append(f"Duplicate destination claim: {a['target']}")
                continue
            if a_path.startswith(b_path + "/"):
                parent, child = b, a
            elif b_path.startswith(a_path + "/"):
                parent, child = a, b
            else:
                continue
            if parent.get("role") != child.get("role"):
                errors.append(
                    f"Cross-role destination claims overlap: "
                    f"{parent['target']} / {child['target']}"
                )
                continue
            if (
                parent.get("kind") != "manual-file-mapping-required"
                or parent.get("copy_permitted") is not False
                or not isinstance(parent.get("review_reason"), str)
                or not parent["review_reason"].strip()
            ):
                errors.append(
                    f"Unreviewed destination claims overlap: "
                    f"{parent['target']} / {child['target']}; "
                    "broader path must prohibit copy and require a manual file map"
                )
    missing = ROLES - seen_roles
    if missing:
        errors.append("Roles missing from ownership routes: " + ", ".join(sorted(missing)))
    return errors


def validate_envelope(data: object) -> list[str]:
    """Validate an actual JSON envelope file, never a hard-coded dict inside the checker."""
    if not isinstance(data, dict):
        return ["BLAZE-COMMS/1 envelope must be an object"]
    errors = ["Missing envelope key: " + k for k in sorted(REQUIRED_KEYS - data.keys())]
    if data.get("protocol") != "BLAZE-COMMS/1":
        errors.append("Wrong protocol")
    if not isinstance(data.get("from"), str) or data["from"] not in ROLES:
        errors.append("Unknown sending role")
    recipient = data.get("to")
    if not isinstance(recipient, str) or not recipient.strip():
        errors.append("Missing recipient")
    elif recipient not in ROLES and recipient != "ALL":
        # BLAZE-COMMS/1 accepts one exact registered role or ALL.
        # Never silently accept a partial/multi-target string with an unknown role.
        errors.append("Invalid recipient: expected a registered role or ALL")
    if not isinstance(data.get("type"), str) or data["type"] not in TYPES:
        errors.append("Invalid message type")
    if not isinstance(data.get("status"), str) or data["status"] not in STATUSES:
        errors.append("Invalid status")
    if data.get("priority") not in ("P0", "P1", "P2"):
        errors.append("Invalid priority")
    for key in ("message_id", "task_id", "next_action"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"Invalid {key}")
    for key in ("scope", "evidence", "blockers"):
        value = data.get(key)
        if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
            errors.append(f"{key} must be a list of strings")
    if not isinstance(data.get("branch"), (str, type(None))):
        errors.append("Invalid branch")
    sha = data.get("base_sha")
    if sha is not None and (not isinstance(sha, str) or re.fullmatch(r"[a-f0-9]{40}", sha) is None):
        errors.append("base_sha must be a full 40-digit hex SHA or null")
    try:
        stamp = data["updated_utc"]
        if not isinstance(stamp, str) or not stamp.endswith("Z"):
            raise ValueError("not UTC Z")
        date = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if date.tzinfo != timezone.utc:
            raise ValueError("not UTC")
    except (KeyError, ValueError, TypeError):
        errors.append("updated_utc must be UTC ISO8601 ending Z")
    return errors


def run_checks() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = HERE / name
        if not path.is_file():
            errors.append("Missing coordination file: " + name)
        elif path.stat().st_size == 0:
            errors.append("Empty coordination file: " + name)
    if errors:
        return errors
    try:
        manifest = json.loads((HERE / "OWNERSHIP_ROUTES.json").read_text(encoding="utf-8"))
        example = json.loads((HERE / "COMMUNICATION_EXAMPLE.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return ["Invalid JSON fixture: " + str(exc)]
    errors.extend(validate_routes(manifest, REPO_ROOT))
    errors.extend(validate_envelope(example))
    assignments = (HERE / "ROLE_ASSIGNMENTS.md").read_text(encoding="utf-8")
    for role in sorted(ROLES):
        if role not in assignments:
            errors.append("Undocumented role: " + role)
    for name in ("ARCHITECTURE_CONTRACTS.md", "AUDIT_SUMMARY.md"):
        if "NO-GO" not in (HERE / name).read_text(encoding="utf-8"):
            errors.append(name + ": production NO-GO gate absent")
    return errors


def main() -> int:
    issues = run_checks()
    if issues:
        for issue in issues:
            print("FAIL:", issue, file=sys.stderr)
        print(f"Phoenix coordination: {len(issues)} failure(s)", file=sys.stderr)
        return 1
    print("Phoenix coordination: PASS — file, scope, protocol and NO-GO checks")
    print("NOTE: This is static coordination validation, NOT CI/hardware/payment acceptance.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
