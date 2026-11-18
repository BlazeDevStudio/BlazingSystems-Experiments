#!/usr/bin/env python3
"""Guard Phoenix release artifact actions against mutable tags and old runtimes."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "actions/upload-artifact": "cf430e030ddbb5b0abf93d22962f4752f3646cd9",  # v7.0.2, node24
    "actions/download-artifact": "9000827ccba6bdab643e8b6fd33ac0654aef8333",  # v8.0.2, node24
}
WORKFLOWS = {
    ".github/workflows/blazepwifi-build.yml": {
        "actions/upload-artifact": 16,
        "actions/download-artifact": 8,
    },
    ".github/workflows/blazepisonet-softtimer-release.yml": {
        "actions/upload-artifact": 1,
        "actions/download-artifact": 1,
    },
}
PATTERN = re.compile(
    r"^\s*-\s*uses:\s*(actions/(?:upload-artifact|download-artifact))@([^\s#]+)(?:\s+#.*)?$",
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
        found: dict[str, list[str]] = {name: [] for name in EXPECTED}
        for action, ref in PATTERN.findall(content):
            found[action].append(ref)
        for action, expected_sha in EXPECTED.items():
            refs = found[action]
            expected_count = expected_counts[action]
            if len(refs) != expected_count:
                errors.append(
                    f"{relative_path}: expected {expected_count} {action} invocations, found {len(refs)}"
                )
            for ref in refs:
                if not re.fullmatch(r"[0-9a-f]{40}", ref) or ref != expected_sha:
                    errors.append(
                        f"{relative_path}: {action} must use reviewed immutable SHA "
                        f"{expected_sha}; found {ref}"
                    )
        if not errors:
            print(
                f"RELEASE-ACTION-PINS-PASS: {relative_path}: "
                f"upload={len(found['actions/upload-artifact'])}, "
                f"download={len(found['actions/download-artifact'])}"
            )
    if errors:
        for error in errors:
            print(f"RELEASE-ACTION-PINS-RED: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
