#!/usr/bin/env python3
"""WITNESS-0738: an operator-provisioned off-device durable floor *candidate*.

This is a local, non-networked witness datastore protocol, NOT a certified
monotonic hardware primitive, controller signer, or production payment service.
It cannot inspect a router's fsync, establish off-device physical independence,
securely pin a remote target identity or authorize a prepaid ACK. A full
SQLite+key snapshot can be restored together: hardware antirollback is OPEN.

A separately managed operator must provision a private root with:
  0700 owner-only directory; regular 0600 "secret.hex" (64 lowercase hex);
  regular 0600 ".witness-candidate-only" containing exact marker below.
No keys or roots are created automatically by this program.
No listening sockets, background processes, private key generation, customer
accounts, OpenWrt installation, money writes, or ACKP1 responses exist.
"""
import hashlib
import hmac
import json
import os
import re
import sqlite3
import stat
import sys
from pathlib import Path

DOMAIN = "BLAZE-WITNESS-CANDIDATE/1"
# Preserve WITNESS-0739's already-integrated status response protocol.
STATUS_DOMAIN = "BLAZE-WITNESS-CANDIDATE-STATUS/1"
# WITNESS-0740 authenticates non-status candidate transaction receipts too.
TRANSACTION_REPLY_DOMAIN = "BLAZE-WITNESS-CANDIDATE-TRANSACTION-REPLY/1"
MARKER = "BLAZE-WITNESS-CANDIDATE-NOT-HARDWARE-ATTESTED\n"
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
HEX32 = re.compile(r"[a-f0-9]{32,64}\Z")
DEVICE = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,31}\Z")
MAX_FLOOR = 1000000000000
SCHEMA = """
CREATE TABLE IF NOT EXISTS floors (
  device TEXT PRIMARY KEY,
  epoch INTEGER NOT NULL,
  revision INTEGER NOT NULL,
  digest TEXT NOT NULL,
  pending_revision INTEGER,
  pending_digest TEXT,
  pending_nonce TEXT
);
CREATE TABLE IF NOT EXISTS finalized (
  device TEXT NOT NULL,
  epoch INTEGER NOT NULL,
  revision INTEGER NOT NULL,
  digest TEXT NOT NULL,
  nonce TEXT NOT NULL,
  PRIMARY KEY(device, epoch, revision)
);
"""

def refuse(reason):
    print("WITNESS-0738 BLOCKED: " + reason + " (NO PAID ACK)", file=sys.stderr)
    raise SystemExit(9)

def owned_regular(path, mode=0o600):
    try:
        st = os.lstat(path)
    except OSError:
        refuse("required protected file missing")
    if (not stat.S_ISREG(st.st_mode) or stat.S_IMODE(st.st_mode) != mode
            or st.st_uid != os.geteuid() or st.st_nlink != 1):
        refuse("unsafe protected file owner/mode/link")
    return st

def strict_floor(value, zero=False):
    if not re.fullmatch(r"(0|[1-9][0-9]{0,12})", value):
        refuse("noncanonical revision/epoch")
    n = int(value)
    if n > MAX_FLOOR or (not zero and n == 0):
        refuse("revision/epoch outside safety bounds")
    return n

def check_root(raw):
    if not os.path.isabs(raw) or raw != os.path.realpath(raw):
        refuse("root must be absolute and free of symlink ancestors")
    if raw == "/" or raw.startswith(("/etc/blazepwifi/", "/tmp/blazepwifi/")):
        refuse("cannot use router/customer financial directory")
    st = os.lstat(raw)
    if not stat.S_ISDIR(st.st_mode) or stat.S_IMODE(st.st_mode) != 0o700 or st.st_uid != os.geteuid():
        refuse("private owned candidate directory required")
    marker = Path(raw) / ".witness-candidate-only"
    owned_regular(marker)
    if marker.read_bytes() != MARKER.encode("ascii"):
        refuse("explicit candidate-only marker missing")
    # CI fault injection may NEVER target arbitrary non-fixture directories.
    is_fixture = raw.startswith("/tmp/blaze-witness0738-") and "/" not in raw[len("/tmp/blaze-witness0738-"):]
    return Path(raw), is_fixture

