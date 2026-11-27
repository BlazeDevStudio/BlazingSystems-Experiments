#!/usr/bin/env python3
"""WITNESS-0692: OFF-DEVICE, IN-MEMORY PROTOCOL MODEL. NOT A PAYMENT SERVICE.

ROLLBACK-0691 demonstrated that restoring a checksum-valid older ledger can
erase ACKed member/rental credits and controller deduplication floors.

This fixture assumes a hypothetical independent, authenticated, non-rollbackable
witness whose storage is NOT part of the ledger backup. No such trusted witness
has been implemented for a real OpenWrt target. Python objects and HMAC here
model protocol invariants, NOT filesystem durability or physical power cuts.

Only fictional balances/keys. No file I/O, network I/O, runtime integration,
rootfs installation, actual signers, customer data, or release authorization.
"""
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import hmac
import json
import unittest


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value):
    return sha256(canonical(value)).hexdigest()


class Refused(Exception):
    """Never accept a payment or replay if trusted state does not agree."""


class NoAck(Exception):
    """Injected interruption: no successful payment response was delivered."""


@dataclass
class Ledger:
    device: str = "fictional-node-a"
    epoch: str = "synthetic-epoch-1"
    revision: int = 0
    members: dict = field(default_factory=lambda: {"alice": 100, "bob": 200})
    leases: dict = field(default_factory=lambda: {"dev01": 0})
    floors: dict = field(default_factory=dict)
    receipts: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Transaction:
    controller: str
    seq: int
    operation: str
    source: str
    destination: str
    seconds: int
    signature: str

    def payload(self):
        return [self.controller, self.seq, self.operation, self.source,
                self.destination, self.seconds]


def snapshot_manifest(ledger):
    return {
        "device": ledger.device,
        "epoch": ledger.epoch,
        "revision": ledger.revision,
        "snapshot_sha256": digest(asdict(ledger)),
        "floors": deepcopy(ledger.floors),
    }


class HypotheticalIndependentWitness:
    """Deliberately NOT a file in the same backup domain as the ledger."""

    def __init__(self, first_snapshot):
        self._synthetic_key = b"WITNESS-0692-LAB-ONLY-NOT-A-REAL-SECRET"
        self.online = True
        self._record = self._seal(snapshot_manifest(first_snapshot))

    def _seal(self, manifest):
        tag = hmac.new(self._synthetic_key, canonical(manifest), sha256).hexdigest()
        return {"manifest": deepcopy(manifest), "mac": tag}

    def _read(self):
        if not self.online:
            raise Refused("independent witness absent or unreachable")
        manifest = self._record["manifest"]
        expected = self._seal(manifest)["mac"]
        if not hmac.compare_digest(expected, self._record["mac"]):
            raise Refused("independent witness integrity mismatch")
        return deepcopy(manifest)

    def verify(self, snapshot):
        trusted = self._read()
        if trusted != snapshot_manifest(snapshot):
            raise Refused("STALE, diverged or foreign snapshot: freeze paid writes")
        return trusted

    def advance(self, previous_revision, next_snapshot):
        trusted = self._read()
        proposed = snapshot_manifest(next_snapshot)
        if proposed["device"] != trusted["device"] or (
            proposed["epoch"] != trusted["epoch"]
        ):
            raise Refused("foreign device or migration epoch")
        if trusted["revision"] != previous_revision or (
            proposed["revision"] != previous_revision + 1
        ):
            raise Refused("witness revision compare-and-advance mismatch")
        if any(proposed["floors"].get(k, -1) < old for k, old in
               trusted["floors"].items()):
            raise Refused("controller high-water rollback")
        self._record = self._seal(proposed)


