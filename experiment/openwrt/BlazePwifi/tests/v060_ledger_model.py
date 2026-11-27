#!/usr/bin/env python3
"""MIG-0620: offline synthetic transaction oracle ONLY, NOT OpenWrt runtime.
Uses a temporary sqlite database to describe expected journal behavior; it
does NOT implement or validate BusyBox storage, fsync, signer or v1 migration.
No external paths, secrets, devices or real balance records are accepted.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path

WINDOW = 8


class Rejected(Exception):
    pass


class InjectedFailure(Exception):
    pass


class AckLost(Exception):
    pass


class SyntheticLedger:
    def __init__(self, filename):
        self.db = sqlite3.connect(filename, timeout=10, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=DELETE")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS accounts(
                name TEXT PRIMARY KEY, seconds INTEGER NOT NULL CHECK(seconds>=0));
            CREATE TABLE IF NOT EXISTS controllers(
                controller TEXT PRIMARY KEY, highwater INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS receipts(
                controller TEXT NOT NULL, seq INTEGER NOT NULL,
                event_id TEXT NOT NULL UNIQUE, digest TEXT NOT NULL,
                result TEXT NOT NULL, PRIMARY KEY(controller,seq));
        """)

    def close(self):
        self.db.close()

    def seed_fixture(self):
        assert not self.db.execute("SELECT 1 FROM accounts").fetchone()
        self.db.executemany("INSERT INTO accounts VALUES(?,?)",
                            [("alice", 100), ("bob", 200)])

    def balances(self):
        return dict(self.db.execute("SELECT name,seconds FROM accounts"))

    def apply(self, controller, seq, event_id, action, source, target, seconds,
              fail_at=None):
        assert controller and event_id and isinstance(seq, int) and seq > 0
        assert isinstance(seconds, int) and 0 <= seconds <= 31536000
        assert action in ("add", "subtract", "transfer")
        assert action != "transfer" or (target and target != source)
        data = [controller, seq, event_id, action, source, target, seconds]
        digest = hashlib.sha256(json.dumps(data, separators=(",", ":")).encode()).hexdigest()
        c = self.db
        c.execute("BEGIN IMMEDIATE")
        try:
            prior = c.execute(
                "SELECT digest,result FROM receipts WHERE controller=? AND seq=?",
                (controller, seq)).fetchone()
            if prior:
                if prior[0] != digest:
                    raise Rejected("collision: same controller/seq changed payload")
                c.execute("COMMIT")
                return ("replay", json.loads(prior[1]))
            row = c.execute("SELECT highwater FROM controllers WHERE controller=?",
                            (controller,)).fetchone()
            highwater = row[0] if row else 0
            if seq <= highwater:
                raise Rejected("stale: previously accepted sequence outside receipt window")
            if seq != highwater + 1:
                raise Rejected("out-of-order: missing authenticated prior sequence")
            own = c.execute("SELECT seconds FROM accounts WHERE name=?",
                            (source,)).fetchone()
            if own is None:
                raise Rejected("unknown source account")
            if action == "transfer":
                other = c.execute("SELECT seconds FROM accounts WHERE name=?",
                                  (target,)).fetchone()
                if other is None or own[0] < seconds:
                    raise Rejected("invalid transfer")
                c.execute("UPDATE accounts SET seconds=? WHERE name=?",
                          (own[0] - seconds, source))
                c.execute("UPDATE accounts SET seconds=? WHERE name=?",
                          (other[0] + seconds, target))
            elif action == "subtract":
                if own[0] < seconds:
                    raise Rejected("insufficient funds")
                c.execute("UPDATE accounts SET seconds=? WHERE name=?",
                          (own[0] - seconds, source))
            else:
                c.execute("UPDATE accounts SET seconds=? WHERE name=?",
                          (own[0] + seconds, source))
            if fail_at == "after_money_before_receipt":
                raise InjectedFailure("synthetic event receipt write/EIO")
            result = self.balances()
            c.execute("INSERT INTO receipts VALUES(?,?,?,?,?)",
                      (controller, seq, event_id, digest, json.dumps(result, sort_keys=True)))
            if row:
                c.execute("UPDATE controllers SET highwater=? WHERE controller=?",
                          (seq, controller))
            else:
                c.execute("INSERT INTO controllers VALUES(?,?)", (controller, seq))
            # Keep a small receipt window, but remember the highest accepted
            # sequence. Old repeats are REJECTED, never interpreted as new.
            c.execute("DELETE FROM receipts WHERE controller=? AND seq<=?",
                      (controller, seq - WINDOW))
            if fail_at == "before_commit":
                raise InjectedFailure("synthetic crash before durable commit")
            c.execute("COMMIT")
        except BaseException:
            if c.in_transaction:
                c.execute("ROLLBACK")
            raise
        if fail_at == "after_commit_before_ack":
            raise AckLost("synthetic lost response: money and receipt committed")
        return ("committed", result)

    def receipt_count(self, controller):
        return self.db.execute("SELECT count(*) FROM receipts WHERE controller=?",
                               (controller,)).fetchone()[0]


