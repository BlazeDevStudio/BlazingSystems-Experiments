#!/usr/bin/env python3
"""RENT-0725: synthetic real rental coin entrypoint → one authority transaction.
NO customer devices, signed controller production ACKs, v1 migration or keys.
"""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("/tmp/blaze-v2-rental-" + os.urandom(7).hex())
STATE = BASE / "state"
RUN = BASE / "run"
HELPER = ROOT / "tests/fixtures/rental_v2_atomic.py"
COMMON = ROOT / "openwrt/rootfs/usr/lib/blazepwifi/common.sh"
RENTAL = ROOT / "openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
LEDGER = STATE / "rental-v2-authority.json"
DEVICES = STATE / "rental-devices.tsv"
EVENTS = STATE / "rental-events.tsv"
MARKER = BASE / ".blaze-v2-rental-synthetic-only"
assert not (ROOT / "openwrt/rootfs/usr/lib/blazepwifi/rental_v2_atomic.py").exists()


def file(path, data):
    path.write_text(data)
    path.chmod(0o600)


def env(**overrides):
    values = os.environ.copy()
    values.update({
        "BP_STATE": str(STATE), "BP_RUN": str(RUN),
        "BP_RENTAL_DEVICES": str(DEVICES),
        "BP_RENTAL_EVENTS": str(EVENTS),
        "BP_PAID_UNCERTAIN": str(STATE / "paid-state-uncertain"),
        "BP_RENTAL_V2_LAB": "1",
        "BP_RENTAL_V2_LAB_HELPER": str(HELPER),
        "BP_RENTAL_V2_LAB_NOW": "123456",
        "BP_RENTAL_V2_LAB_SECONDS_PER_PULSE": "600",
    })
    values.update(overrides)
    return values


def call(*args, **overrides):
    script = """
      . "$1"; . "$2"; shift 2
      # Source first: common.sh deliberately pins derived path variables.
      # Inject only after sourcing to test the *actual runtime guard*.
      case "${RENT_TEST_OVERRIDE_KEY:-}" in
        BP_RENTAL_DEVICES) BP_RENTAL_DEVICES="$RENT_TEST_OVERRIDE_VALUE"; export BP_RENTAL_DEVICES ;;
        BP_RENTAL_EVENTS) BP_RENTAL_EVENTS="$RENT_TEST_OVERRIDE_VALUE"; export BP_RENTAL_EVENTS ;;
        BP_PAID_UNCERTAIN) BP_PAID_UNCERTAIN="$RENT_TEST_OVERRIDE_VALUE"; export BP_PAID_UNCERTAIN ;;
      esac
      bp_init_dirs() { :; }
      bp_cfg() { [ "$1" = rental_seconds_per_pulse ] && printf 600 || printf ''; }
      bp_now() { printf 123456; }
      bp_rental_apply_coin "$@"
    """
    return subprocess.run(["sh", "-c", script, "sh", str(COMMON), str(RENTAL), *args],
                          env=env(**overrides), capture_output=True, text=True, timeout=15)


def admin(name, *args):
    script = """
      . "$1"; . "$2"; shift 2
      bp_init_dirs() { :; }
      bp_cfg() { printf ''; }
      bp_now() { printf 123456; }
      "$@"
    """
    return subprocess.run(["sh", "-c", script, "sh", str(COMMON), str(RENTAL), name, *args],
                          env=env(), capture_output=True, text=True, timeout=15)


def digest():
    return hashlib.sha256(LEDGER.read_bytes()).hexdigest()


def lease(did):
    rows = [x.split("\t") for x in DEVICES.read_text().splitlines()]
    return int(next(row[2] for row in rows if row[0] == did))


def receipt_count(event_nonce):
    import json
    body = json.loads(LEDGER.read_text())["body"]
    return len([r for r in body["receipts"] if r["nonce"] == event_nonce])


def check(proc, code=0, stdout=None):
    assert proc.returncode == code, (
        f"unexpected exit {proc.returncode} expected {code}: {proc.stderr}/{proc.stdout}")
    assert not proc.stderr, proc.stderr
    if stdout is not None:
        assert proc.stdout == stdout, (proc.stdout, stdout)


