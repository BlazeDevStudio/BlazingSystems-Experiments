#!/usr/bin/env python3
"""RENT-20261022-V2FLOOR: isolated, nonproduction coin/receipt replay floor.

This deliberately re-seals an internally contradictory synthetic v2 authority.
SHA-256 is only corruption detection, NOT an independent rollback witness.
NO source files are installed on real routers, no customer credentials/payments.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "tests/fixtures/rental_v2_atomic.py"
PREFIX = "/tmp/blaze-v2-rental-"


def write_private(path, data):
    path.write_bytes(data if isinstance(data, bytes) else data.encode())
    path.chmod(0o600)


def canonical(body):
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def command(env, *args):
    return subprocess.run([sys.executable, str(HELPER), *args],
                          env=env, capture_output=True, text=True, timeout=15)


base = Path(tempfile.mkdtemp(prefix="blaze-v2-rental-", dir="/tmp"))
try:
    # Hard fixture root prefix, private dirs/marker, exact derived paths.
    assert str(base).startswith(PREFIX)
    state, run = base / "state", base / "run"
    state.mkdir(mode=0o700)
    run.mkdir(mode=0o700)
    write_private(base / ".blaze-v2-rental-synthetic-only",
                  "BLAZE-V2-RENTAL-SYNTHETIC-ONLY\n")
    devices = state / "rental-devices.tsv"
    events = state / "rental-events.tsv"
    authority = state / "rental-v2-authority.json"
    write_private(devices, "dev01\tfake-secret\t0\tSynthetic device\t0\n")
    write_private(events, "")
    env = os.environ.copy()
    env.update({
        "BP_STATE": str(state),
        "BP_RUN": str(run),
        "BP_RENTAL_DEVICES": str(devices),
        "BP_RENTAL_EVENTS": str(events),
        "BP_PAID_UNCERTAIN": str(state / "paid-state-uncertain"),
        "BP_RENTAL_V2_LAB_NOW": "123456",
        "BP_RENTAL_V2_LAB_SECONDS_PER_PULSE": "600",
    })

    seeded = command(env, "seed")
    assert seeded.returncode == 0, (seeded.returncode, seeded.stderr)
    first = command(env, "coin", "dev01", "ctrl01", "nonce01", "target01", "1")
    assert first.returncode == 0 and first.stdout == "credited\t124056\n", (
        first.returncode, first.stdout, first.stderr)
    expected_replay = command(env, "coin", "dev01", "ctrl01", "nonce01", "target01", "1")
    assert expected_replay.returncode == 0 and expected_replay.stdout == "duplicate\t124056\n", (
        expected_replay.returncode, expected_replay.stdout, expected_replay.stderr)

    # Explicitly simulate an internally valid-checksum BUT contradictory authority:
    # receipt claims 124056 prepaid seconds, device current lease was set to 0.
    # Not intended to model a keyed signature or independent monotonic witness.
    envelope = json.loads(authority.read_bytes())
    assert len(envelope["body"]["receipts"]) == 1
    assert envelope["body"]["receipts"][0]["lease"] == 124056
    envelope["body"]["devices"][0]["lease"] = 0
    envelope["checksum"] = hashlib.sha256(canonical(envelope["body"])).hexdigest()
    write_private(authority, canonical(envelope) + b"\n")
    before_authority = authority.read_bytes()
    before_devices = devices.read_bytes()
    before_events = events.read_bytes()

    for ident in ("nonce01", "nonce02"):
        # Duplicate and fresh coin events must BOTH reject, without rebuilding a
        # regressed projection or acknowledging money from contradictory authority.
        result = command(env, "coin", "dev01", "ctrl01", ident, "target01", "1")
        unchanged = (authority.read_bytes() == before_authority
                     and devices.read_bytes() == before_devices
                     and events.read_bytes() == before_events)
        if result.returncode == 0 or result.stdout or not unchanged:
            raise AssertionError(
                "RENT-V2FLOOR RED: internally regressed lease accepted/replayed "
                f"or mutated projections (nonce={ident}, rc={result.returncode}, "
                f"stdout={result.stdout!r}, unchanged={unchanged})"
            )
        assert not result.stderr, result.stderr

    print("RENT-V2FLOOR PASS: synthetic contradictory lease/receipt rejected "
          "before replay, new coin and projection writes")
    print("NOT PRODUCTION: no independent rollback witness, signer, v1 migration "
          "or physical powercut acceptance")
finally:
    shutil.rmtree(base)