def parse(command, values):
    counts = {"init": 4, "prepare": 7, "finalize": 5, "status": 2}
    if command not in counts or len(values) != counts[command] + 1:
        refuse("usage: ROOT COMMAND ARGUMENTS AUTH_HEX64")
    if not DEVICE.fullmatch(values[0]):
        refuse("invalid witness device")
    if command == "init":
        strict_floor(values[1])
        strict_floor(values[2])
        if not HEX64.fullmatch(values[3]): refuse("invalid ledger digest")
    if command == "prepare":
        strict_floor(values[1])
        base, new = strict_floor(values[2], zero=True), strict_floor(values[4])
        if new != base + 1: refuse("nonadjacent revision")
        if not HEX64.fullmatch(values[3]) or not HEX64.fullmatch(values[5]):
            refuse("invalid ledger digest")
        if not HEX32.fullmatch(values[6]): refuse("invalid unique nonce")
    if command == "finalize":
        strict_floor(values[1])
        strict_floor(values[2])
        if not HEX64.fullmatch(values[3]) or not HEX32.fullmatch(values[4]):
            refuse("invalid finalize envelope")
    if command == "status" and not HEX32.fullmatch(values[1]):
        refuse("invalid status challenge nonce")
    if not HEX64.fullmatch(values[-1]):
        refuse("invalid request authenticator")

def canonical(command, args):
    return (DOMAIN + "\t" + command + "\t" + "\t".join(args) + "\n").encode("ascii")

def open_store(root, initialize):
    path = root / "witness.sqlite3"
    if path.exists() or path.is_symlink():
        owned_regular(path)
    elif not initialize:
        refuse("witness database not initialized")
    for suffix in ("-wal", "-shm", "-journal"):
        side = Path(str(path) + suffix)
        if side.exists() or side.is_symlink():
            owned_regular(side) if suffix != "-shm" else owned_regular(side)  # 0600 only
    # Existing private directory with no peer-write permission protects the
    # sqlite sidecars against untrusted replacement, not malicious root.
    os.umask(0o077)
    con = sqlite3.connect(str(path), timeout=5, isolation_level=None)
    if con.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() != "wal":
        refuse("SQLite WAL unavailable")
    con.execute("PRAGMA synchronous=FULL")
    if con.execute("PRAGMA synchronous").fetchone()[0] != 2:
        refuse("SQLite FULL sync unavailable")
    con.execute("PRAGMA foreign_keys=ON")
    owned_regular(path)
    con.executescript(SCHEMA)
    return con

def reply(state, floor, pending=False, *, challenge=None, key=None,
          request_sha256=None):
    # Candidate only. NO positive paid ACK or independently attested witness.
    # All replies must be authenticated to the exact inbound request.
    if key is None or request_sha256 is None:
        refuse("candidate response authentication unavailable")
    status = challenge is not None
    result = {
      "schema": DOMAIN, "state": state,
      "witness_revision": floor[2], "witness_epoch": floor[1],
      "witness_digest": floor[3],
      "pending_reconciliation": bool(pending),
      # Matching PREPARE tuple is necessary for manual ambiguous recovery.
      # Authentication does NOT independently prove the target's fsync.
      "pending_revision": floor[4] if pending else None,
      "pending_digest": floor[5] if pending else None,
      "pending_nonce": floor[6] if pending else None,
      "request_sha256": request_sha256,
      "reply_schema": STATUS_DOMAIN if status else TRANSACTION_REPLY_DOMAIN,
      "independent_monotonic_witness_verified": False,
      "financial_migration_authorized": False,
      "paid_ack_authorized": False,
      "customer_install_authorized": False
    }
    if status:
        # Keep merged PR #79 STATUS/1 response_challenge and response_mac
        # formatting; its existing independent verifier must remain valid.
        result["response_challenge"] = challenge
    canonical_reply = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("ascii")
    if status:
        envelope = STATUS_DOMAIN.encode("ascii") + b"\n" + canonical_reply + b"\n"
    else:
        envelope = (TRANSACTION_REPLY_DOMAIN + "\t" + request_sha256 + "\t").encode("ascii") + canonical_reply + b"\n"
    result["response_mac"] = hmac.new(key, envelope, hashlib.sha256).hexdigest()
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))

def fault(stage, fixture):
    if fixture and os.environ.get("BLAZE_WITNESS0738_TEST_FAULT") == stage:
        os._exit(73)

