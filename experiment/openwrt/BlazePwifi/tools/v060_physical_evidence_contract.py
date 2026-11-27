#!/usr/bin/env python3
"""PEVID-0679: read-only STRUCTURAL checklist for power-cut evidence.

NEVER evidence that a physical trial occurred. Input is a private, disposable
/tmp/blaze-v2-evidence-* TEST FIXTURE (no customer identifiers or keys).
Even structurally complete reports remain unverified human claims and do not
authorize shipping, migration, firmware flashing or financial ingress.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import argparse
from datetime import datetime

ROOT_PREFIX = "blaze-v2-evidence-"
MARKER = ".blaze-physical-evidence-fixture-only"
MAGIC = b"BLAZE-POWER-CUT-STRUCTURE-NOT-HARDWARE-PROOF\n"
SCHEMA = "blaze-v060-physical-evidence-structure/1"
ARCHES = ("ruijie", "orangepi_zero3", "x86_64")
CHECKPOINTS = (
    "before-source-fsync",
    "before-rename",
    "after-rename-before-dir-fsync",
    "after-dir-fsync-before-ack",
    "after-ack-observed",
)
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
TIME = re.compile(r"20[2-9][0-9]-[01][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z\Z")
DEVICE = re.compile(r"/dev/[a-zA-Z0-9/._-]{2,70}\Z")
OPAQUE = re.compile(r"[a-z0-9]{12,40}\Z")
MAX_CAPTURE = 65536
MAX_MANIFEST = 256000
TRIAL_FIELDS = {
    "target_arch", "checkpoint", "trial_index", "hardware_model",
    "storage_source", "filesystem", "package_sha256",
    "pre_state_sha256", "post_state_sha256", "observed_delta_seconds",
    "total_before_seconds", "total_after_seconds",
    "receipts_consistent", "duplicate_ack_count", "event_ref_redacted",
    "power_event_time_utc", "power_log", "power_log_sha256",
    "recovery_log", "recovery_log_sha256", "claimed_outcome",
}
SOAK_FIELDS = {
    "target_arch", "duration_seconds", "concurrent_clients",
    "duplicate_ack_count", "lost_ack_count", "capture_log",
    "capture_log_sha256", "claimed_outcome",
}
REPORT_FIELDS = {"schema", "fixture_only", "claim_origin", "candidate_git_sha", "trials", "soaks"}


def deny(code: str) -> None:
    raise ValueError(code)


def ensure(ok: bool, reason: str) -> None:
    if not ok:
        deny(reason)


def private_dir(p: Path) -> None:
    st = os.lstat(p)
    ensure(stat.S_ISDIR(st.st_mode) and st.st_uid == os.geteuid() and
           (stat.S_IMODE(st.st_mode) == 0o700), "UNSAFE_PRIVATE_DIR")


def private_bytes(p: Path, maximum: int) -> bytes:
    fd = os.open(p, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        pre = os.fstat(fd)
        ensure(stat.S_ISREG(pre.st_mode) and pre.st_nlink == 1 and
               pre.st_uid == os.geteuid() and
               stat.S_IMODE(pre.st_mode) == 0o600 and
               0 <= pre.st_size <= maximum, "UNSAFE_PRIVATE_FILE")
        data = bytearray()
        while len(data) <= maximum:
            part = os.read(fd, min(65536, maximum + 1 - len(data)))
            if not part:
                break
            data.extend(part)
        post = os.fstat(fd)
        ensure(len(data) == pre.st_size and
               (pre.st_dev, pre.st_ino, pre.st_mtime_ns, pre.st_ctime_ns) ==
               (post.st_dev, post.st_ino, post.st_mtime_ns, post.st_ctime_ns),
               "CAPTURE_CHANGED_OR_OVERSIZED")
        return bytes(data)
    finally:
        os.close(fd)


def stamp(p: Path) -> tuple[int, ...]:
    """Opaque local identity stamp; never print private paths or identifiers."""
    st = os.lstat(p)
    return (st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_nlink,
            st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def check_unchanged(p: Path, expected: tuple[int, ...], contents: bytes,
                    maximum: int) -> None:
    ensure(stamp(p) == expected, "EVIDENCE_CHANGED_DURING_REVIEW")
    ensure(private_bytes(p, maximum) == contents,
           "EVIDENCE_CHANGED_DURING_REVIEW")
    ensure(stamp(p) == expected, "EVIDENCE_CHANGED_DURING_REVIEW")


def hex64(s: object) -> bool:
    return isinstance(s, str) and HEX64.fullmatch(s) is not None


def hex40(s: object) -> bool:
    """The project's GitHub commit identity uses SHA-1 (40 hex digits)."""
    return isinstance(s, str) and HEX40.fullmatch(s) is not None


