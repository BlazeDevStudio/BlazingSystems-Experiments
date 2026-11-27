#!/usr/bin/env python3
"""WITNESS-0693: synthetic two-stage recovery MODEL ONLY, never deployed.

This experiment assumes an independently trustworthy, durable, nonrollbackable
witness that does NOT exist in the BlazePwifi runtime. No files/network,
hardware, cryptographic provisioning or customer storage are accessed.

A witness PREPARE is followed by a ledger commit, witness FINALIZE, then ACK.
During interruption all money writes freeze; owner-quiesced recovery can only
choose an exactly witnessed old or proposed new snapshot. This is a model of
failure policy, NOT a distributed transaction implementation or proof of fsync.
"""
from copy import deepcopy
from hashlib import sha256
import hmac
import unittest

from v060_trusted_witness_model import (
    LabPaymentAuthority, NoAck, Refused, canonical, digest,
    snapshot_manifest,
)


class TwoStageIndependentWitness:
    """Idealized outside-rollback-domain witness. NOT real hardware custody."""

    def __init__(self, ledger):
        self.online = True
        self._synthetic_key = b"WITNESS-0693-TEST-ONLY-NOT-AN-EXTERNAL-SERVICE"
        self._sealed = self._seal({
            "committed": snapshot_manifest(ledger), "pending": None
        })

    def _seal(self, state):
        signature = hmac.new(
            self._synthetic_key, canonical(state), sha256
        ).hexdigest()
        return {"state": deepcopy(state), "mac": signature}

    def _read(self):
        if not self.online:
            raise Refused("independent witness offline")
        state = self._sealed["state"]
        expected = self._seal(state)["mac"]
        if not hmac.compare_digest(self._sealed["mac"], expected):
            raise Refused("independent witness integrity failure")
        return deepcopy(state)

    def _save(self, state):
        if not self.online:
            raise Refused("independent witness offline")
        self._sealed = self._seal(state)

    def require_live(self, ledger):
        state = self._read()
        if state["pending"] is not None:
            raise Refused("outstanding prepared money operation: freeze")
        if state["committed"] != snapshot_manifest(ledger):
            raise Refused("stale/diverged ledger: freeze paid writes")
        return state

    def prepare(self, old_ledger, next_ledger, signed_envelope):
        state = self.require_live(old_ledger)
        old = state["committed"]
        new = snapshot_manifest(next_ledger)
        if new["device"] != old["device"] or new["epoch"] != old["epoch"]:
            raise Refused("foreign device/migration epoch")
        if new["revision"] != old["revision"] + 1:
            raise Refused("non-monotonic ledger revision")
        for key, floor in old["floors"].items():
            if new["floors"].get(key, -1) < floor:
                raise Refused("decreasing controller sequence floor")
        state["pending"] = {
            "before": old,
            "after": new,
            "envelope_sha256": digest(signed_envelope.payload()),
        }
        self._save(state)

    def finalize(self, ledger):
        state = self._read()
        pending = state["pending"]
        if pending is None:
            raise Refused("finalization without independently prepared event")
        if snapshot_manifest(ledger) != pending["after"]:
            raise Refused("cannot finalize unexpected ledger")
        state["committed"] = pending["after"]
        state["pending"] = None
        self._save(state)

    def recover(self, ledger, *, owner_quiesced=False):
        if not owner_quiesced:
            raise Refused("operator has not quiesced all paid writers")
        state = self._read()
        current = snapshot_manifest(ledger)
        pending = state["pending"]
        if pending is None:
            if current != state["committed"]:
                raise Refused("unknown ledger state: manual reconciliation")
            return "ALREADY_CONSISTENT"
        if state["committed"] != pending["before"]:
            raise Refused("corrupt witness prepared base")
        if current == pending["before"]:
            # No ACK was possible while the operation was PREPARED only.
            state["pending"] = None
            self._save(state)
            return "ABORTED_UNACKED"
        if current == pending["after"]:
            # Ledger contains the *exact* staged balance+receipt/floor bytes.
            state["committed"] = pending["after"]
            state["pending"] = None
            self._save(state)
            return "FINALIZED_UNACKED"
        raise Refused("neither prepared snapshot matches: freeze and investigate")