def expect(exception_type, fn):
    try:
        fn()
    except exception_type:
        return
    raise AssertionError("required failure not observed: " + exception_type.__name__)


def test_oracle():
    # This model intentionally refuses to open a user-provided or device path.
    with tempfile.TemporaryDirectory(prefix="blaze-synthetic-ledger-") as temp:
        location = str(Path(temp) / "test-only.db")
        a = SyntheticLedger(location)
        a.seed_fixture()
        assert a.apply("controller1", 1, "unique-bank1", "add", "alice", "", 40)[0] == "committed"
        assert a.balances() == {"alice": 140, "bob": 200}
        assert a.apply("controller1", 1, "unique-bank1", "add", "alice", "", 40)[0] == "replay"
        assert a.balances()["alice"] == 140
        expect(Rejected, lambda: a.apply("controller1", 1, "unique-bank1", "add", "bob", "", 40))
        expect(Rejected, lambda: a.apply("controller1", 3, "seq-gap", "add", "alice", "", 40))
        # Interruption AFTER debit/before receipt must roll back both parties.
        expect(InjectedFailure, lambda: a.apply("controller1", 2, "tx2", "transfer",
                                               "alice", "bob", 50, "after_money_before_receipt"))
        assert a.balances() == {"alice": 140, "bob": 200}
        # Committed transfer with lost ACK must survive reopen/retry unchanged.
        expect(AckLost, lambda: a.apply("controller1", 2, "tx2", "transfer",
                                       "alice", "bob", 50, "after_commit_before_ack"))
        a.close()
        a = SyntheticLedger(location)
        assert a.balances() == {"alice": 90, "bob": 250}
        assert a.apply("controller1", 2, "tx2", "transfer", "alice", "bob", 50)[0] == "replay"
        assert a.balances()["alice"] + a.balances()["bob"] == 340
        # Explicit storage/receipt failure cannot return success or mutate.
        expect(InjectedFailure, lambda: a.apply("controller1", 3, "tx3", "add",
                                                "alice", "", 30, "after_money_before_receipt"))
        assert a.balances() == {"alice": 90, "bob": 250}
        expect(InjectedFailure, lambda: a.apply("controller1", 3, "tx3", "add",
                                                "alice", "", 30, "before_commit"))
        assert a.balances() == {"alice": 90, "bob": 250}
        assert a.apply("controller1", 3, "tx3", "add", "alice", "", 30)[0] == "committed"
        assert a.balances()["alice"] == 120
        # Reused event ID by another controller is rejected while retained.
        expect(sqlite3.IntegrityError, lambda: a.apply("controller2", 1, "tx3",
                                                      "add", "bob", "", 10))
        assert a.balances()["bob"] == 250
        # Rotation must never make old sequences newly creditable.
        for seq in range(4, 22):
            a.apply("controller1", seq, f"fresh-{seq}", "add", "alice", "", 1)
        assert a.receipt_count("controller1") <= WINDOW
        before = a.balances()
        expect(Rejected, lambda: a.apply("controller1", 1, "unique-bank1",
                                         "add", "alice", "", 40))
        assert a.balances() == before
        # Two independent writers submit identical authenticated sequence.
        # SQLite serializes them, yielding exactly one commit and one replay.
        before_concurrent = a.balances()
        def simultaneous_retry(_):
            second = SyntheticLedger(location)
            try:
                return second.apply("controller1", 22, "fresh-22",
                                    "add", "alice", "", 9)[0]
            finally:
                second.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(simultaneous_retry, range(2)))
        assert sorted(outcomes) == ["committed", "replay"], outcomes
        assert a.balances()["alice"] == before_concurrent["alice"] + 9
        assert a.receipt_count("controller1") <= WINDOW
        a.close()
    print("MIG-0620 synthetic ledger MODEL PASS: atomic money+receipt, ACK replay, "
          "storage rollback, bounded stale rejection, collisions, concurrent duplicate serialization and transfer invariance")
    print("NOT PRODUCTION: no BusyBox implementation, physical fsync, v1 migration or signer QA")


if __name__ == "__main__":
    test_oracle()
