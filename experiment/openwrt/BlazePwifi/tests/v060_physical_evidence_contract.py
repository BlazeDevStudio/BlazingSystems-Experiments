#!/usr/bin/env python3
"""PEVID-0679: mocked data tests schema, NEVER physical power-cut success.

No actual hardware, paid client, storage power operation or customer data.
The structurally complete fixture MUST STILL say physical_verified=false.
"""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

TOOL = Path(__file__).resolve().parents[1] / "tools/v060_physical_evidence_contract.py"
ARCHES = ("ruijie", "orangepi_zero3", "x86_64")
CHECKPOINTS = (
    "before-source-fsync",
    "before-rename",
    "after-rename-before-dir-fsync",
    "after-dir-fsync-before-ack",
    "after-ack-observed",
)


def write_private(path: Path, contents: bytes) -> None:
    path.write_bytes(contents)
    path.chmod(0o600)


def run(root: Path, expected: str) -> dict:
    p = subprocess.run([sys.executable, str(TOOL), "--root", str(root)],
                       text=True, capture_output=True, timeout=15)
    assert p.returncode == (0 if expected.startswith("STRUCTURE_") else 4), (
        "unexpected evidence gate exit: " + str(p.returncode) + " / " + p.stderr
    )
    assert not p.stderr and len(p.stdout.splitlines()) == 1, "Leaky diagnostics"
    doc = json.loads(p.stdout)
    assert doc["status"] == expected, doc
    assert doc["physical_powercut_verified"] is False, doc
    assert doc["production_release_authorized"] is False, doc
    assert doc["financial_migration_authorized"] is False, doc
    assert "operator" not in p.stdout.lower() or expected.startswith("STRUCTURE_")
    return doc


