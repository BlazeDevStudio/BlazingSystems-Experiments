#!/usr/bin/env python3
"""WITNESS-0740: independent verifier for a real CLI candidate response.

Disposable /tmp synthetic key/SQLite only. No sockets, router installation,
customer data, hardware witness, ACKP1 or paid-authority promotion.
"""
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/v060_offdevice_witness_candidate.py"
REQ_DOMAIN = "BLAZE-WITNESS-CANDIDATE/1"
RESP_DOMAIN = "BLAZE-WITNESS-CANDIDATE-TRANSACTION-REPLY/1"
STATUS_DOMAIN = "BLAZE-WITNESS-CANDIDATE-STATUS/1"
DENIED = ("paid_ack_authorized", "independent_monotonic_witness_verified",
          "financial_migration_authorized", "customer_install_authorized")
A, B = "a" * 64, "b" * 64
CH1, CH2, CH3 = "1" * 32, "2" * 32, "3" * 32
NONCE = "c" * 32


def canonical(command, args):
    return (REQ_DOMAIN + "\t" + command + "\t" + "\t".join(args) + "\n").encode("ascii")


def verify_bound_response(result, command, args, key):
    """Use a separate verifier, NOT the witness candidate's implementation."""
    try:
        wire = dict(result)
        mac = wire.pop("response_mac")
        reqhash = hashlib.sha256(canonical(command, args)).hexdigest()
        assert wire["request_sha256"] == reqhash, "old/wrong request challenge"
        expected_domain = STATUS_DOMAIN if command == "status" else RESP_DOMAIN
        assert wire["schema"] == REQ_DOMAIN and wire["reply_schema"] == expected_domain
        if command == "status":
            assert wire.get("response_challenge") == args[1], "status replayed"
        assert isinstance(mac, str) and len(mac) == 64
        assert all(wire[k] is False for k in DENIED), "production admission forged"
        body = json.dumps(wire, sort_keys=True, separators=(",", ":")).encode("ascii")
        if command == "status":
            # Compatibility: existing merged WITNESS-0739 STATUS/1 contract.
            message = STATUS_DOMAIN.encode("ascii") + b"\n" + body + b"\n"
        else:
            message = (RESP_DOMAIN + "\t" + reqhash + "\t").encode("ascii") + body + b"\n"
        exp = hmac.new(key, message, hashlib.sha256).hexdigest()
        assert hmac.compare_digest(mac, exp), "response payload or key forged"
        return wire
    except (KeyError, AssertionError, TypeError, UnicodeEncodeError):
        return None


def main():
    with tempfile.TemporaryDirectory(prefix="blaze-witness0738-") as labname:
        os.umask(0o077)
        lab = Path(labname)
        key = secrets.token_bytes(32)
        (lab / ".witness-candidate-only").write_text(
            "BLAZE-WITNESS-CANDIDATE-NOT-HARDWARE-ATTESTED\n", encoding="ascii")
        (lab / "secret.hex").write_text(key.hex() + "\n", encoding="ascii")
        assert all((lab / n).stat().st_mode & 0o777 == 0o600
                   for n in (".witness-candidate-only", "secret.hex"))

        def call(command, *args):
            arguments = list(args)
            auth = hmac.new(key, canonical(command, arguments), hashlib.sha256).hexdigest()
            proc = subprocess.run([sys.executable, str(TOOL), labname, command,
                                   *arguments, auth], text=True, capture_output=True, check=False)
            assert proc.returncode == 0, (command, proc.returncode, proc.stderr)
            assert not proc.stderr, proc.stderr
            result = json.loads(proc.stdout)
            assert verify_bound_response(result, command, arguments, key) is not None, command
            return result

        genesis = call("init", "device01", "1", "1", A)
        assert genesis["state"] == "GENESIS_CANDIDATE_ONLY"
        initial = call("status", "device01", CH1)
        assert initial["state"] == "OBSERVED_CANDIDATE_ONLY"
        assert initial["pending_revision"] is None

        prepared = call("prepare", "device01", "1", "1", A, "2", B, NONCE)
        assert prepared["state"] == "PREPARED_NOT_COMMITTED"
        assert prepared["pending_reconciliation"] is True
        assert (prepared["pending_revision"], prepared["pending_digest"],
                prepared["pending_nonce"]) == (2, B, NONCE)
        pending = call("status", "device01", CH2)
        assert pending["state"] == "PENDING_RECONCILIATION"
        assert (pending["pending_revision"], pending["pending_digest"],
                pending["pending_nonce"]) == (2, B, NONCE)
        finalized = call("finalize", "device01", "1", "2", B, NONCE)
        assert finalized["state"] == "FINALIZED_CANDIDATE_NO_PAID_ACK"
        assert finalized["pending_revision"] is None
        replay = call("finalize", "device01", "1", "2", B, NONCE)
        assert replay["state"] == "ALREADY_FINALIZED_NO_PAID_ACK"
        observed = call("status", "device01", CH3)
        assert observed["witness_revision"] == 2 and observed["pending_revision"] is None

        # This is the original exploit surface: a successful JSON print used
        # to have no MAC or binding to a fresh challenge. Deny five variants.
        def bad(message, command, args, authkey=key):
            assert verify_bound_response(message, command, args, authkey) is None, (
                "unsafe witness response accepted", command, args)

        old_args = ["device01", CH2]
        bad(pending, "status", ["device01", CH3])  # signed old status replay
        bad(pending, "status", ["device02", CH2])  # another device
        bad(pending, "prepare", ["device01", "1", "1", A, "2", B, NONCE])
        tampered = dict(pending)
        tampered["witness_revision"] = 999
        bad(tampered, "status", old_args)
        tampered = dict(pending)
        tampered["paid_ack_authorized"] = True
        bad(tampered, "status", old_args)
        tampered = dict(pending)
        tampered["pending_digest"] = A
        bad(tampered, "status", old_args)
        tampered = dict(pending)
        tampered["response_mac"] = "0" * 64
        bad(tampered, "status", old_args)
        bad(pending, "status", old_args, secrets.token_bytes(32))
        # JSON injection/reordering cannot forge a new canonical HMAC.
        tampered = dict(pending)
        tampered["witness_epoch"] = 0
        bad(tampered, "status", old_args)
        assert verify_bound_response(pending, "status", old_args, key) is not None
        print("WITNESS-0740 PASS: authenticated genesis/prepare/status/finalize/replay responses,"
              " original request/challenge bound; tampering, old-nonce replay,"
              " cross-device, false ACK and wrong secret rejected")
        print("BLOCKED: this is only an off-device SQLite candidate; independent "
              "monotonic hardware, target fsync, protected P-256 signer, "
              "physical powercut, customer migration and v0.6 release NOT verified")


if __name__ == "__main__":
    main()
