#!/usr/bin/env python3
"""RENT-0725: OFF-DEVICE synthetic single-authority lease+receipt integration.

Not installed in rootfs. No v1 customer migration, HMAC witness, actual
hardware power-cut, signed controller enrollment or production ACK authority.
A SHA-256 checksum is corruption detection, NOT independent antirollback.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

PREFIX = "/tmp/blaze-v2-rental-"
MAGIC = "BLAZE-V2-RENTAL-SYNTHETIC-ONLY\n"
SCHEMA = "BLAZE_RENTAL_V2_SYNTHETIC_V1"
MAX = 2147483647
ID = re.compile(r"[A-Za-z0-9_.:-]{2,96}\Z")
HEX = re.compile(r"r:[0-9a-f]{64}\Z")
STATE_KEYS = ("BP_STATE", "BP_RUN", "BP_RENTAL_DEVICES", "BP_RENTAL_EVENTS",
              "BP_PAID_UNCERTAIN")


class Reject(Exception):
    def __init__(self, code=8):
        self.code = code


def reject(allowed, code=8):
    if not allowed:
        raise Reject(code)


def decimal(value, max_value=MAX):
    reject(re.fullmatch(r"0|[1-9][0-9]*", str(value)) is not None)
    reject(len(str(value)) <= 10)
    number = int(value)
    reject(number <= max_value)
    return number


def private(path, directory=False):
    st = path.lstat()
    reject(stat.S_ISDIR(st.st_mode) if directory else stat.S_ISREG(st.st_mode))
    reject(st.st_uid == os.geteuid() and not (st.st_mode & 0o077))
    if not directory:
        reject(st.st_nlink == 1)
    return st


def paths():
    root = os.environ.get("BP_STATE", "")
    reject(root.startswith(PREFIX) and root.endswith("/state"), 9)
    suffix = root[len(PREFIX):-len("/state")]
    reject(re.fullmatch(r"[A-Za-z0-9]{6,32}", suffix) is not None, 9)
    top = Path(root[:-len("/state")])
    state, run = top / "state", top / "run"
    expected = {
        "BP_STATE": str(state), "BP_RUN": str(run),
        "BP_RENTAL_DEVICES": str(state / "rental-devices.tsv"),
        "BP_RENTAL_EVENTS": str(state / "rental-events.tsv"),
        "BP_PAID_UNCERTAIN": str(state / "paid-state-uncertain"),
    }
    reject(all(os.environ.get(k) == v for k, v in expected.items()), 9)
    for p in (top, state, run):
        reject(p.is_absolute(), 9)
        private(p, directory=True)
        reject(stat.S_IMODE(p.stat().st_mode) == 0o700, 9)
    marker = top / ".blaze-v2-rental-synthetic-only"
    private(marker)
    reject(stat.S_IMODE(marker.stat().st_mode) == 0o600, 9)
    reject(marker.read_text() == MAGIC, 9)
    reject(not (state / "paid-state-uncertain").exists()
           and not (state / "paid-state-uncertain").is_symlink(), 9)
    return state, run


def canonical(body):
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def seal(body):
    packed = canonical(body)
    return canonical({"body": body, "checksum": hashlib.sha256(packed).hexdigest()}) + b"\n"


def valid(body):
    reject(isinstance(body, dict) and set(body) == {"schema", "revision", "devices", "receipts"})
    reject(body["schema"] == SCHEMA)
    decimal(body["revision"])
    reject(isinstance(body["devices"], list) and 0 < len(body["devices"]) <= 5000)
    reject(isinstance(body["receipts"], list) and len(body["receipts"]) <= 100000)
    ids, events = set(), set()
    for row in body["devices"]:
        reject(isinstance(row, dict) and set(row) == {"id", "secret", "lease", "label", "last"})
        did = row["id"]
        reject(isinstance(did, str) and ID.fullmatch(did) and did not in ids)
        ids.add(did)
        reject(isinstance(row["secret"], str) and 0 < len(row["secret"]) <= 256)
        reject(isinstance(row["label"], str) and len(row["label"]) <= 80)
        reject("\t" not in row["secret"] and "\n" not in row["secret"])
        reject("\t" not in row["label"] and "\n" not in row["label"])
        decimal(row["lease"]); decimal(row["last"])
    for item in body["receipts"]:
        reject(isinstance(item, dict) and set(item) ==
               {"event", "id", "lease", "now", "pulses", "controller", "nonce", "target"})
        event = item["event"]
        reject(isinstance(event, str) and HEX.fullmatch(event) and event not in events)
        events.add(event)
        reject(item["id"] in ids)
        pulses = decimal(item["pulses"], 20)
        reject(pulses >= 1)
        decimal(item["lease"]); decimal(item["now"])
        for field in ("controller", "nonce", "target"):
            reject(isinstance(item[field], str) and 0 < len(item[field]) <= 128)
        expected = hashlib.sha256(
            ("rental|" + item["controller"] + "|" + item["nonce"] + "|" + item["target"]).encode()
        ).hexdigest()
        reject(event == "r:" + expected)


def load(path):
    private(path)
    reject(path.stat().st_size <= 12_000_000)
    try:
        envelope = json.loads(path.read_bytes())
        reject(isinstance(envelope, dict) and set(envelope) == {"body", "checksum"})
        data = envelope["body"]
        digest = hashlib.sha256(canonical(data)).hexdigest()
        reject(envelope["checksum"] == digest)
        valid(data)
        return data
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        raise Reject(8) from exc


def atomic(path, payload, fault=""):
    tmp = path.with_name(".rental-v2-intent-" + str(os.getpid()))
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    fd = os.open(str(tmp), flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(payload)
            out.flush()
            os.fsync(out.fileno())
        if fault == "before-authority-rename":
            tmp.unlink()
            raise Reject(86)
        os.replace(str(tmp), str(path))
        if fault == "after-authority-rename":
            raise Reject(86)
        dirfd = os.open(str(path.parent), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    finally:
        if tmp.exists():
            tmp.unlink()


def projection(path, lines):
    tmp = path.with_name(".rental-projection-" + path.name + "-" + str(os.getpid()))
    payload = ("\n".join(lines) + ("\n" if lines else "")).encode()
    atomic(tmp, payload)
    os.replace(str(tmp), str(path))
    dirfd = os.open(str(path.parent), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(dirfd)
    finally:
        os.close(dirfd)


def project(state, body, fault=""):
    if fault == "projection-eio":
        raise Reject(8)
    devices = ["\t".join([d["id"], d["secret"], str(d["lease"]), d["label"], str(d["last"])])
               for d in body["devices"]]
    events = ["\t".join([r["event"], r["id"], str(r["lease"]), str(r["now"]),
                          "p:" + str(r["pulses"])]) for r in body["receipts"]]
    projection(state / "rental-devices.tsv", devices)
    projection(state / "rental-events.tsv", events)


def seed(state, ledger):
    reject(not ledger.exists() and not ledger.is_symlink(), 9)
    raw = state / "rental-devices.tsv"
    events = state / "rental-events.tsv"
    private(raw); private(events)
    reject(events.stat().st_size == 0, 9)  # NO implicit paid-history import
    devices = []
    for text in raw.read_text().splitlines():
        fields = text.split("\t")
        reject(len(fields) == 5)
        devices.append(dict(zip(("id", "secret", "lease", "label", "last"), fields)))
        devices[-1]["lease"] = decimal(devices[-1]["lease"])
        devices[-1]["last"] = decimal(devices[-1]["last"])
    body = {"schema": SCHEMA, "revision": 0, "devices": devices, "receipts": []}
    valid(body)
    atomic(ledger, seal(body))
    project(state, body)


def coin(state, ledger, did, controller, nonce, target, pulses):
    reject(ID.fullmatch(did) is not None, 2)
    pulse = decimal(pulses, 20)
    reject(pulse > 0, 2)
    now = decimal(os.environ.get("BP_RENTAL_V2_LAB_NOW", ""))
    per = decimal(os.environ.get("BP_RENTAL_V2_LAB_SECONDS_PER_PULSE", ""))
    reject(1 <= per <= 86400)
    for value in (controller, nonce, target):
        reject(bool(value) and len(value) <= 128, 2)
    event = "r:" + hashlib.sha256(
        ("rental|" + controller + "|" + nonce + "|" + target).encode()).hexdigest()
    body = load(ledger)
    project(state, body)  # reconstruct any torn derived files before replay
    prev = next((r for r in body["receipts"] if r["event"] == event), None)
    if prev:
        reject(prev["id"] == did and prev["pulses"] == pulse and
               prev["controller"] == controller and prev["nonce"] == nonce and
               prev["target"] == target, 5)
        print("duplicate\t" + str(prev["lease"]))
        return
    row = next((r for r in body["devices"] if r["id"] == did), None)
    reject(row is not None, 2)
    delta = per * pulse
    base = max(row["lease"], now)
    reject(base <= MAX - delta)
    newlease = base + delta
    row["lease"] = newlease
    row["last"] = now
    body["revision"] += 1
    body["receipts"].append({
        "event": event, "id": did, "lease": newlease, "now": now,
        "pulses": pulse, "controller": controller, "nonce": nonce, "target": target,
    })
    valid(body)
    fault = os.environ.get("BP_RENTAL_V2_LAB_FAULT", "")
    atomic(ledger, seal(body), fault=fault)
    project(state, body, fault=fault)
    print("credited\t" + str(newlease))


def main():
    reject(len(sys.argv) in (2, 7), 2)
    state, run = paths()
    lockfile = run / "paid-financial.lock"
    fd = os.open(str(lockfile), os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    try:
        private(lockfile)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Reject(8) from exc
        ledger = state / "rental-v2-authority.json"
        if sys.argv[1] == "seed" and len(sys.argv) == 2:
            seed(state, ledger)
        elif sys.argv[1] == "coin" and len(sys.argv) == 7:
            coin(state, ledger, *sys.argv[2:])
        else:
            raise Reject(2)
    finally:
        os.close(fd)


if __name__ == "__main__":
    try:
        main()
    except (Reject, OSError) as error:
        sys.exit(error.code if isinstance(error, Reject) else 8)
