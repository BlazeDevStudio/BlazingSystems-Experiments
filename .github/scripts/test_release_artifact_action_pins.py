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
    ".github/workflows/phx-release-esp32-core-compatibility.yml": {
        "actions/checkout": 2,
        "arduino/setup-arduino-cli": 1,
    },
    ".github/workflows/blazepisonet-softtimer-release.yml": {
        "actions/checkout": 3,
        "actions/setup-dotnet": 1,
        "actions/upload-artifact": 1,
        "actions/download-artifact": 1,
    },
}

ARDUINO_CLI_VERSION = "1.6.0"
ARDUINO_CLI_STEP_NAMES = ("Install ESP8266 core", "Install ESP32 core")


def _workflow_step(content: str, name: str) -> str:
    marker = f"      - name: {name}\n"
    start = content.find(marker)
    if start < 0:
        return ""
    body_start = start + len(marker)
    next_step = re.search(r"(?m)^      - (?:name|uses):", content[body_start:])
    end = body_start + next_step.start() if next_step else len(content)
    return content[body_start:end]


def check_arduino_cli_toolchain(content: str) -> list[str]:
    errors: list[str] = []
    action_marker = re.compile(
        r"(?m)^      - uses: arduino/setup-arduino-cli@[0-9a-f]{40}[^\n]*\n"
    )
    matches = list(action_marker.finditer(content))
    if len(matches) != len(ARDUINO_CLI_STEP_NAMES):
        errors.append(
            f"expected {len(ARDUINO_CLI_STEP_NAMES)} Arduino CLI setup actions, found {len(matches)}"
        )
    for index, match in enumerate(matches, start=1):
        remainder = content[match.end():]
        next_step = re.search(r"(?m)^      - (?:name|uses):", remainder)
        block = remainder[:next_step.start()] if next_step else remainder
        versions = re.findall(r"(?m)^          version:\s*[\"']?([^\"'#\s]+)", block)
        if versions != [ARDUINO_CLI_VERSION]:
            errors.append(
                f"Arduino CLI setup action {index} must pin version {ARDUINO_CLI_VERSION}; found {versions}"
            )

    for name in ARDUINO_CLI_STEP_NAMES:
        block = _workflow_step(content, name)
        if not block:
            errors.append(f"missing Arduino CLI core step: {name}")
            continue
        if (
            "arduino-cli version" not in block
            or f"RELEASE-TOOLCHAIN-RED: expected Arduino CLI {ARDUINO_CLI_VERSION}" not in block
        ):
            errors.append(
                f"{name} must verify the installed Arduino CLI binary is exactly {ARDUINO_CLI_VERSION}"
            )
    return errors


ACTION_PATTERN = re.compile(
    r"^\s*(?:-\s*)?uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([^\s#]+)(?:\s+#.*)?$",
    re.MULTILINE,
)


def check_arduino_cli_archive_verification(content: str) -> list[str]:
    errors: list[str] = []
    verifier_step = "      - name: Verify Arduino CLI binary against upstream release digest"
    verifier_command = (
        'run: python3 .github/scripts/verify_arduino_cli_archive.py '
        '--binary "$(command -v arduino-cli)"'
    )
    if content.count(verifier_step) != 2:
        errors.append("BlazePwifi workflow must verify the installed Arduino CLI against the release archive in both ESP jobs")
    if content.count(verifier_command) != 2:
        errors.append("both ESP jobs must invoke the checksum verifier with the installed arduino-cli path")

    test_step = "      - name: RELEASE-TOOLCHAIN Arduino CLI archive verifier negative controls"
    if content.count(test_step) != 1:
        errors.append("CI-0701 must run the Arduino CLI archive verifier negative-control suite exactly once")

    helper_path = ROOT / ".github/scripts/verify_arduino_cli_archive.py"
    if not helper_path.is_file():
        errors.append("missing release-owned Arduino CLI archive verifier")
    else:
        helper = helper_path.read_text(encoding="utf-8")
        expected = (
            "https://github.com/arduino/arduino-cli/releases/download/v1.6.0/",
            "arduino-cli_1.6.0_Linux_64bit.tar.gz",
            "20111675",
            "321ee249f44c78053234fec0f36101092bc6021bf24939e15e0cc2449c5ed250",
            "installed Arduino CLI binary differs",
        )
        for value in expected:
            if value not in helper:
                errors.append(f"Arduino CLI archive verifier is missing pinned/required value: {value}")
    return errors


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

        if relative_path == ".github/workflows/blazepwifi-build.yml":
            workflow_errors.extend(check_arduino_cli_toolchain(content))
            workflow_errors.extend(check_arduino_cli_archive_verification(content))

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
