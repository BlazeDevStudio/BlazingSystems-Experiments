#!/usr/bin/env python3
"""Guard Phoenix build and release workflows against mutable external actions."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Upstream refs were resolved to full commit SHAs and action.yml was read at
# each exact commit. All pinned JavaScript actions now declare Node24; signature
# provenance, including the unsigned Android emulator action, is in the handover.
EXPECTED = {
    "actions/checkout": "3d3c42e5aac5ba805825da76410c181273ba90b1",  # v7.0.1, node24
    "actions/setup-dotnet": "0f4a354dd5547a28c70b7853dbd95d5b67886e73",  # v6.1.0, node24
    "actions/setup-java": "d1374f8ac74474200d16ef8ecee22c7ae7a51880",  # v6.3.0, node24
    "actions/setup-python": "6d4fd22b20465ccc0f7354476588e8df7c9ca0e0",  # v7.1.0, node24
    "actions/upload-artifact": "cf430e030ddbb5b0abf93d22962f4752f3646cd9",  # v7.0.2, node24
    "actions/download-artifact": "9000827ccba6bdab643e8b6fd33ac0654aef8333",  # v8.0.2, node24
    "arduino/setup-arduino-cli": "b3cda96fddef6af6c56b4c5efb5c47e2357935db",  # current @v2 resolution, signed Node24 commit
    "reactivecircus/android-emulator-runner": "a421e43855164a8197daf9d8d40fe71c6996bb0d",  # v2.38.0, node24; upstream commit unsigned
}

WORKFLOWS = {
    ".github/workflows/blazepwifi-build.yml": {
        "actions/checkout": 20,
        "arduino/setup-arduino-cli": 2,
        "actions/setup-java": 2,
        "actions/setup-python": 3,
        "reactivecircus/android-emulator-runner": 1,
        "actions/upload-artifact": 16,
        "actions/download-artifact": 8,
    },
    ".github/workflows/blazepisonet-softtimer-release.yml": {
        "actions/checkout": 3,
        "actions/setup-dotnet": 1,
        "actions/upload-artifact": 1,
        "actions/download-artifact": 1,
    },
}

ACTION_PATTERN = re.compile(
    r"^\s*(?:-\s*)?uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([^\s#]+)(?:\s+#.*)?$",
    re.MULTILINE,
)


def main() -> int:
    errors: list[str] = []
    for relative_path, expected_counts in WORKFLOWS.items():
        path = ROOT / relative_path
        if not path.is_file():
            errors.append(f"missing release workflow: {relative_path}")
            continue

        content = path.read_text(encoding="utf-8")
        found: dict[str, list[str]] = {}
        for action, ref in ACTION_PATTERN.findall(content):
            found.setdefault(action, []).append(ref)

        workflow_errors: list[str] = []
        unexpected = sorted(set(found) - set(expected_counts))
        if unexpected:
            workflow_errors.append(
                f"{relative_path}: unexpected external actions: {', '.join(unexpected)}"
            )

        for action, expected_count in expected_counts.items():
            refs = found.get(action, [])
            if len(refs) != expected_count:
                workflow_errors.append(
                    f"{relative_path}: expected {expected_count} {action} invocations, found {len(refs)}"
                )

            expected_sha = EXPECTED.get(action)
            if expected_sha is None:
                workflow_errors.append(f"{relative_path}: missing reviewed SHA for {action}")
                continue

            for ref in refs:
                if not re.fullmatch(r"[0-9a-f]{40}", ref) or ref != expected_sha:
                    workflow_errors.append(
                        f"{relative_path}: {action} must use reviewed immutable SHA "
                        f"{expected_sha}; found {ref}"
                    )

        if workflow_errors:
            errors.extend(workflow_errors)
            for error in workflow_errors:
                print(f"RELEASE-ACTION-PINS-RED: {error}")
        else:
            total = sum(expected_counts.values())
            print(
                f"RELEASE-ACTION-PINS-PASS: {relative_path}: "
                f"{total} external action invocations pinned to reviewed immutable commits"
            )

    if errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
