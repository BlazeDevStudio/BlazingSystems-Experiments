#!/usr/bin/env python3
"""MIG-0645: strictly read-only redacted inventory for synthetic v1 money state.

NOT a production migration tool, backup, device preflight or quiescence proof.
Only accepts /tmp/blaze-v1-audit-* marker-guarded disposable test directories.
This tool reads metadata and sums, never displays raw account IDs, device keys,
customer names, passwords, receipts, enrollment codes or SHA of private files.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys

PREFIX = "/tmp/blaze-v1-audit-"
MARKER = ".blaze-v1-fixture-only"
MAGIC = b"BLAZE-V1-SYNTHETIC-INVENTORY-ONLY\n"
MAX_BYTES = 16 * 1024 * 1024
MAX_TOTAL = 200 * 1024 * 1024
MAX_INT = 2**63 - 1
REQUIRED = (
    "accounts.tsv", "members.tsv", "member-events.tsv",
    "member-revision", "rental-devices.tsv", "rental-events.tsv",
    "vouchers.tsv",
)
OPTIONAL = ("credits.tsv", "sessions.tsv")
KEY_RE = re.compile(r"^[A-Za-z0-9_.:-]{2,96}$")
MEMBER_RE = re.compile(r"^[A-Za-z0-9_.-]{2,32}$")
MAC_RE = re.compile(r"^[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}$")


class InvalidState(Exception):
    def __init__(self, code: str):
        self.code = code


def number(value: str, *, signed: bool = False) -> int:
    if not re.fullmatch(r"-?(0|[1-9][0-9]*)" if signed else r"0|[1-9][0-9]*", value):
        raise InvalidState("INVALID_NUMERIC")
    # Python 3.11 limits very long int() input; reject it as malformed state
    # instead of producing an unredacted ValueError/traceback in preflight.
    if len(value.lstrip("-")) > 19:
        raise InvalidState("NUMERIC_OVERFLOW")
    num = int(value)
    if abs(num) > MAX_INT:
        raise InvalidState("NUMERIC_OVERFLOW")
    return num


def require(condition: bool, code: str) -> None:
    if not condition:
        raise InvalidState(code)


def private_file(dirfd: int, name: str, required: bool = True) -> bytes | None:
    try:
        fd = os.open(name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dirfd)
    except FileNotFoundError:
        if not required:
            return None
        raise InvalidState("REQUIRED_SOURCE_MISSING") from None
    except OSError:
        raise InvalidState("SOURCE_UNREADABLE_OR_SYMLINK") from None
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
                before.st_uid == os.geteuid() and
                not (before.st_mode & 0o077), "SOURCE_NOT_PRIVATE_REGULAR")
        require(0 <= before.st_size <= MAX_BYTES, "SOURCE_SIZE_UNSAFE")
        chunks = []
        size = 0
        while True:
            piece = os.read(fd, min(65536, MAX_BYTES + 1 - size))
            if not piece:
                break
            chunks.append(piece)
            size += len(piece)
            require(size <= MAX_BYTES, "SOURCE_SIZE_UNSAFE")
        after = os.fstat(fd)
        entry = os.stat(name, dir_fd=dirfd, follow_symlinks=False)
        require((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino) ==
                (entry.st_dev, entry.st_ino) and
                (before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                (after.st_size, after.st_mtime_ns, after.st_ctime_ns),
                "SOURCE_CHANGED_DURING_READ")
        require(size == before.st_size, "SOURCE_SHORT_READ")
        return b"".join(chunks)
    except OSError:
        raise InvalidState("SOURCE_READ_ERROR") from None
    finally:
        os.close(fd)


def file_stamp(dirfd: int, name: str) -> tuple | None:
    """Opaque in-process metadata only; never emit customer IDs."""
    try:
        st = os.stat(name, dir_fd=dirfd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    return (st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_nlink,
            st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def directory_stamp(fd: int) -> tuple:
    st = os.fstat(fd)
    return (st.st_dev, st.st_ino, st.st_mode, st.st_uid,
            st.st_mtime_ns, st.st_ctime_ns)


def confirm_same_file(dirfd: int, name: str, stamp: tuple | None,
                      contents: bytes | None, *, required: bool = True) -> None:
    """Best-effort volatility detector; NOT proof of quiescence."""
    require(file_stamp(dirfd, name) == stamp, "SOURCE_CHANGED_DURING_AUDIT")
    require(private_file(dirfd, name, required=required) == contents,
            "SOURCE_CHANGED_DURING_AUDIT")
    require(file_stamp(dirfd, name) == stamp, "SOURCE_CHANGED_DURING_AUDIT")


def lines(data: bytes) -> list[list[str]]:
    require(not (b"\x00" in data or b"\r" in data), "SOURCE_BINARY_OR_CR")
    if data and not data.endswith(b"\n"):
        raise InvalidState("SOURCE_UNTERMINATED_ROW")
    try:
        rows = data.decode("utf-8").splitlines()
    except UnicodeError:
        raise InvalidState("SOURCE_BAD_ENCODING") from None
    require(not any(not row for row in rows), "SOURCE_BLANK_RECORD")
    return [row.split("\t") for row in rows]


def unique(rows: list[list[str]], index: int, label: str) -> None:
    seen = set()
    for row in rows:
        key = row[index]
        if key in seen:
            raise InvalidState(label + "_DUPLICATE_ID")
        seen.add(key)


def money_total(rows: list[list[str]], column: int) -> int:
    total = 0
    for row in rows:
        total += number(row[column])
        require(total <= MAX_INT, "AGGREGATE_OVERFLOW")
    return total


def audit(root: Path) -> dict:
    absolute = str(root)
    require(absolute.startswith(PREFIX) and
            len(absolute) > len(PREFIX) and
            "/" not in absolute[len(PREFIX):] and
            os.path.realpath(absolute) == absolute, "NONFIXTURE_ROOT")
    try:
        dirfd = os.open(absolute, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
    except OSError:
        raise InvalidState("UNSAFE_ROOT") from None
    try:
        rootstat = os.fstat(dirfd)
        require(stat.S_ISDIR(rootstat.st_mode) and
                rootstat.st_uid == os.geteuid() and
                (rootstat.st_mode & 0o077) == 0,
                "ROOT_NOT_PRIVATE")
        start_root_stamp = directory_stamp(dirfd)
        marker_stamp = file_stamp(dirfd, MARKER)
        require(private_file(dirfd, MARKER) == MAGIC, "FIXTURE_MARKER_INVALID")
        require(file_stamp(dirfd, MARKER) == marker_stamp,
                "SOURCE_CHANGED_DURING_AUDIT")
        # Never declare the source comprehensively inventoried if a future,
        # unknown or half-written paid-state sidecar was omitted entirely.
        # This is a strict disposable fixture schema, not live migration.
        allowed_entries = set((*REQUIRED, *OPTIONAL, MARKER,
                               "targets", "paid-state-uncertain"))
        root_entries = set(os.listdir(dirfd))
        require(root_entries <= allowed_entries,
                "UNRECOGNIZED_SOURCE_ENTRY")
        data: dict[str, bytes] = {}
        stamps: dict[str, tuple | None] = {}
        total_bytes = 0
        for name in (*REQUIRED, *OPTIONAL):
            before_stamp = file_stamp(dirfd, name)
            value = private_file(dirfd, name, required=name in REQUIRED)
            require(file_stamp(dirfd, name) == before_stamp,
                    "SOURCE_CHANGED_DURING_AUDIT")
            stamps[name] = before_stamp
            if value is not None:
                total_bytes += len(value)
                require(total_bytes <= MAX_TOTAL, "TOTAL_SIZE_UNSAFE")
                data[name] = value
        # No keys or opaque source rows appear in the public JSON output.
        accounts = lines(data["accounts.tsv"])
        members = lines(data["members.tsv"])
        events = lines(data["member-events.tsv"])
        rentals = lines(data["rental-devices.tsv"])
        rental_events = lines(data["rental-events.tsv"])
        vouchers = lines(data["vouchers.tsv"])

        for row in accounts:
            require(len(row) == 9 and bool(KEY_RE.fullmatch(row[0])), "ACCOUNTS_SCHEMA")
            for c in (1, 2, 3, 4, 5):
                number(row[c])
            require(row[4] in ("0", "1"), "ACCOUNTS_PAUSE_FLAG")
            require(len(row[8]) <= 131072, "ACCOUNTS_RECEIPT_SIZE")
        unique(accounts, 0, "ACCOUNTS")

        for row in members:
            require(len(row) == 11 and bool(MEMBER_RE.fullmatch(row[0])),
                    "MEMBERS_SCHEMA")
            require(row[2] in ("0", "1"), "MEMBERS_ENABLED_FLAG")
            number(row[7])
            number(row[8])
        unique(members, 0, "MEMBERS")

        for row in events:
            require(len(row) == 8 and bool(row[0]) and bool(row[2]),
                    "MEMBER_EVENTS_SCHEMA")
            number(row[1])
            number(row[4], signed=True)
            number(row[5])
        unique(events, 0, "MEMBER_EVENTS")
        member_ids = {row[0] for row in members}
        require(all(row[2] in member_ids for row in events),
                "MEMBER_EVENT_ORPHAN")

        for row in rentals:
            require(len(row) == 5 and bool(KEY_RE.fullmatch(row[0])),
                    "RENTAL_DEVICES_SCHEMA")
            number(row[2])
            number(row[4])
        unique(rentals, 0, "RENTAL_DEVICES")

        for row in rental_events:
            require(len(row) in (4, 5) and bool(row[0]) and bool(row[1]),
                    "RENTAL_EVENTS_SCHEMA")
            number(row[3])
        paid_rental_events = [r for r in rental_events if r[0].startswith("r:")]
        unique(paid_rental_events, 0, "PAID_RENTAL_EVENTS")
        rental_ids = {row[0] for row in rentals}
        require(all(row[1] in rental_ids for row in paid_rental_events),
                "PAID_RENTAL_EVENT_ORPHAN")

        for row in vouchers:
            require(len(row) in (2, 3) and bool(row[0]), "VOUCHERS_SCHEMA")
            number(row[1])
        unique(vouchers, 0, "VOUCHERS")

        rawrev = data["member-revision"]
        require(re.fullmatch(rb"[0-9]+\n", rawrev) is not None,
                "MEMBER_REVISION_SCHEMA")
        revision = number(rawrev.strip().decode("ascii"))
        max_member_revision = max([0] + [number(x[8]) for x in members])
        require(revision >= max_member_revision, "MEMBER_REVISION_REGRESSION")

        legacy_count = {}
        for name in OPTIONAL:
            if name not in data:
                legacy_count[name] = 0
                continue
            legacy = lines(data[name])
            for row in legacy:
                require(len(row) == 2 and bool(MAC_RE.fullmatch(row[0])),
                        "LEGACY_SCHEMA")
                number(row[1])
            unique(legacy, 0, "LEGACY")
            legacy_count[name] = len(legacy)

        # A marker requires operator reconciliation. This is a read-only
        # observation and cannot initiate/simulate the paid lock or clear it.
        disputed = None
        try:
            disputed = private_file(dirfd, "paid-state-uncertain", required=False)
        except InvalidState:
            raise InvalidState("UNCERTAINTY_MARKER_UNSAFE") from None
        if disputed is not None:
            raise InvalidState("FINANCIAL_STATE_QUARANTINED")

        try:
            targetsfd = os.open("targets", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                dir_fd=dirfd)
        except OSError:
            raise InvalidState("TARGETS_DIR_MISSING_OR_UNSAFE") from None
        try:
            st = os.fstat(targetsfd)
            require(stat.S_ISDIR(st.st_mode) and st.st_uid == os.geteuid() and
                    (st.st_mode & 0o077) == 0, "TARGETS_DIR_NOT_PRIVATE")
            account_ids = {row[0] for row in accounts}
            start_targets_stamp = directory_stamp(targetsfd)
            names = os.listdir(targetsfd)
            target_snapshots: dict[str, tuple[tuple | None, bytes]] = {}
            targets = 0
            for name in names:
                require(re.fullmatch(r"[A-Za-z0-9_.-]{1,96}\.tsv", name) is not None,
                        "TARGET_UNRECOGNIZED_ENTRY")
                before_stamp = file_stamp(targetsfd, name)
                d = private_file(targetsfd, name)
                require(file_stamp(targetsfd, name) == before_stamp,
                        "TARGET_CHANGED_DURING_AUDIT")
                target_snapshots[name] = (before_stamp, d)
                rows = lines(d)
                require(len(rows) == 1 and len(rows[0]) == 6,
                        "TARGET_SCHEMA")
                require(rows[0][0] in account_ids, "TARGET_ACCOUNT_ORPHAN")
                number(rows[0][3])
                targets += 1
            require(len(set(names)) == len(names) and
                    set(os.listdir(targetsfd)) == set(names) and
                    directory_stamp(targetsfd) == start_targets_stamp,
                    "TARGET_CHANGED_DURING_AUDIT")
            for name, (stamp, contents) in target_snapshots.items():
                require(file_stamp(targetsfd, name) == stamp,
                        "TARGET_CHANGED_DURING_AUDIT")
                require(private_file(targetsfd, name) == contents and
                        file_stamp(targetsfd, name) == stamp,
                        "TARGET_CHANGED_DURING_AUDIT")
        finally:
            os.close(targetsfd)

        # Best-effort rereads detect common concurrent writer races.
        # Even if this succeeds, it CANNOT prove a quiesced point-in-time state.
        require(set(os.listdir(dirfd)) == root_entries and
                directory_stamp(dirfd) == start_root_stamp,
                "SOURCE_CHANGED_DURING_AUDIT")
        confirm_same_file(dirfd, MARKER, marker_stamp, MAGIC)
        for name in (*REQUIRED, *OPTIONAL):
            confirm_same_file(dirfd, name, stamps[name], data.get(name),
                              required=name in REQUIRED)
        require(set(os.listdir(dirfd)) == root_entries and
                directory_stamp(dirfd) == start_root_stamp,
                "SOURCE_CHANGED_DURING_AUDIT")

        return {
            "status": "SCHEMA_READABLE_UNQUIESCED",
            "fixture_only": True,
            "migration_authorized": False,
            "quiesced": False,
            "balances_verified_against_external_receipts": False,
            "accounts": len(accounts),
            "wifi_credit_cents": money_total(accounts, 1),
            "members": len(members),
            "member_banked_seconds": money_total(members, 7),
            "member_events": len(events),
            "member_revision": revision,
            "rental_devices": len(rentals),
            "rental_events": len(rental_events),
            "vouchers": len(vouchers),
            "controller_targets": targets,
            "legacy_credit_rows": legacy_count["credits.tsv"],
            "legacy_session_rows": legacy_count["sessions.tsv"],
        }
    finally:
        os.close(dirfd)


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic read-only v1 inventory; NEVER migration approval")
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    try:
        report = audit(Path(args.root))
        print(json.dumps(report, sort_keys=True))
        return 0
    except InvalidState as exc:
        print(json.dumps({
            "status": "BLOCKED",
            "reason_code": exc.code,
            "fixture_only": True,
            "migration_authorized": False,
            "quiesced": False
        }, sort_keys=True))
        return 4
    except OSError:
        print(json.dumps({"status": "BLOCKED", "reason_code": "READ_ERROR",
                          "fixture_only": True, "migration_authorized": False,
                          "quiesced": False}, sort_keys=True))
        return 4


if __name__ == "__main__":
    sys.exit(main())