def operate(con, command, args, fixture, key):
    # The authenticated response is bound to every original request field.
    # STATUS includes caller-generated fresh challenge in this exact hash.
    request_sha = hashlib.sha256(canonical(command, args)).hexdigest()
    def bound_reply(state, floor, pending=False, *, challenge=None):
        reply(state, floor, pending, challenge=challenge, key=key,
              request_sha256=request_sha)
    device = args[0]
    con.execute("BEGIN IMMEDIATE")
    row = con.execute(
      "SELECT device,epoch,revision,digest,pending_revision,pending_digest,pending_nonce"
      " FROM floors WHERE device=?", (device,)).fetchone()
    if command == "init":
        if row: refuse("genesis reset forbidden")
        epoch, rev, digest = int(args[1]), int(args[2]), args[3]
        con.execute("INSERT INTO floors(device,epoch,revision,digest) VALUES(?,?,?,?)",
                    (device, epoch, rev, digest))
        row = (device, epoch, rev, digest, None, None, None)
        fault("before_init_commit", fixture)
        con.commit()
        fault("after_init_commit", fixture)
        bound_reply("GENESIS_CANDIDATE_ONLY", row)
        return
    if row is None: refuse("unknown witness device")
    if command == "status":
        con.commit()
        bound_reply("PENDING_RECONCILIATION" if row[4] is not None else "OBSERVED_CANDIDATE_ONLY",
              row, row[4] is not None, challenge=args[1])
        return
    epoch, revision, digest = int(args[1]), int(args[2]), args[3]
    if epoch != row[1]: refuse("wrong migration epoch")
    if command == "prepare":
        # PREPARE: device epoch old_revision old_digest new_revision new_digest nonce
        _, _, old_rev, old_digest, new_rev, new_digest, nonce = args
        if row[4] is not None:
            if row[4] != int(new_rev) or row[5] != new_digest or row[6] != nonce:
                refuse("conflicting pending operation; reconcile before mutation")
            con.commit()
            bound_reply("PREPARED_NOT_COMMITTED", row, True)
            return
        old = con.execute(
          "SELECT nonce,digest FROM finalized WHERE device=? AND epoch=? AND revision=?",
          (device, epoch, int(new_rev))).fetchone()
        if old:
            if old != (nonce, new_digest): refuse("finalized revision collision")
            con.commit()
            bound_reply("ALREADY_FINALIZED_NO_PAID_ACK", row)
            return
        if row[2] != int(old_rev) or row[3] != old_digest:
            refuse("stale/rolled-back local base snapshot")
        con.execute(
          "UPDATE floors SET pending_revision=?,pending_digest=?,pending_nonce=? WHERE device=?",
          (int(new_rev), new_digest, nonce, device))
        row = (device, epoch, row[2], row[3], int(new_rev), new_digest, nonce)
        fault("before_prepare_commit", fixture)
        con.commit()
        fault("after_prepare_commit", fixture)
        bound_reply("PREPARED_NOT_COMMITTED", row, True)
        return
    # FINALIZE: authenticated target claims local fsync completed, but this
    # *candidate* cannot verify hardware fsync or monotonic external storage.
    # The only useful outcome is a durable candidate floor, NEVER a paid ACK.
    nonce = args[4]
    if row[4] is None:
        old = con.execute(
          "SELECT nonce,digest FROM finalized WHERE device=? AND epoch=? AND revision=?",
          (device, epoch, revision)).fetchone()
        if old != (nonce, digest):
            refuse("not prepared or disputed replay")
        con.commit()
        bound_reply("ALREADY_FINALIZED_NO_PAID_ACK", row)
        return
    if row[4] != revision or row[5] != digest or row[6] != nonce:
        refuse("mismatched pending finalize")
    if row[2] + 1 != revision: refuse("nonadjacent pending finalize")
    con.execute(
      "UPDATE floors SET revision=?, digest=?, pending_revision=NULL,"
      " pending_digest=NULL,pending_nonce=NULL WHERE device=?",
      (revision, digest, device))
    con.execute(
      "INSERT INTO finalized(device,epoch,revision,digest,nonce) VALUES(?,?,?,?,?)",
      (device, epoch, revision, digest, nonce))
    row = (device, epoch, revision, digest, None, None, None)
    fault("before_finalize_commit", fixture)
    con.commit()
    fault("after_finalize_commit", fixture)
    bound_reply("FINALIZED_CANDIDATE_NO_PAID_ACK", row)

def main():
    if len(sys.argv) < 5: refuse("usage: ROOT {init|prepare|finalize|status} ...")
    root, fixture = check_root(sys.argv[1])
    command = sys.argv[2]
    args, auth = sys.argv[3:-1], sys.argv[-1]
    parse(command, args + [auth])
    keypath = root / "secret.hex"
    owned_regular(keypath)
    raw = keypath.read_bytes()
    if len(raw) != 65 or raw[-1:] != b"\n" or not HEX64.fullmatch(raw[:-1].decode("ascii")):
        refuse("invalid operator-provisioned authentication key")
    key = bytes.fromhex(raw[:-1].decode("ascii"))
    expected = hmac.new(key, canonical(command, args), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(auth, expected):
        refuse("bad request authentication")
    try:
        con = open_store(root, command == "init")
        try:
            operate(con, command, args, fixture, key)
        finally:
            con.close()
    except (sqlite3.Error, OSError, ValueError) as exc:
        # Do not leak paths or SQL state into public automation logs.
        refuse("durable candidate storage/transaction unavailable")

if __name__ == "__main__":
    main()