def create(root: Path) -> dict:
    write_private(root / ".blaze-physical-evidence-fixture-only",
                  b"BLAZE-POWER-CUT-STRUCTURE-NOT-HARDWARE-PROOF\n")
    captures = root / "captures"
    captures.mkdir(mode=0o700)
    next_capture = [1]

    def log(label: str) -> tuple[str, str]:
        n = next_capture[0]
        next_capture[0] += 1
        # This is entirely MOCKED; no hardware was powered down.
        data = f"MOCKED CI TEST LOG; NOT HARDWARE EVIDENCE; {n:04d}; {label}\n".encode()
        rel = f"captures/{n:040x}.log"
        write_private(root / rel, data)
        return rel, hashlib.sha256(data).hexdigest()

    trials = []
    for arch_idx, arch in enumerate(ARCHES):
        for checkpoint in CHECKPOINTS:
            for i in range(1, 11):
                event = len(trials) + 1
                power, ph = log("power-log")
                boot, bh = log("reboot-recovery-log")
                delta = -10 if i % 3 == 0 else 10
                trials.append({
                    "target_arch": arch,
                    "checkpoint": checkpoint,
                    "trial_index": i,
                    "hardware_model": ("Mock Ruijie RG-EW1200G Pro",
                                       "Mock Orange Pi Zero 3",
                                       "Mock x86-64 lab host")[arch_idx],
                    "storage_source": ("/dev/sdb1", "/dev/sdc1", "/dev/sdd1")[arch_idx],
                    "filesystem": "ext4",
                    "package_sha256": str(arch_idx + 1) * 64,
                    "pre_state_sha256": "a" * 64,
                    "post_state_sha256": "b" * 64,
                    "observed_delta_seconds": delta,
                    "total_before_seconds": 1000,
                    "total_after_seconds": 1000 + delta,
                    "receipts_consistent": True,
                    "duplicate_ack_count": 0,
                    "event_ref_redacted": f"{event:012x}",
                    "power_event_time_utc": (datetime(2026, 10, 9, 12, tzinfo=timezone.utc)
                                             + timedelta(minutes=event)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "power_log": power,
                    "power_log_sha256": ph,
                    "recovery_log": boot,
                    "recovery_log_sha256": bh,
                    "claimed_outcome": "pass",
                })
    soaks = []
    for arch in ARCHES:
        rel, sha = log("mocked 24h controller soak")
        soaks.append({
            "target_arch": arch,
            "duration_seconds": 86400,
            "concurrent_clients": 30,
            "duplicate_ack_count": 0,
            "lost_ack_count": 0,
            "capture_log": rel,
            "capture_log_sha256": sha,
            "claimed_outcome": "pass",
        })
    return {
        "schema": "blaze-v060-physical-evidence-structure/1",
        "fixture_only": True,
        "claim_origin": "operator-claimed-unverified",
        "candidate_git_sha": "c" * 40,
        "trials": trials,
        "soaks": soaks
    }


with tempfile.TemporaryDirectory(prefix="blaze-v2-evidence-", dir="/tmp") as folder:
    root = Path(folder)
    manifest = root / "manifest.json"
    original = create(root)

    def store(doc: dict) -> None:
        write_private(manifest, (json.dumps(doc, sort_keys=True) + "\n").encode())

    store(original)
    result = run(root, "STRUCTURE_READY_FOR_INDEPENDENT_REVIEW")
    assert result["trial_records"] == 150 and result["soak_records"] == 3
    assert result["power_controller_authenticity_verified"] is False

    def blocked(edit) -> None:
        copy_doc = copy.deepcopy(original)
        edit(copy_doc)
        store(copy_doc)
        run(root, "BLOCKED")
        store(original)

    # These checks operate on data that is MOCKED, NOT genuine physical logs.
    blocked(lambda d: d["trials"].pop())
    blocked(lambda d: d["soaks"].pop())
    blocked(lambda d: d["trials"].__setitem__(1, copy.deepcopy(d["trials"][0])))
    blocked(lambda d: d["trials"][1].__setitem__("power_log", d["trials"][0]["power_log"]))
    blocked(lambda d: d["trials"][5].__setitem__("observed_delta_seconds", 100))
    blocked(lambda d: d["trials"][5].__setitem__("duplicate_ack_count", 1))
    blocked(lambda d: d["trials"][5].__setitem__("duplicate_ack_count", False))
    blocked(lambda d: d["trials"][2].__setitem__("power_event_time_utc", "unknown"))
    blocked(lambda d: d["trials"][2].__setitem__("power_event_time_utc", "2026-02-30T12:04:00Z"))
    blocked(lambda d: d["trials"][2].__setitem__(
        "power_event_time_utc", d["trials"][0]["power_event_time_utc"]))
    blocked(lambda d: d["trials"][2].__setitem__("power_log", "../../etc/passwd"))
    blocked(lambda d: d["trials"][2].__setitem__("target_arch", "customer"))
    blocked(lambda d: d["trials"][2].__setitem__("package_sha256", "not-a-hash"))
    blocked(lambda d: d["soaks"][0].__setitem__("concurrent_clients", 29))
    blocked(lambda d: d["soaks"][0].__setitem__("lost_ack_count", 1))
    # PEVID-0690: commit identity must be the actual 40-character GitHub
    # SHA-1, unlike SHA-256 digests for package/state/capture content.
    # A 64-character synthetic "commit" used to pass and a real 40-char
    # commit was wrongly rejected. Keep this contract fail closed.
    blocked(lambda d: d.__setitem__("candidate_git_sha", "c" * 64))
    blocked(lambda d: d.__setitem__("candidate_git_sha", "c" * 39))
    blocked(lambda d: d.__setitem__("candidate_git_sha", "C" * 40))
    blocked(lambda d: d.__setitem__("candidate_git_sha", "z" * 40))
    blocked(lambda d: d.__setitem__("candidate_git_sha", ""))
    blocked(lambda d: d.__setitem__("claim_origin", "physical-certified"))
    blocked(lambda d: d.__setitem__("fixture_only", False))
    blocked(lambda d: d.__setitem__("production_release_authorized", True))

    # Copies of legitimate capture contents under a distinct filename must
    # still fail, even when the copied file has a matching SHA-256 in the
    # manifest. Unique filenames alone are not independent observations.
    first_claim = original["trials"][0]["power_log"]
    second_claim = original["trials"][1]["power_log"]
    original_second = (root / second_claim).read_bytes()
    first_bytes = (root / first_claim).read_bytes()
    write_private(root / second_claim, first_bytes)
    forged_copy = copy.deepcopy(original)
    forged_copy["trials"][1]["power_log_sha256"] = hashlib.sha256(first_bytes).hexdigest()
    store(forged_copy)
    run(root, "BLOCKED")
    store(original)
    write_private(root / second_claim, original_second)

    # The bytes must match each claim, and private files must not be symlinks
    # or world-readable. No modification to genuine lab media occurs.
    capture = root / original["trials"][0]["power_log"]
    saved = capture.read_bytes()
    write_private(capture, saved + b"tamper")
    run(root, "BLOCKED")
    write_private(capture, saved)
    capture.chmod(0o644)
    run(root, "BLOCKED")
    capture.chmod(0o600)
    capture.unlink()
    capture.symlink_to("/etc/passwd")
    run(root, "BLOCKED")
    capture.unlink()
    write_private(capture, saved)
    manifest.chmod(0o644)
    run(root, "BLOCKED")
    manifest.chmod(0o600)
    extra = root / "captures" / ("f" * 40 + ".log")
    write_private(extra, b"MOCK UNREFERENCED EVIDENCE NOT AN ACTUAL POWER TEST\n")
    run(root, "BLOCKED")
    extra.unlink()
    marker = root / ".blaze-physical-evidence-fixture-only"
    marker.unlink()
    run(root, "BLOCKED")
    write_private(marker, b"BLAZE-POWER-CUT-STRUCTURE-NOT-HARDWARE-PROOF\n")
    assert run(root, "STRUCTURE_READY_FOR_INDEPENDENT_REVIEW")["physical_powercut_verified"] is False

    # PEVID-0682: an early capture/manifest replaced AFTER its first review
    # must be caught at the final second pass. No actual equipment is touched.
    spec = importlib.util.spec_from_file_location("pevid0682_lab", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_capture = module.capture
    last_capture = original["soaks"][-1]["capture_log"]

    def injected_change(mutate, expected_reason: str = "EVIDENCE_CHANGED_DURING_REVIEW") -> None:
        fired = [False]

        def inject(*args, **kwargs):
            result = original_capture(*args, **kwargs)
            if args[1] == last_capture and not fired[0]:
                fired[0] = True
                mutate()
            return result

        with patch.object(module, "capture", side_effect=inject):
            try:
                module.review(str(root))
            except ValueError as exc:
                assert str(exc) == expected_reason, (
                    "Wrong late mutation rejection code: " + str(exc)
                )
            else:
                raise AssertionError("Mutated evidence returned review-ready")
        assert fired[0], "Late mutation injection not exercised"

    first_capture = root / original["trials"][0]["power_log"]
    first_saved = first_capture.read_bytes()
    injected_change(lambda: write_private(first_capture, first_saved + b"CHANGED IN REVIEW"))
    write_private(first_capture, first_saved)

    def replace_identical():
        first_capture.unlink()
        write_private(first_capture, first_saved)

    injected_change(replace_identical)
    write_private(first_capture, first_saved)

    manifest_saved = manifest.read_bytes()
    injected_change(lambda: write_private(manifest, manifest_saved + b" "))
    write_private(manifest, manifest_saved)

    unknown_capture = root / "captures" / ("e" * 40 + ".log")
    injected_change(lambda: write_private(unknown_capture,
                    b"MOCK EXTRA RECORD AFTER LAST CAPTURE; NOT REAL POWER DATA\n"),
                    expected_reason="UNREFERENCED_EVIDENCE")
    unknown_capture.unlink()
    assert run(root, "STRUCTURE_READY_FOR_INDEPENDENT_REVIEW")["physical_powercut_verified"] is False

print("PEVID-0679 PASS: 150 mock trials+3 mock 24h soaks structurally checked, missing/duplicate/tamper/path/permission/financial claims refused")
print("PEVID-0680 PASS: repeated power-cut timestamps, invalid calendar dates and copied capture contents rejected without hardware approval")
print("PEVID-0682 PASS: late capture content/replacement, manifest edit and added evidence during review rejected; hardware remains unverified")
print("PEVID-0690 PASS: 40-character GitHub commit IDs accepted; 64-character, short, uppercase and invalid IDs refused; still not hardware attestation")
print("PHYSICAL_POWER_CUT_VERIFIED=0; CUSTOMER_INSTALL_AUTHORIZED=0; mocked CI input is NOT hardware acceptance")