class LabPaymentAuthority:
    def __init__(self, *, device="fictional-node-a", epoch="synthetic-epoch-1"):
        self.ledger = Ledger(device=device, epoch=epoch)
        self.witness = HypotheticalIndependentWitness(self.ledger)
        self.keys = {"ctrlOne": b"3" * 32, "ctrlTwo": b"4" * 32}

    def sign(self, controller, seq, operation, source, destination, seconds):
        if controller not in self.keys:
            raise Refused("unknown controller")
        payload = [controller, seq, operation, source, destination, seconds]
        sig = hmac.new(self.keys[controller], canonical(payload), sha256).hexdigest()
        return Transaction(*payload, sig)

    def require_fresh(self):
        if self.witness is None:
            raise Refused("independent witness missing")
        self.witness.verify(self.ledger)

    def apply(self, tx, *, cut=None, now=1000):
        self.require_fresh()
        if tx.controller not in self.keys:
            raise Refused("unknown controller")
        expected = hmac.new(self.keys[tx.controller], canonical(tx.payload()),
                            sha256).hexdigest()
        if not hmac.compare_digest(expected, tx.signature):
            raise Refused("unauthenticated synthetic envelope")
        if type(tx.seq) is not int or tx.seq < 1 or (
            type(tx.seconds) is not int or tx.seconds < 1 or
            tx.seconds > 31536000
        ):
            raise Refused("bad sequence or units")

        key = f"{tx.controller}:{tx.seq}"
        fingerprint = digest(tx.payload())
        old = self.ledger
        if key in old.receipts:
            prior = old.receipts[key]
            if prior["fingerprint"] != fingerprint:
                raise Refused("controller/sequence collision")
            return ("REPLAY", prior["result"])
        if tx.seq != old.floors.get(tx.controller, 0) + 1:
            raise Refused("stale or out-of-order signed sequence")

        nxt = deepcopy(old)
        if tx.operation == "AM" and tx.destination == "-":
            if tx.source not in nxt.members:
                raise Refused("unknown account")
            nxt.members[tx.source] += tx.seconds
            result = nxt.members[tx.source]
        elif tx.operation == "TM" and tx.source != tx.destination:
            if tx.source not in nxt.members or (
                tx.destination not in nxt.members
            ) or nxt.members[tx.source] < tx.seconds:
                raise Refused("invalid transfer")
            nxt.members[tx.source] -= tx.seconds
            nxt.members[tx.destination] += tx.seconds
            result = nxt.members[tx.source]
        elif tx.operation == "LR" and tx.destination == "-":
            if tx.source not in nxt.leases:
                raise Refused("unknown rental device")
            nxt.leases[tx.source] = max(nxt.leases[tx.source], now) + tx.seconds
            result = nxt.leases[tx.source]
        else:
            raise Refused("unsupported/mismatched operation")
        if result > 2000000000:
            raise Refused("prepaid overflow")
        nxt.floors[tx.controller] = tx.seq
        nxt.receipts[key] = {"fingerprint": fingerprint, "result": result}
        nxt.revision += 1

        # Simulation: never issue a successful ACK before BOTH logical sides
        # have reached the same revision and digest. No real fsync is modeled.
        if cut == "before-ledger":
            raise NoAck("interrupted before model ledger replace")
        self.ledger = nxt
        if cut == "after-ledger-before-witness":
            raise NoAck("ledger ahead; trusted witness still old: quarantine")
        if cut == "witness-offline-after-ledger":
            self.witness.online = False
        self.witness.advance(old.revision, nxt)
        if cut == "after-witness-before-ack":
            raise NoAck("witness and ledger agree but ACK was lost")
        self.require_fresh()
        return ("COMMIT", result)


