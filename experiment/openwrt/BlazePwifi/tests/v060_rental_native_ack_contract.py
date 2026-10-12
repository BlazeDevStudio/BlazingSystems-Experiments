#!/usr/bin/env python3
"""RENT-0727 / #32: OFF-DEVICE authenticated rental lease/receipt/ACKV2 contract.

The actual C native HMAC journal fixture is compiled, not mocked. A distinct
locally pinned synthetic server-ACK key verifies committed/replayed responses.
NO OpenWrt rootfs executable, real money, production signer, P-256 ACKP1,
antirollback witness, historical v1 migration or physical flash acceptance.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
NATIVE_SOURCE = ROOT / "tools/v060_journal_authority_native.c"
RUNTIME_CGI = ROOT / "openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
KEY_A = bytes.fromhex("33" * 32)
KEY_B = bytes.fromhex("44" * 32)
ACK_A = bytes.fromhex("55" * 32)
ACK_B = bytes.fromhex("66" * 32)
ACK_OLD = bytes.fromhex("77" * 32)
ACK_ROTATED = bytes.fromhex("88" * 32)
AUTH_DOMAIN = "BLAZE-V2-AUTH-FIXTURE/1"
ACK_DOMAIN = "BLAZE-V2-SERVER-ACK-FIXTURE/1"


def private(path: Path, data: bytes) -> None:
    path.write_bytes(data)
    path.chmod(0o600)


def receipt_count(root: Path, ctl: str, sequence: int) -> int:
    rows = ledger_rows(root)
    return sum(row[0] == "R" and row[1] == ctl and row[2] == str(sequence)
               for row in rows)


def ledger_rows(root: Path) -> list[list[str]]:
    content = (root / "ledger.tsv").read_bytes()
    lines = content.splitlines(keepends=True)
    assert lines and lines[-1].startswith(b"H\t") and lines[-1].endswith(b"\n")
    body = b"".join(lines[:-1])
    assert lines[-1] == b"H\t" + hashlib.sha256(body).hexdigest().encode() + b"\n"
    return [line.decode("ascii").rstrip("\n").split("\t") for line in lines[:-1]]


def value(root: Path, kind: str, name: str) -> int:
    rows = [row for row in ledger_rows(root) if len(row) == 3 and
            row[0] == kind and row[1] == name]
    assert len(rows) == 1, (kind, name, rows)
    return int(rows[0][2])


def digest(root: Path) -> str:
    return hashlib.sha256((root / "ledger.tsv").read_bytes()).hexdigest()


def signed_call(binary: Path, root: Path, controller: str, sequence: int,
                op: str, subject: str, units: int, now: int = 1000,
                *, target: str = "-", fault: str = "",
                signature_override: str | None = None) -> subprocess.CompletedProcess:
    assert controller in ("ctrlOne", "ctrlTwo")
    event = f"{controller}:{sequence}"
    fields = [controller, str(sequence), event, op, subject, target,
              str(units), str(now)]
    command = (AUTH_DOMAIN + "\t" + "\t".join(fields) + "\n").encode("ascii")
    key = KEY_A if controller == "ctrlOne" else KEY_B
    sig = signature_override or hmac.new(key, command, hashlib.sha256).hexdigest()
    env = os.environ.copy()
    env.pop("BLAZE_V2_NATIVE_TEST_FAULT", None)
    if fault:
        env["BLAZE_V2_NATIVE_TEST_FAULT"] = fault
    return subprocess.run([str(binary), str(root), *fields, sig,
                           "--server-ack-v2"], capture_output=True,
                          text=True, timeout=12, env=env)


def verify_ack(output: str, controller: str, seq: int, op: str, subject: str,
               units: int, result: int, outcome: str, pinned_kid: str,
               pinned_key: bytes, now: int = 1000, target: str = "-") -> None:
    fields = output.rstrip("\n").split("\t")
    assert output.endswith("\n") and output.count("\n") == 1
    assert len(fields) == 8, fields
    tag, actual_outcome, actual_ctl, actual_seq, request_sha, actual_result, kid, mac = fields
    assert tag == "ACKV2" and actual_outcome == outcome
    assert actual_ctl == controller and actual_seq == str(seq)
    assert actual_result == str(result) and kid == pinned_kid
    assert len(mac) == 64 and mac == mac.lower()
    event = f"{controller}:{seq}"
    identity = (f"{controller}|{seq}|{event}|{op}|{subject}|{target}|"
                f"{units}|{now}|v2").encode("ascii")
    assert request_sha == hashlib.sha256(identity).hexdigest()
    # The command MAC and server receipt MAC have separate key identities
    # and domains; no key is downloaded from the same untrusted response.
    signed_message = (f"{ACK_DOMAIN}\t{kid}\t{controller}\t{seq}\t"
                      f"{request_sha}\t{result}\t{outcome}\n").encode("ascii")
    expected = hmac.new(pinned_key, signed_message, hashlib.sha256).hexdigest()
    assert hmac.compare_digest(expected, mac), "ACK signed by wrong/rotated key"


def denied(response: subprocess.CompletedProcess, before: str, root: Path) -> None:
    assert response.returncode != 0, f"false successful paid ACK: {response.stdout}"
    assert response.stdout == "", f"failed paid transaction emitted ACK: {response.stdout}"
    assert digest(root) == before, "rejected request mutated journal"


def run() -> None:
    assert not (ROOT / "openwrt/rootfs/usr/bin/v2-native-fixture").exists()
    assert not (ROOT / "openwrt/rootfs/usr/lib/blazepwifi/v060_journal_authority_native.c").exists()
    assert "rental_v2_*) bp_fail" in RUNTIME_CGI.read_text()
    with tempfile.TemporaryDirectory(prefix="blaze-v2-native-", dir="/tmp") as raw:
        top = Path(raw)
        top.chmod(0o700)
        binary = top / "native"
        compiled = subprocess.run(
            ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2",
             "-DBLAZE_FIXTURE_ONLY", str(NATIVE_SOURCE), "-lcrypto", "-o", str(binary)],
            capture_output=True, text=True, timeout=45)
        assert compiled.returncode == 0, compiled.stderr
        binary.chmod(0o700)
        private(top / ".blaze-v2-fixture-only", b"BLAZE-V2-SYNTHETIC-ONLY\n")
        private(top / "controller-keys.tsv",
                f"ctrlOne\t{KEY_A.hex()}\nctrlTwo\t{KEY_B.hex()}\n".encode())
        body = b"V\t2\nA\talice\t100\nL\tdev01\t0\nL\tdev02\t500\n"
        private(top / "ledger.tsv", body + b"H\t" +
                hashlib.sha256(body).hexdigest().encode() + b"\n")

        def ack_registry(rotated: bool = False) -> None:
            if rotated:
                lines = (f"serverOne\tctrlOne\trevoked\t{ACK_A.hex()}\n"
                         f"serverRotated\tctrlOne\tactive\t{ACK_ROTATED.hex()}\n"
                         f"serverTwo\tctrlTwo\tactive\t{ACK_B.hex()}\n")
            else:
                lines = (f"serverOne\tctrlOne\tactive\t{ACK_A.hex()}\n"
                         f"serverOld\tctrlOne\trevoked\t{ACK_OLD.hex()}\n"
                         f"serverTwo\tctrlTwo\tactive\t{ACK_B.hex()}\n")
            private(top / "server-ack-keys.tsv", lines.encode())

        original = digest(top)
        # Without a pre-provisioned independent ACK signer, never commit money.
        denied(signed_call(binary, top, "ctrlOne", 1, "LR", "dev01", 600),
               original, top)
        ack_registry()
        first = signed_call(binary, top, "ctrlOne", 1, "LR", "dev01", 600)
        assert first.returncode == 0, first.stderr
        verify_ack(first.stdout, "ctrlOne", 1, "LR", "dev01", 600,
                   1600, "COMMIT", "serverOne", ACK_A)
        assert value(top, "L", "dev01") == 1600
        assert value(top, "C", "ctrlOne") == 1 and receipt_count(top, "ctrlOne", 1) == 1
        committed = digest(top)
        replay = signed_call(binary, top, "ctrlOne", 1, "LR", "dev01", 600)
        assert replay.returncode == 0, replay.stderr
        verify_ack(replay.stdout, "ctrlOne", 1, "LR", "dev01", 600,
                   1600, "REPLAY", "serverOne", ACK_A)
        assert digest(top) == committed

        # Client rejects tampering even though its controller HMAC was valid.
        for tampered in (replay.stdout.replace("\t1600\t", "\t1601\t"),
                         replay.stdout.replace("\tREPLAY\t", "\tCOMMIT\t"),
                         replay.stdout.replace("\tserverOne\t", "\tserverTwo\t"),
                         replay.stdout.replace("\tctrlOne\t", "\tctrlTwo\t")):
            try:
                verify_ack(tampered, "ctrlOne", 1, "LR", "dev01", 600,
                           1600, "REPLAY", "serverOne", ACK_A)
            except AssertionError:
                pass
            else:
                raise AssertionError("modified rental ACK accepted by pinned verifier")

        # Same controller+sequence cannot be reused for changed lease, target
        # or time; skipped sequence and cross-key forgery have no ACK.
        for request in (
            ("ctrlOne", 1, "LR", "dev01", 601),
            ("ctrlOne", 1, "LR", "dev02", 600),
            ("ctrlOne", 3, "LR", "dev01", 200),
        ):
            denied(signed_call(binary, top, *request), committed, top)
        denied(signed_call(binary, top, "ctrlOne", 2, "LR", "dev01", 100,
                           signature_override="0" * 64), committed, top)
        denied(signed_call(binary, top, "ctrlOne", 2, "LR", "missing", 100),
               committed, top)

        # Key registry mutations fail closed BEFORE money, not after.
        valid_registry = (top / "server-ack-keys.tsv").read_bytes()
        for records in (
            f"serverOne\tctrlOne\trevoked\t{ACK_A.hex()}\n"
            f"serverTwo\tctrlTwo\tactive\t{ACK_B.hex()}\n",
            f"serverOne\tctrlOne\tactive\t{ACK_A.hex()}\n"
            f"serverDup\tctrlOne\tactive\t{ACK_OLD.hex()}\n",
            f"serverOne\tctrlOne\tactive\t{KEY_A.hex()}\n"
            f"serverTwo\tctrlTwo\tactive\t{ACK_B.hex()}\n",
        ):
            private(top / "server-ack-keys.tsv", records.encode())
            denied(signed_call(binary, top, "ctrlOne", 2, "LR", "dev01", 100),
                   committed, top)
        private(top / "server-ack-keys.tsv", valid_registry)

        for fault in ("before-source-fsync", "before-rename"):
            denied(signed_call(binary, top, "ctrlOne", 2, "LR", "dev01",
                               100, fault=fault), committed, top)
        uncertain = signed_call(binary, top, "ctrlOne", 2, "LR", "dev01",
                                100, fault="after-rename-before-dir-fsync")
        assert uncertain.returncode != 0 and uncertain.stdout == ""
        assert "UNCERTAIN" in uncertain.stderr
        assert value(top, "L", "dev01") == 1700
        assert receipt_count(top, "ctrlOne", 2) == 1
        after_uncertain = digest(top)
        retransmit = signed_call(binary, top, "ctrlOne", 2, "LR", "dev01", 100)
        assert retransmit.returncode == 0, retransmit.stderr
        verify_ack(retransmit.stdout, "ctrlOne", 2, "LR", "dev01", 100,
                   1700, "REPLAY", "serverOne", ACK_A)
        assert digest(top) == after_uncertain

        # A second controller has an independent key+sequence floor but
        # shares the one authoritative lease+receipt transaction boundary.
        second = signed_call(binary, top, "ctrlTwo", 1, "LR", "dev01", 200)
        assert second.returncode == 0, second.stderr
        verify_ack(second.stdout, "ctrlTwo", 1, "LR", "dev01", 200,
                   1900, "COMMIT", "serverTwo", ACK_B)
        assert value(top, "L", "dev01") == 1900
        assert value(top, "C", "ctrlOne") == 2 and value(top, "C", "ctrlTwo") == 1
        multi_digest = digest(top)
        historical = signed_call(binary, top, "ctrlOne", 2, "LR", "dev01", 100)
        verify_ack(historical.stdout, "ctrlOne", 2, "LR", "dev01", 100,
                   1700, "REPLAY", "serverOne", ACK_A)
        assert digest(top) == multi_digest
        denied(signed_call(binary, top, "ctrlTwo", 1, "LR", "dev01", 201),
               multi_digest, top)

        # Rotating a server ACK signer while an old paid receipt is pending
        # is NOT accepted by a client pinned to the original key and ID.
        ack_registry(rotated=True)
        rotated = signed_call(binary, top, "ctrlOne", 2, "LR", "dev01", 100)
        assert rotated.returncode == 0 and digest(top) == multi_digest
        try:
            verify_ack(rotated.stdout, "ctrlOne", 2, "LR", "dev01", 100,
                       1700, "REPLAY", "serverOne", ACK_A)
        except AssertionError:
            pass
        else:
            raise AssertionError("unprovisioned key rotation accepted")
        private(top / "server-ack-keys.tsv", valid_registry)

        # A fully fsync-committed transaction can still lose its ACK; retry
        # must return the ORIGINAL committed lease (no double-credit).
        lost = signed_call(binary, top, "ctrlTwo", 2, "LR", "dev02",
                           300, fault="after-dir-fsync-before-ack")
        assert lost.returncode != 0 and lost.stdout == ""
        assert value(top, "L", "dev02") == 1300
        retry = signed_call(binary, top, "ctrlTwo", 2, "LR", "dev02", 300)
        assert retry.returncode == 0, retry.stderr
        verify_ack(retry.stdout, "ctrlTwo", 2, "LR", "dev02", 300,
                   1300, "REPLAY", "serverTwo", ACK_B)
        assert value(top, "L", "dev02") == 1300
        assert receipt_count(top, "ctrlTwo", 2) == 1
        assert len([x for x in ledger_rows(top) if x[0] == "R"]) == 4
        # Never confuse the legacy/symmetric fixture with public P-256 ACKP1.
        assert not any(x.startswith("ACKP1") for x in
                       (first.stdout, replay.stdout, retransmit.stdout, retry.stdout))
        print("RENT-0727 PASS: native rental HMAC sequence -> fsynced lease+receipt "
              "-> independently pinned synthetic ACKV2; replay, collision, "
              "lost ACK, registry and cross-controller checks")
        print("LAB ONLY: NOT publicly verifiable ACKP1, independent antirollback, "
              "physical target powercut, customer v1 migration or rental v2 CGI")


if __name__ == "__main__":
    run()