try:
    BASE.mkdir(mode=0o700)
    STATE.mkdir(mode=0o700)
    RUN.mkdir(mode=0o700)
    file(MARKER, "BLAZE-V2-RENTAL-SYNTHETIC-ONLY\n")
    file(DEVICES, "dev01\tfake-secret\t0\tSynthetic Device\t0\n"
                  "dev02\tfake-secret-2\t200000\tOther Device\t0\n")
    file(EVENTS, "")
    check(subprocess.run([sys.executable, str(HELPER), "seed"],
                         env=env(), capture_output=True, text=True))
    baseline = digest()
    check(call("dev01", "ctrlA", "nonce1", "targetA", "2"),
          stdout="credited\t124656\n")
    assert lease("dev01") == 124656 and lease("dev02") == 200000
    assert receipt_count("nonce1") == 1
    first = digest()
    check(call("dev01", "ctrlA", "nonce1", "targetA", "2"),
          stdout="duplicate\t124656\n")
    assert digest() == first
    check(call("dev01", "ctrlA", "nonce1", "targetA", "3"), code=5)
    check(call("dev02", "ctrlA", "nonce1", "targetA", "2"), code=5)
    assert digest() == first

    # Nothing is committed if interrupted before the authoritative rename.
    check(call("dev01", "ctrlA", "nonce2", "targetA", "1",
               BP_RENTAL_V2_LAB_FAULT="before-authority-rename"), code=86)
    assert digest() == first and lease("dev01") == 124656
    assert receipt_count("nonce2") == 0

    # Lost ACK after rename: source of truth contains both money and receipt,
    # even if legacy projection was not yet rebuilt.
    check(call("dev01", "ctrlA", "nonce2", "targetA", "1",
               BP_RENTAL_V2_LAB_FAULT="after-authority-rename"), code=86)
    after = digest()
    assert after != first and lease("dev01") == 124656
    assert receipt_count("nonce2") == 1
    check(call("dev01", "ctrlA", "nonce2", "targetA", "1"),
          stdout="duplicate\t125256\n")
    assert lease("dev01") == 125256 and receipt_count("nonce2") == 1
    assert digest() == after

    # Failed projection after a single authority commit must not ACK. Retry
    # repairs both derived files and does not double-credit.
    check(call("dev01", "ctrlA", "nonce3", "targetA", "1",
               BP_RENTAL_V2_LAB_FAULT="projection-eio"), code=8)
    assert lease("dev01") == 125256 and receipt_count("nonce3") == 1
    check(call("dev01", "ctrlA", "nonce3", "targetA", "1"),
          stdout="duplicate\t125856\n")
    assert lease("dev01") == 125856 and receipt_count("nonce3") == 1

    # Derived-state corruption is repaired from the ledger, not imported.
    snapshot = digest()
    file(DEVICES, "dev01\tforged\t0\ttampered\t0\n")
    file(EVENTS, "tampered\tbad\n")
    check(call("dev01", "ctrlA", "nonce3", "targetA", "1"),
          stdout="duplicate\t125856\n")
    assert lease("dev01") == 125856 and receipt_count("nonce3") == 1
    assert digest() == snapshot

    # Refuse an unauthorized mutation of the signed-independent authority.
    good = LEDGER.read_bytes()
    LEDGER.write_bytes(good.replace(b"dev01", b"devZZ"))
    check(call("dev01", "ctrlA", "nonce4", "targetA", "1"), code=8)
    assert lease("dev01") == 125856
    LEDGER.write_bytes(good)
    LEDGER.chmod(0o600)

    # In lab mode, all original admin mutation paths must fail closed.
    check(admin("bp_rental_lease_add", "dev01", "600"), code=9)
    check(admin("bp_rental_lease_expire", "dev01", "CONFIRM_FORFEIT"), code=9)
    check(admin("bp_rental_device_write", "dev01", "s", "0", "x", "0"), code=9)
    assert digest() == snapshot

    # Missing, relative or untrusted helper: no mutation or success ACK.
    for helper in ("", "tests/fixtures/rental_v2_atomic.py", str(BASE / "missing.py")):
        check(call("dev01", "ctrlA", "nonce4", "targetA", "1",
                   BP_RENTAL_V2_LAB_HELPER=helper), code=9)
    assert digest() == snapshot

    # An override for ANY derived path must fail before Python can write.
    file(BASE / "external-sentinel", "UNCHANGED\n")
    for key in ("BP_RENTAL_DEVICES", "BP_RENTAL_EVENTS", "BP_PAID_UNCERTAIN"):
        check(call("dev01", "ctrlA", "nonce4", "targetA", "1",
                   RENT_TEST_OVERRIDE_KEY=key,
                   RENT_TEST_OVERRIDE_VALUE=str(BASE / "external-sentinel")), code=9)
        assert (BASE / "external-sentinel").read_text() == "UNCHANGED\n"
    check(call("dev01", "ctrlA", "nonce4", "targetA", "1",
               BP_STATE="/etc/blazepwifi/state"), code=9)
    assert digest() == snapshot

    file(STATE / "paid-state-uncertain", "PENDING\n")
    check(call("dev01", "ctrlA", "nonce4", "targetA", "1"), code=9)
    (STATE / "paid-state-uncertain").unlink()
    assert digest() == snapshot and baseline != snapshot
    print("RENT-0725 PASS: real rental coin entrypoint synthetic-only lease+receipt one-rename, lost ACK, projection recovery, collision, tamper and path guards")
    print("NOT PRODUCTION: no signed v2 controller contract, independently witnessed antirollback, v1 migration or physical powercut proof")
finally:
    shutil.rmtree(BASE, ignore_errors=True)