def nonneg(x: object) -> bool:
    return type(x) is int and 0 <= x <= 2**63 - 1


def capture(root: Path, rel: object, digest: object, used: set[str], digests: set[str], observed: dict[str, tuple[str, tuple[int, ...]]]) -> None:
    ensure(isinstance(rel, str) and re.fullmatch(r"captures/[0-9a-f]{40}\.log", rel) is not None,
           "CAPTURE_PATH_UNSAFE")
    ensure(rel not in used, "CAPTURE_REUSED")
    used.add(rel)
    ensure(hex64(digest), "CAPTURE_DIGEST_INVALID")
    data = private_bytes(root / rel, MAX_CAPTURE)
    ensure(len(data) >= 32 and hashlib.sha256(data).hexdigest() == digest,
           "CAPTURE_DIGEST_MISMATCH")
    ensure(digest not in digests, "CAPTURE_CONTENT_REUSED")
    digests.add(digest)
    observed[rel] = (digest, stamp(root / rel))


def review(rootname: str) -> dict:
    root = Path(rootname)
    ensure(root.parent == Path("/tmp") and
           re.fullmatch(ROOT_PREFIX + r"[A-Za-z0-9_-]+", root.name) is not None and
           os.path.realpath(root) == str(root), "NOT_ISOLATED_FIXTURE")
    private_dir(root)
    private_dir(root / "captures")
    root_stamp = stamp(root)
    captures_stamp = stamp(root / "captures")
    marker_stamp = stamp(root / MARKER)
    ensure(private_bytes(root / MARKER, 128) == MAGIC, "MARKER_MISSING")
    ensure(set(os.listdir(root)) == {"captures", "manifest.json", MARKER},
           "ROOT_HAS_UNREVIEWED_FILES")
    manifest_stamp = stamp(root / "manifest.json")
    raw = private_bytes(root / "manifest.json", MAX_MANIFEST)
    obj = json.loads(raw)
    ensure(type(obj) is dict and set(obj) == REPORT_FIELDS and
           obj["schema"] == SCHEMA and obj["fixture_only"] is True and
           obj["claim_origin"] == "operator-claimed-unverified" and
           hex40(obj["candidate_git_sha"]), "MANIFEST_SCHEMA")
    trials, soaks = obj["trials"], obj["soaks"]
    ensure(type(trials) is list and len(trials) == 150 and
           type(soaks) is list and len(soaks) == 3, "MINIMUM_COVERAGE_MISSING")
    coverage: set[tuple[str, str, int]] = set()
    used: set[str] = set()
    used_digests: set[str] = set()
    observed: dict[str, tuple[str, tuple[int, ...]]] = {}
    seen_power_times: set[datetime] = set()
    events: set[str] = set()
    arch_identity: dict[str, tuple[str, str, str, str]] = {}
    for t in trials:
        ensure(type(t) is dict and set(t) == TRIAL_FIELDS, "TRIAL_SCHEMA")
        a, c, i = t["target_arch"], t["checkpoint"], t["trial_index"]
        ensure(a in ARCHES and c in CHECKPOINTS and
               type(i) is int and 1 <= i <= 10, "TRIAL_COVERAGE_INVALID")
        ensure((a, c, i) not in coverage, "DUPLICATE_TRIAL")
        coverage.add((a, c, i))
        ensure(type(t["hardware_model"]) is str and
               re.fullmatch(r"[A-Za-z0-9 _.+()-]{8,85}", t["hardware_model"]) is not None and
               type(t["storage_source"]) is str and DEVICE.fullmatch(t["storage_source"]) is not None and
               t["filesystem"] in ("ext4", "f2fs", "xfs", "btrfs") and
               hex64(t["package_sha256"]), "HARDWARE_IDENTITY_INVALID")
        sig = (t["hardware_model"], t["storage_source"],
               t["filesystem"], t["package_sha256"])
        ensure(a not in arch_identity or arch_identity[a] == sig,
               "TARGET_HARDWARE_IDENTITY_CHANGED")
        arch_identity[a] = sig
        ensure(hex64(t["pre_state_sha256"]) and hex64(t["post_state_sha256"]) and
               nonneg(t["total_before_seconds"]) and
               nonneg(t["total_after_seconds"]) and
               type(t["observed_delta_seconds"]) is int and
               -(2**63 - 1) <= t["observed_delta_seconds"] <= 2**63 - 1 and
               t["total_before_seconds"] + t["observed_delta_seconds"] ==
               t["total_after_seconds"], "MONEY_CONSERVATION_INVALID")
        ensure(t["receipts_consistent"] is True and
               t["claimed_outcome"] == "pass" and
               type(t["duplicate_ack_count"]) is int and
               t["duplicate_ack_count"] == 0, "PAYMENT_REPLAY_INVARIANT_FAILED")
        ref = t["event_ref_redacted"]
        ensure(type(ref) is str and OPAQUE.fullmatch(ref) is not None and
               ref not in events, "EVENT_REF_UNSAFE_OR_DUPLICATE")
        events.add(ref)
        instant = t["power_event_time_utc"]
        ensure(type(instant) is str and TIME.fullmatch(instant) is not None,
               "POWER_EVENT_TIME_INVALID")
        try:
            parsed = datetime.strptime(instant, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            deny("POWER_EVENT_CALENDAR_INVALID")
        # This is a uniqueness guard on *claimed* events, not an attestation
        # that any powered-off trial actually happened.
        ensure(parsed not in seen_power_times, "POWER_EVENT_TIME_REUSED")
        seen_power_times.add(parsed)
        capture(root, t["power_log"], t["power_log_sha256"], used, used_digests, observed)
        capture(root, t["recovery_log"], t["recovery_log_sha256"], used, used_digests, observed)
    seen_arch: set[str] = set()
    for soak in soaks:
        ensure(type(soak) is dict and set(soak) == SOAK_FIELDS,
               "SOAK_SCHEMA")
        a = soak["target_arch"]
        ensure(a in ARCHES and a not in seen_arch and
               nonneg(soak["duration_seconds"]) and
               soak["duration_seconds"] >= 86400 and
               nonneg(soak["concurrent_clients"]) and
               soak["concurrent_clients"] >= 30 and
               type(soak["duplicate_ack_count"]) is int and
               type(soak["lost_ack_count"]) is int and
               soak["duplicate_ack_count"] == 0 and
               soak["lost_ack_count"] == 0 and
               soak["claimed_outcome"] == "pass", "SOAK_EVIDENCE_INSUFFICIENT")
        seen_arch.add(a)
        capture(root, soak["capture_log"], soak["capture_log_sha256"], used, used_digests, observed)
    ensure(set(arch_identity) == set(ARCHES) and seen_arch == set(ARCHES) and
           len(coverage) == 150, "COVERAGE_MISSING")
    ensure({"captures/" + name for name in os.listdir(root / "captures")} == used,
           "UNREFERENCED_EVIDENCE")
    # This second pass detects common edits after each first inspection:
    # a changed manifest, replaced identical-byte capture, newly inserted
    # file, or modified first capture while later entries are reviewed.
    # It remains non-atomic and proves NOTHING about hardware authenticity.
    ensure(stamp(root) == root_stamp and
           stamp(root / "captures") == captures_stamp,
           "EVIDENCE_CHANGED_DURING_REVIEW")
    check_unchanged(root / MARKER, marker_stamp, MAGIC, 128)
    check_unchanged(root / "manifest.json", manifest_stamp, raw, MAX_MANIFEST)
    for rel, (digest, before) in observed.items():
        path = root / rel
        ensure(stamp(path) == before, "EVIDENCE_CHANGED_DURING_REVIEW")
        data = private_bytes(path, MAX_CAPTURE)
        ensure(hashlib.sha256(data).hexdigest() == digest,
               "EVIDENCE_CHANGED_DURING_REVIEW")
        ensure(stamp(path) == before, "EVIDENCE_CHANGED_DURING_REVIEW")
    ensure({"captures/" + name for name in os.listdir(root / "captures")} == used and
           set(os.listdir(root)) == {"captures", "manifest.json", MARKER} and
           stamp(root) == root_stamp and
           stamp(root / "captures") == captures_stamp,
           "EVIDENCE_CHANGED_DURING_REVIEW")
    return {
        "status": "STRUCTURE_READY_FOR_INDEPENDENT_REVIEW",
        "trial_records": len(coverage), "soak_records": len(seen_arch),
        "physical_powercut_verified": False,
        "power_controller_authenticity_verified": False,
        "financial_migration_authorized": False,
        "production_release_authorized": False,
        "note": "Human claims and synthetic fixtures cannot prove actual power interruption."
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PEVID-0679: structural review only; no physical verification")
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    try:
        report = review(args.root)
        print(json.dumps(report, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError, OverflowError, UnicodeError):
        print(json.dumps({
            "status": "BLOCKED", "reason": "EVIDENCE_INCOMPLETE_OR_UNSAFE",
            "physical_powercut_verified": False,
            "financial_migration_authorized": False,
            "production_release_authorized": False
        }, sort_keys=True))
        return 4


if __name__ == "__main__":
    sys.exit(main())
