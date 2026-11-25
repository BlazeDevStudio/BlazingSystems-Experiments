#!/usr/bin/env python3
"""Validate the PHX-ANDROID scoped acceptance ledger and report conservative progress.

This file never edits the ledger. Its numbers are PHX-ANDROID PROVISIONAL,
not PHX-MASTER's authoritative deduplicated ecosystem denominator.
"""
import argparse
import json
import math
import sys
from pathlib import Path

STATUSES = {
    "NOT STARTED", "IN PROGRESS", "IMPLEMENTED", "VERIFICATION PENDING",
    "VERIFIED", "FAILED", "BLOCKED", "UNKNOWN", "NOT APPLICABLE"
}
DIMENSIONS = (
    "implementation", "functional", "integration", "qa_security",
    "release", "deployment", "actual_deployment"
)


class LedgerInvalid(ValueError):
    pass


def _pct(numerator, denominator):
    return round(100.0 * numerator / denominator, 4) if denominator else None


def _bar(percentage):
    if percentage is None:
        return "?" * 20
    count = max(0, min(20, math.floor(percentage / 5.0)))
    return "#" * count + "." * (20 - count)


def calculate(ledger):
    if not isinstance(ledger, dict):
        raise LedgerInvalid("ledger root must be a JSON object")
    if ledger.get("schema") != "phoenix/android-workstream-acceptance/v1":
        raise LedgerInvalid("unexpected acceptance ledger schema")
    if ledger.get("scope_status") != "PROVISIONAL_PENDING_PHX_MASTER":
        raise LedgerInvalid("this workstream must not impersonate a global roadmap")
    criteria = ledger.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        raise LedgerInvalid("criteria must be a nonempty array")
    if set(ledger.get("readiness_dimensions", [])) != set(DIMENSIONS[:-1]):
        raise LedgerInvalid("readiness dimensions cannot omit a mandatory category")
    if ledger.get("deployment_dimension") != DIMENSIONS[-1]:
        raise LedgerInvalid("actual deployment must be measured separately")

    seen = set()
    by_dimension = {name: {"total_weight": 0, "verified_weight": 0,
                           "unknown_weight": 0, "evidence_weight": 0,
                           "applicable_count": 0, "verified_count": 0}
                    for name in DIMENSIONS}
    counts = {state: 0 for state in STATUSES}
    for item in criteria:
        if not isinstance(item, dict):
            raise LedgerInvalid("criterion must be an object")
        cid = item.get("id")
        if not isinstance(cid, str) or not cid.startswith("PXA-") or cid in seen:
            raise LedgerInvalid("criterion id absent, duplicated or not PHX-ANDROID")
        seen.add(cid)
        dim = item.get("dimension")
        if dim not in by_dimension:
            raise LedgerInvalid(cid + ": unsupported dimension")
        status = item.get("status")
        if status not in STATUSES:
            raise LedgerInvalid(cid + ": invalid status")
        weight = item.get("weight")
        if type(weight) is not int or weight <= 0:
            raise LedgerInvalid(cid + ": weight must be a positive fixed integer")
        if item.get("mandatory") is not True:
            raise LedgerInvalid(cid + ": mandatory criterion omitted from this denominator")
        if not isinstance(item.get("requirement_sources"), list) or not item["requirement_sources"]:
            raise LedgerInvalid(cid + ": original requirement source missing")
        if not isinstance(item.get("acceptance_criterion"), str) or not item["acceptance_criterion"].strip():
            raise LedgerInvalid(cid + ": objective acceptance criterion missing")
        if not isinstance(item.get("verification_method"), str) or not item["verification_method"].strip():
            raise LedgerInvalid(cid + ": verification method missing")
        if status == "VERIFIED":
            if not item.get("verified_commit") or not item.get("verified_at_utc") or not item.get("evidence"):
                raise LedgerInvalid(cid + ": VERIFIED without exact version, date and evidence")
        if status == "NOT APPLICABLE" and not item.get("not_applicable_rationale"):
            raise LedgerInvalid(cid + ": NOT APPLICABLE needs an approved scope decision")
        counts[status] += 1
        if status == "NOT APPLICABLE":
            continue
        bucket = by_dimension[dim]
        bucket["total_weight"] += weight
        bucket["applicable_count"] += 1
        if item.get("evidence"):
            bucket["evidence_weight"] += weight
        if status == "UNKNOWN":
            bucket["unknown_weight"] += weight
        if status == "VERIFIED":
            bucket["verified_weight"] += weight
            bucket["verified_count"] += 1

    for dim, expected in ledger.get("known_dimension_weights", {}).items():
        if dim not in by_dimension or by_dimension[dim]["total_weight"] != expected:
            raise LedgerInvalid(dim + ": scope denominator drifted without revision")

    readiness = [by_dimension[name] for name in ledger["readiness_dimensions"]]
    verified = sum(x["verified_weight"] for x in readiness)
    total = sum(x["total_weight"] for x in readiness)
    if not total:
        raise LedgerInvalid("readiness denominator is zero")

    for bucket in by_dimension.values():
        denom = bucket["total_weight"]
        bucket["verified_percent"] = _pct(bucket["verified_weight"], denom)
        bucket["bar20"] = _bar(bucket["verified_percent"])
    unresolved = total - verified
    result = {
        "schema": "phoenix/android-provisional-progress/v1",
        "revision": ledger.get("revision"),
        "measurement_status": "PROVISIONAL",
        "scope": ledger.get("scope"),
        "readiness_verified_weight": verified,
        "readiness_total_weight": total,
        "readiness_verified_percent": _pct(verified, total),
        "readiness_bar20": _bar(_pct(verified, total)),
        "readiness_unverified_weight": unresolved,
        "readiness_unknown_weight": sum(x["unknown_weight"] for x in readiness),
        "readiness_evidence_coverage_percent": _pct(
            sum(x["evidence_weight"] for x in readiness), total),
        "scope_source_mapping_coverage_percent": _pct(len(seen), len(criteria)),
        "confirmed_lower_bound_percent": _pct(verified, total),
        "potential_upper_bound_percent": 100.0,
        "unresolved_measurement_range_pp": _pct(unresolved, total),
        "actual_deployment_verified_percent": by_dimension["actual_deployment"]["verified_percent"],
        "actual_deployment_bar20": by_dimension["actual_deployment"]["bar20"],
        "statuses": {key: value for key, value in sorted(counts.items()) if value},
        "dimension_breakdown": by_dimension,
        "important_note": (
            "Workstream-only provisional denominator; NOT PHX-MASTER consolidated "
            "progress and NOT physical deployment evidence. The upper bound "
            "is a logical ceiling, not a statistical confidence interval.")
    }
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("ledger", type=Path)
    p.add_argument("--compact", action="store_true")
    args = p.parse_args(argv)
    try:
        data = json.loads(args.ledger.read_text(encoding="utf-8"))
        result = calculate(data)
    except (OSError, json.JSONDecodeError, LedgerInvalid) as exc:
        print("LEDGER INVALID: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