class TwoStageSyntheticProtocol:
    def __init__(self):
        self.authority = LabPaymentAuthority()
        self.witness = TwoStageIndependentWitness(self.authority.ledger)

    def sign(self, *args):
        return self.authority.sign(*args)

    def apply(self, tx, *, fault=None):
        if self.witness is None:
            raise Refused("independent witness missing")
        self.witness.require_live(self.authority.ledger)

        # The pre-existing WITNESS-0692 signed transaction oracle supplies a
        # proposed synthetic snapshot without mutating the original.
        candidate = deepcopy(self.authority)
        result = candidate.apply(tx)
        if result[0] == "REPLAY":
            return result
        if result[0] != "COMMIT":
            raise Refused("unexpected signed transaction result")
        if fault == "before-prepare":
            raise NoAck("nothing prepared or committed")
        self.witness.prepare(self.authority.ledger, candidate.ledger, tx)
        if fault == "after-prepare-before-ledger":
            raise NoAck("prepared witness; old ledger; no ACK")
        self.authority = candidate
        if fault == "after-ledger-before-finalize":
            raise NoAck("new ledger; prepared witness; no ACK")
        self.witness.finalize(self.authority.ledger)
        if fault == "after-finalize-before-ack":
            raise NoAck("durable witness assumed; ACK lost in transit")
        self.witness.require_live(self.authority.ledger)
        return result

    def recover(self, *, owner_quiesced=False):
        if self.witness is None:
            raise Refused("independent witness missing")
        return self.witness.recover(
            self.authority.ledger, owner_quiesced=owner_quiesced
        )


class TwoStageRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.x = TwoStageSyntheticProtocol()
        self.credit = self.x.sign("ctrlOne", 1, "AM", "alice", "-", 40)

    def test_normal_commit_and_original_result_replay(self):
        self.assertEqual(self.x.apply(self.credit), ("COMMIT", 140))
        self.assertEqual(self.x.apply(self.credit), ("REPLAY", 140))
        self.assertEqual(self.x.authority.ledger.members["alice"], 140)

    def test_before_prepare_has_no_credit(self):
        with self.assertRaises(NoAck):
            self.x.apply(self.credit, fault="before-prepare")
        self.assertEqual(self.x.authority.ledger.members["alice"], 100)
        self.assertEqual(self.x.recover(owner_quiesced=True), "ALREADY_CONSISTENT")
        self.assertEqual(self.x.apply(self.credit), ("COMMIT", 140))

    def test_prepared_old_ledger_can_abort_only_under_quiescence(self):
        with self.assertRaises(NoAck):
            self.x.apply(self.credit, fault="after-prepare-before-ledger")
        with self.assertRaises(Refused):
            self.x.apply(self.credit)
        with self.assertRaisesRegex(Refused, "quiesced"):
            self.x.recover()
        self.assertEqual(self.x.recover(owner_quiesced=True), "ABORTED_UNACKED")
        self.assertEqual(self.x.apply(self.credit), ("COMMIT", 140))

    def test_prepared_new_ledger_can_finalize_without_false_ack(self):
        with self.assertRaises(NoAck):
            self.x.apply(self.credit, fault="after-ledger-before-finalize")
        self.assertEqual(self.x.authority.ledger.members["alice"], 140)
        with self.assertRaisesRegex(Refused, "prepared"):
            self.x.apply(self.credit)
        self.assertEqual(self.x.recover(owner_quiesced=True), "FINALIZED_UNACKED")
        self.assertEqual(self.x.apply(self.credit), ("REPLAY", 140))

    def test_witness_finalized_ack_lost_replays_once(self):
        with self.assertRaises(NoAck):
            self.x.apply(self.credit, fault="after-finalize-before-ack")
        self.assertEqual(self.x.recover(owner_quiesced=True), "ALREADY_CONSISTENT")
        self.assertEqual(self.x.apply(self.credit), ("REPLAY", 140))
        self.assertEqual(self.x.authority.ledger.members["alice"], 140)

    def test_second_controller_rental_blocked_during_partial_commit(self):
        rental = self.x.sign("ctrlTwo", 1, "LR", "dev01", "-", 600)
        with self.assertRaises(NoAck):
            self.x.apply(self.credit, fault="after-ledger-before-finalize")
        with self.assertRaises(Refused):
            self.x.apply(rental)
        self.x.recover(owner_quiesced=True)
        self.assertEqual(self.x.apply(rental), ("COMMIT", 1600))
        self.assertEqual(self.x.apply(rental), ("REPLAY", 1600))
        self.assertEqual(self.x.authority.ledger.members["alice"], 140)

    def test_valid_but_older_ledger_rejected_after_new_ack(self):
        old = deepcopy(self.x.authority)
        self.x.apply(self.credit)
        self.x.authority = old
        with self.assertRaisesRegex(Refused, "stale/diverged"):
            self.x.apply(self.credit)
        with self.assertRaisesRegex(Refused, "unknown ledger"):
            self.x.recover(owner_quiesced=True)

    def test_unknown_ledger_during_prepare_never_autorepairs(self):
        with self.assertRaises(NoAck):
            self.x.apply(self.credit, fault="after-prepare-before-ledger")
        self.x.authority.ledger.members["alice"] = 999
        with self.assertRaisesRegex(Refused, "neither prepared"):
            self.x.recover(owner_quiesced=True)
        with self.assertRaises(Refused):
            self.x.apply(self.credit)

    def test_offline_witness_blocks_recovery_and_payment(self):
        with self.assertRaises(NoAck):
            self.x.apply(self.credit, fault="after-ledger-before-finalize")
        self.x.witness.online = False
        with self.assertRaisesRegex(Refused, "offline"):
            self.x.recover(owner_quiesced=True)
        with self.assertRaises(Refused):
            self.x.apply(self.credit)
        self.x.witness.online = True
        self.assertEqual(self.x.recover(owner_quiesced=True), "FINALIZED_UNACKED")

    def test_missing_witness_never_falls_back_to_local_snapshot(self):
        self.x.witness = None
        with self.assertRaisesRegex(Refused, "missing"):
            self.x.apply(self.credit)
        with self.assertRaisesRegex(Refused, "missing"):
            self.x.recover(owner_quiesced=True)

    def test_tampered_prepare_mac_denies_recovery(self):
        with self.assertRaises(NoAck):
            self.x.apply(self.credit, fault="after-prepare-before-ledger")
        self.x.witness._sealed["state"]["pending"]["envelope_sha256"] = "0" * 64
        with self.assertRaisesRegex(Refused, "integrity"):
            self.x.recover(owner_quiesced=True)
        with self.assertRaises(Refused):
            self.x.apply(self.credit)

    def test_foreign_epoch_cannot_be_prepared(self):
        self.x.authority.ledger.epoch = "fake-old-epoch"
        with self.assertRaisesRegex(Refused, "stale/diverged"):
            self.x.apply(self.credit)

    def test_real_transfer_conservation_in_synthetic_oracle(self):
        self.x.apply(self.credit)
        transfer = self.x.sign("ctrlOne", 2, "TM", "alice", "bob", 25)
        self.assertEqual(self.x.apply(transfer), ("COMMIT", 115))
        self.assertEqual(self.x.apply(transfer), ("REPLAY", 115))
        self.assertEqual(self.x.authority.ledger.members["alice"], 115)
        self.assertEqual(self.x.authority.ledger.members["bob"], 225)
        self.assertEqual(sum(self.x.authority.ledger.members.values()), 340)

    def test_changed_signed_payload_cannot_reuse_old_receipt(self):
        self.x.apply(self.credit)
        changed = self.x.sign("ctrlOne", 1, "AM", "alice", "-", 60)
        with self.assertRaisesRegex(Refused, "collision"):
            self.x.apply(changed)

    def test_restore_both_trusted_witness_and_ledger_is_unsafe_by_design(self):
        """EXPECTED UNSAFE LIMIT: a rollbackable witness is NOT independent."""
        old_authority = deepcopy(self.x.authority)
        old_witness = deepcopy(self.x.witness)
        self.x.apply(self.credit)
        self.x.authority = old_authority
        self.x.witness = old_witness
        # This is intentionally allowed by the idealized model. It proves that
        # saving a witness in the same backup as ledger gives NO protection.
        self.assertEqual(self.x.apply(self.credit), ("COMMIT", 140))
        self.assertEqual(self.x.authority.ledger.members["alice"], 140)


if __name__ == "__main__":
    print("WITNESS-0693 LAB ONLY: two-stage state recovery requires a REAL independent witness (NOT IMPLEMENTED)")
    print("UNSAFE LIMIT: joint rollback of ledger+witness defeats this model; v0.6 customer release remains BLOCKED")
    unittest.main(verbosity=2)
