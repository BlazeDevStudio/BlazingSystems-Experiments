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
        "actions/checkout": 3,
        "arduino/setup-arduino-cli": 1,
    },
    ".github/workflows/blazepisonet-softtimer-release.yml": {
        "actions/checkout": 3,
        "actions/setup-dotnet": 1,
        "actions/upload-artifact": 1,
        "actions/download-artifact": 1,
    },
    # Manual v0.5.3 production release/signing workflows are release-capable
    # even though they are not part of the ordinary PR build matrix.
    ".github/workflows/blazepwifi-v053-release.yml": {
        "actions/checkout": 1,
        "actions/upload-artifact": 1,
    },
    ".github/workflows/blazerental-v053-lineage2-sign.yml": {
        "actions/checkout": 1,
        "actions/setup-java": 1,
        "actions/upload-artifact": 1,
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


ARDUINO_CORE_EXPECTATIONS = (
    ("Install ESP8266 core", "esp8266:esp8266", "3.1.2"),
    ("Install ESP32 core", "esp32:esp32", "3.3.13"),
)


def check_arduino_core_version_assertions(content: str) -> list[str]:
    """Require runtime proof that each installed board core matches provenance."""
    errors: list[str] = []
    for step_name, package, version in ARDUINO_CORE_EXPECTATIONS:
        block = _workflow_step(content, step_name)
        if not block:
            errors.append(f"missing Arduino core installation step: {step_name}")
            continue

        required = (
            ('core_list="$(arduino-cli core list)"', "capture the installed core list"),
            (f"""awk '$1 == "{package}" {{print $2}}'""", "select the installed package version"),
            (f'if [ "$installed_core_versions" != "{version}" ]; then', "compare the resolved version"),
            (f"RELEASE-TOOLCHAIN-RED: expected {package}@{version}", "fail closed on version mismatch"),
            (f"RELEASE-TOOLCHAIN-CORE-PASS: {package}@{version}", "emit the verified core identity"),
        )
        for snippet, description in required:
            if snippet not in block:
                errors.append(f"{step_name} must {description} for {package}@{version}")
    return errors


USES_DIRECTIVE_PATTERN = re.compile(
    r"^ {2,8}(?:- )?uses:[ \t]*(?P<value>[^\r\n]*)$",
    re.MULTILINE,
)
PINNED_ACTION_VALUE_PATTERN = re.compile(
    r"(?P<action>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(?P<sha>[0-9a-f]{40})"
)


def parse_pinned_uses_directives(content: str) -> tuple[dict[str, list[str]], list[str]]:
    """Parse every YAML action-use directive and reject anything not immutably pinned."""
    found: dict[str, list[str]] = {}
    errors: list[str] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        match = USES_DIRECTIVE_PATTERN.fullmatch(line)
        if match is None:
            continue

        raw_value = match.group("value").strip()
        value = re.split(r"[ \t]+#", raw_value, maxsplit=1)[0].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        pin = PINNED_ACTION_VALUE_PATTERN.fullmatch(value)
        if pin is None:
            errors.append(
                f"line {line_number}: uses: must be an explicit owner/repo@40-hex "
                f"immutable action ref; found {raw_value!r}"
            )
            continue
        found.setdefault(pin.group("action"), []).append(pin.group("sha"))
    return found, errors


def check_uses_parser_regressions() -> list[str]:
    """Exercise accepted and rejected uses: forms before inspecting live workflows."""
    sha = "a" * 40
    cases = (
        ("pinned action with comment", f"      - uses: actions/checkout@{sha} # immutable", False),
        ("quoted pinned action", f"        uses: 'actions/checkout@{sha}'", False),
        ("dynamic expression", "      - uses: ${{ matrix.action }}", True),
        ("local action path", "      - uses: ./.github/actions/publish", True),
        ("mutable tag", "      - uses: actions/checkout@v4", True),
        ("reusable workflow path", f"    uses: BlazeDevStudio/BlazingSystems-Experiments/.github/workflows/release.yml@{sha}", True),
        ("empty uses directive", "      - uses:", True),
    )
    errors: list[str] = []
    for label, fixture, should_reject in cases:
        _, fixture_errors = parse_pinned_uses_directives(fixture)
        if should_reject and not fixture_errors:
            errors.append(f"{label}: unpinned directive was accepted")
        elif not should_reject and fixture_errors:
            errors.append(f"{label}: immutable pin was rejected: {fixture_errors[0]}")

    # A command inside a YAML run: block is not a workflow-level uses: directive.
    _, shell_errors = parse_pinned_uses_directives("          echo 'uses: ./not-a-step'")
    if shell_errors:
        errors.append("shell text inside run: was incorrectly parsed as an action directive")
    return errors


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
    parser_errors = check_uses_parser_regressions()
    if parser_errors:
        errors.extend(parser_errors)
        for error in parser_errors:
            print(f"RELEASE-ACTION-PARSER-RED: {error}")
    else:
        print("RELEASE-ACTION-PARSER-PASS: 8 synthetic uses: directive cases")
    for relative_path, expected_counts in WORKFLOWS.items():
        path = ROOT / relative_path
        if not path.is_file():
            errors.append(f"missing release workflow: {relative_path}")
            continue

        content = path.read_text(encoding="utf-8")
        found, workflow_errors = parse_pinned_uses_directives(content)
        unexpected = sorted(set(found) - set(expected_counts))
        if unexpected:
            workflow_errors.append(
                f"{relative_path}: unexpected external actions: {', '.join(unexpected)}"
            )

        if relative_path == ".github/workflows/blazepwifi-build.yml":
            workflow_errors.extend(check_arduino_cli_toolchain(content))
            workflow_errors.extend(check_arduino_core_version_assertions(content))
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