class WitnessModelTests(unittest.TestCase):
    def setUp(self):
        self.a = LabPaymentAuthority()
        self.one = self.a.sign("ctrlOne", 1, "AM", "alice", "-", 40)

    def test_commit_and_exact_replay(self):
        self.assertEqual(self.a.apply(self.one), ("COMMIT", 140))
        self.assertEqual(self.a.apply(self.one), ("REPLAY", 140))
        self.assertEqual(self.a.ledger.members["alice"], 140)

    def test_old_checksum_valid_snapshot_cannot_reenter_paid_state(self):
        self.a.apply(self.one)
        old = deepcopy(self.a.ledger)
        old_checksum = digest(asdict(old))
        a2 = self.a.sign("ctrlOne", 2, "AM", "alice", "-", 30)
        rental = self.a.sign("ctrlTwo", 1, "LR", "dev01", "-", 600)
        self.a.apply(a2)
        self.a.apply(rental)
        self.a.ledger = old
        self.assertEqual(digest(asdict(self.a.ledger)), old_checksum)
        for request in (a2, rental, self.one):
            with self.subTest(request=request):
                with self.assertRaisesRegex(Refused, "STALE"):
                    self.a.apply(request)
        self.assertEqual(self.a.ledger.members["alice"], 140)

    def test_after_ledger_before_witness_quarantines_all_payments(self):
        with self.assertRaises(NoAck):
            self.a.apply(self.one, cut="after-ledger-before-witness")
        self.assertEqual(self.a.ledger.members["alice"], 140)
        with self.assertRaises(Refused):
            self.a.apply(self.one)
        with self.assertRaises(Refused):
            self.a.apply(self.a.sign("ctrlTwo", 1, "LR", "dev01", "-", 600))

    def test_no_ack_before_ledger_does_not_commit(self):
        with self.assertRaises(NoAck):
            self.a.apply(self.one, cut="before-ledger")
        self.a.require_fresh()
        self.assertEqual(self.a.ledger.members["alice"], 100)
        self.assertEqual(self.a.apply(self.one), ("COMMIT", 140))

    def test_after_witness_before_ack_retries_without_double_credit(self):
        with self.assertRaises(NoAck):
            self.a.apply(self.one, cut="after-witness-before-ack")
        self.a.require_fresh()
        self.assertEqual(self.a.apply(self.one), ("REPLAY", 140))
        self.assertEqual(self.a.ledger.members["alice"], 140)

    def test_missing_external_witness_denies_all_paid_writes(self):
        self.a.witness = None
        with self.assertRaises(Refused):
            self.a.apply(self.one)

    def test_offline_external_witness_denies_even_replay(self):
        self.a.apply(self.one)
        self.a.witness.online = False
        with self.assertRaises(Refused):
            self.a.apply(self.one)

    def test_corrupt_witness_manifest_denies_writes(self):
        self.a.witness._record["manifest"]["revision"] = 100
        with self.assertRaisesRegex(Refused, "integrity mismatch"):
            self.a.apply(self.one)

    def test_same_revision_tampered_balance_denied(self):
        self.a.ledger.members["alice"] = 900
        with self.assertRaisesRegex(Refused, "STALE"):
            self.a.apply(self.one)

    def test_same_revision_reset_controller_floor_denied(self):
        self.a.apply(self.one)
        self.a.ledger.floors["ctrlOne"] = 0
        with self.assertRaisesRegex(Refused, "STALE"):
            self.a.apply(self.one)

    def test_foreign_device_snapshot_denied(self):
        other = LabPaymentAuthority(device="fictional-node-b")
        self.a.ledger = deepcopy(other.ledger)
        with self.assertRaisesRegex(Refused, "STALE"):
            self.a.apply(self.one)

    def test_foreign_migration_epoch_denied(self):
        self.a.ledger.epoch = "synthetic-epoch-0"
        with self.assertRaisesRegex(Refused, "STALE"):
            self.a.apply(self.one)

    def test_witness_ahead_of_old_snapshot_denied(self):
        newer = deepcopy(self.a.ledger)
        newer.revision = 1
        newer.members["alice"] = 140
        newer.floors["ctrlOne"] = 1
        newer.receipts["ctrlOne:1"] = {
            "fingerprint": digest(self.one.payload()), "result": 140
        }
        self.a.witness.advance(0, newer)
        with self.assertRaisesRegex(Refused, "STALE"):
            self.a.apply(self.one)

    def test_missing_witness_after_ledger_write_quarantines(self):
        with self.assertRaises(Refused):
            self.a.apply(self.one, cut="witness-offline-after-ledger")
        self.a.witness.online = True
        with self.assertRaisesRegex(Refused, "STALE"):
            self.a.apply(self.one)

    def test_signature_tamper_and_payload_collision_rejected(self):
        tampered = Transaction("ctrlOne", 1, "AM", "alice", "-", 60,
                               self.one.signature)
        with self.assertRaisesRegex(Refused, "unauthenticated"):
            self.a.apply(tampered)
        self.a.apply(self.one)
        changed = self.a.sign("ctrlOne", 1, "AM", "alice", "-", 60)
        with self.assertRaisesRegex(Refused, "collision"):
            self.a.apply(changed)

    def test_out_of_order_and_expired_seq_denied(self):
        later = self.a.sign("ctrlOne", 2, "AM", "alice", "-", 40)
        with self.assertRaisesRegex(Refused, "out-of-order"):
            self.a.apply(later)
        self.a.apply(self.one)
        self.a.apply(later)
        stale = self.a.sign("ctrlOne", 1, "AM", "alice", "-", 99)
        with self.assertRaises(Refused):
            self.a.apply(stale)

    def test_transfer_and_rental_preserve_business_invariants(self):
        self.a.apply(self.one)
        transfer = self.a.sign("ctrlOne", 2, "TM", "alice", "bob", 25)
        rental = self.a.sign("ctrlTwo", 1, "LR", "dev01", "-", 600)
        self.assertEqual(self.a.apply(transfer), ("COMMIT", 115))
        self.assertEqual(self.a.apply(rental), ("COMMIT", 1600))
        self.assertEqual(sum(self.a.ledger.members.values()), 340)
        self.assertEqual(self.a.apply(transfer), ("REPLAY", 115))
        self.assertEqual(self.a.apply(rental), ("REPLAY", 1600))
        self.a.require_fresh()


if __name__ == "__main__":
    print("WITNESS-0692 LAB MODEL ONLY: assumes an external trusted witness; NOT a deployed OpenWrt safeguard")
    unittest.main(verbosity=2)
