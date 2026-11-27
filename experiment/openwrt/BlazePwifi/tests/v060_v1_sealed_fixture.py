#!/usr/bin/env python3
"""EBACK-0677: synthetic sealed financial backup/restore negative regressions.

All contents are fake under /tmp/blaze-v1-audit-* and /tmp/blaze-v1-seal-*.
Never connects to /etc, OpenWrt, an account, or payment/lease authority.
"""
import errno
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "tools/v060_v1_sealed_fixture.py"
FAKE_SECRET = "PRIVATE-SYNTHETIC-BACKUP-DO-NOT-PRINT"
FAKE_ACCOUNT = "a" * 32
FAKE_DEVICE = "b" * 32
OUTPUTS = []

def put(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8")
    path.chmod(0o600)

def make_fixture(root: Path) -> None:
    put(root / ".blaze-v1-fixture-only", "BLAZE-V1-SYNTHETIC-INVENTORY-ONLY\n")
    put(root / "accounts.tsv", f"{FAKE_ACCOUNT}\t100\t0\t0\t0\t0\taa:bb:cc:dd:ee:ff\t10.0.0.2\tc:synthetic\n")
    put(root / "members.tsv", f"alice\tSynthetic\t1\tsha256i\tsalt\t{FAKE_SECRET}\t4096\t300\t2\t1000\tfixture\n"
                              "bob\tSynthetic\t1\tsha256i\tsalt\thash\t4096\t50\t1\t1000\tfixture\n")
    put(root / "member-events.tsv", "evt-a\t1000\talice\tadd\t120\t300\tsofttimer:test\t300\n")
    put(root / "member-revision", "2\n")
    put(root / "rental-devices.tsv", f"{FAKE_DEVICE}\t{FAKE_SECRET}\t1700001000\tSynthetic\t1000\n")
    put(root / "rental-events.tsv", f"r:synthetic\t{FAKE_DEVICE}\t1700001000\t1000\n")
    put(root / "vouchers.tsv", "TRUSTED-FAKE-CODE\t100\n")
    (root / "targets").mkdir(mode=0o700)
    put(root / "targets" / "vendo-01.tsv",
        f"{FAKE_ACCOUNT}\taa:bb:cc:dd:ee:ff\t1122334455667788\t1700001200\tvendo-01\thotspot\n")

def invoke(action: str, *args: str, expected: int) -> None:
    command = [sys.executable, str(SCRIPT), action, *map(str, args)]
    r = subprocess.run(command, capture_output=True, text=True, timeout=20)
    assert r.returncode == expected, f"{action}: unexpected return {r.returncode}: {r.stdout} / {r.stderr}"
    all_text = r.stdout + r.stderr
    for secret in (FAKE_ACCOUNT, FAKE_DEVICE, FAKE_SECRET, "alice", "bob", "TRUSTED-FAKE-CODE"):
        assert secret not in all_text, "TEST FAILURE: synthetic identity leaked into public diagnostic"
    if expected:
        assert not r.stdout and "EBACK-0677 BLOCKED" in r.stderr
    else:
        assert "EBACK-0677" in r.stdout and not r.stderr

def tree(root: Path) -> dict:
    return {str(p.relative_to(root)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mode & 0o777)
            for p in root.rglob("*") if p.is_file()}

with tempfile.TemporaryDirectory(prefix="blaze-v1-audit-", dir="/tmp") as temp_source, \
     tempfile.TemporaryDirectory(prefix="blaze-v1-seal-", dir="/tmp") as temp_seal, \
     tempfile.TemporaryDirectory(prefix="blaze-v1-key-", dir="/tmp") as temp_key:
    src, sealroot, keyroot = Path(temp_source), Path(temp_seal), Path(temp_key)
    make_fixture(src)
    baseline = tree(src)
    keyfile, backup = keyroot / "key.bin", sealroot / "backup.blaze"
    dst = Path(tempfile.mkdtemp(prefix="blaze-v1-audit-recovered-", dir="/tmp"))
    dst.rmdir()  # Reserve a valid path without allowing an existing restore destination.
    try:
        invoke("keygen", "--key-file", keyfile, expected=0)
        assert keyfile.stat().st_mode & 0o777 == 0o600
        invoke("keygen", "--key-file", keyfile, expected=4)
        invoke("seal", "--source", src, "--backup", backup, "--key-file", keyfile, expected=0)
        assert backup.stat().st_mode & 0o777 == 0o600
        assert FAKE_SECRET.encode() not in backup.read_bytes()
        assert FAKE_ACCOUNT.encode() not in backup.read_bytes()
        assert tree(src) == baseline, "Seal mutated source financial records"
        invoke("seal", "--source", src, "--backup", backup, "--key-file", keyfile, expected=4)
        invoke("restore", "--backup", backup, "--key-file", keyfile, "--output", dst, expected=0)
        assert tree(dst) == baseline, "Restored fake accounts/leases differ from source"
        assert (dst / "targets").stat().st_mode & 0o777 == 0o700
        invoke("restore", "--backup", backup, "--key-file", keyfile, "--output", dst, expected=4)
        saved_cipher = backup.read_bytes()
        saved_key = keyfile.read_bytes()
        # Transporting the backup root must never transport the recovery key.
        assert not (sealroot / "key.bin").exists()
        colocated = sealroot / "key.bin"
        colocated.write_bytes(saved_key)
        colocated.chmod(0o600)
        forbidden_dst = Path("/tmp/blaze-v1-audit-colocated-" + str(os.getpid()))
        invoke("restore", "--backup", backup, "--key-file", colocated,
               "--output", forbidden_dst, expected=4)
        assert not forbidden_dst.exists()
        colocated.unlink()

        # Tampering, wrong-key, shortened authentication tag all fail closed,
        # with no newly created restore directory and no plaintext exposure.
        for i, kind in enumerate(("wrong-key", "tampered", "truncated")):
            reject_dst = Path("/tmp/blaze-v1-audit-seal-reject-" + str(os.getpid()) + "-" + str(i))
            assert not reject_dst.exists()
            if kind == "wrong-key":
                keyfile.write_bytes(os.urandom(32))
            elif kind == "tampered":
                value = bytearray(saved_cipher)
                value[-6] ^= 1
                backup.write_bytes(value)
            else:
                backup.write_bytes(saved_cipher[:-6])
            invoke("restore", "--backup", backup, "--key-file", keyfile,
                   "--output", reject_dst, expected=4)
            assert not reject_dst.exists(), "Failed authenticated restore created output"
            keyfile.write_bytes(saved_key)
            backup.write_bytes(saved_cipher)
        keyfile.chmod(0o644)
        reject_dst = Path("/tmp/blaze-v1-audit-unsafe-key-" + str(os.getpid()))
        invoke("restore", "--backup", backup, "--key-file", keyfile, "--output", reject_dst, expected=4)
        assert not reject_dst.exists()
        keyfile.chmod(0o600)

        # EBACK-0678: ciphertext must not appear at its final filename until
        # every byte is written and the staging file is fsynced. Failures are
        # fault-injected in the LAB module only; no block devices are altered.
        spec = importlib.util.spec_from_file_location("v1_sealed_atomic_lab", SCRIPT)
        assert spec is not None and spec.loader is not None
        sys.path.insert(0, str(SCRIPT.parent))
        try:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        finally:
            sys.path.pop(0)
        backup.unlink()
        for fault in ("write", "file-fsync", "rename"):
            assert not backup.exists(), "A previous failed archive became visible"
            try:
                if fault == "write":
                    with patch.object(mod.os, "write", side_effect=OSError(errno.ENOSPC, "synthetic full disk")):
                        mod.publish_encrypted_archive(backup, saved_cipher)
                elif fault == "file-fsync":
                    with patch.object(mod.os, "fsync", side_effect=OSError(errno.EIO, "synthetic file sync")):
                        mod.publish_encrypted_archive(backup, saved_cipher)
                else:
                    with patch.object(mod, "publish_no_replace",
                                      side_effect=OSError(errno.EIO, "synthetic rename failure")):
                        mod.publish_encrypted_archive(backup, saved_cipher)
            except OSError:
                pass
            else:
                raise AssertionError(f"Injected {fault} unexpectedly succeeded")
            assert not backup.exists(), f"Unsafe partial final archive after {fault}"
            assert not list(sealroot.iterdir()), f"Private stage leak after {fault}"

        # Once a rename succeeds, a failed directory fsync is an UNCERTAIN
        # durability outcome. The *complete* authenticated bytes are retained,
        # and no success is returned to the caller.
        real_fsync = os.fsync
        count = [0]
        def fail_parent_sync(fd):
            count[0] += 1
            if count[0] == 2:
                raise OSError(errno.EIO, "synthetic directory fsync uncertainty")
            return real_fsync(fd)
        try:
            with patch.object(mod.os, "fsync", side_effect=fail_parent_sync):
                mod.publish_encrypted_archive(backup, saved_cipher)
        except OSError:
            pass
        else:
            raise AssertionError("Directory fsync failure falsely acknowledged")
        assert count == [2], "Fixture did not reach simulated post-rename sync"
        assert backup.read_bytes() == saved_cipher, "Published encrypted archive truncated"
        assert not any(p.name.startswith(".blaze-v1-cipher-stage-")
                       for p in sealroot.iterdir()), "Staging file leaked after rename"

        # Existing immutable output must not be replaced, even if a caller
        # attempts to publish the same or modified ciphertext.
        with patch.object(mod, "publish_no_replace",
                          side_effect=AssertionError("Must refuse before rename")):
            try:
                mod.publish_encrypted_archive(backup, saved_cipher + b"x")
            except ValueError:
                pass
            else:
                raise AssertionError("Encrypted backup overwrite unexpectedly succeeded")

        # An unknown paid sidecar or changed marker must prevent new sealing.
        (src / "unknown-money-ledger.tsv").write_text("synthetic-hidden-credit\n")
        (src / "unknown-money-ledger.tsv").chmod(0o600)
        backup.unlink()
        invoke("seal", "--source", src, "--backup", backup, "--key-file", keyfile, expected=4)
        assert not backup.exists()
        (src / "unknown-money-ledger.tsv").unlink()
        put(src / ".blaze-v1-fixture-only", "INVALID-FIXTURE\n")
        invoke("seal", "--source", src, "--backup", backup, "--key-file", keyfile, expected=4)
        assert not backup.exists()
        put(src / ".blaze-v1-fixture-only", "BLAZE-V1-SYNTHETIC-INVENTORY-ONLY\n")
        assert tree(src) == baseline

        # Never read a live /etc source or create a backup with an unsafe key.
        invoke("seal", "--source", "/etc", "--backup", backup, "--key-file", keyfile, expected=4)
        assert not backup.exists()
        keyfile.unlink()
        keyfile.symlink_to("/etc/passwd")
        invoke("seal", "--source", src, "--backup", backup, "--key-file", keyfile, expected=4)
        assert not backup.exists()
        keyfile.unlink()
        assert tree(src) == baseline
    finally:
        if dst.exists():
            import shutil
            shutil.rmtree(dst)

print("EBACK-0677 PASS: AES-256-GCM synthetic sealed backup / exact reversible restore; wrong key, tamper, truncated tag, untrusted source and overwrite blocked")
print("EBACK-0678 PASS: injected write, file-fsync, rename faults publish no partial archive; post-rename fsync refuses success and retains complete ciphertext")
print("NOT PRODUCTION: no customer funds, live quiescence, off-device custody, or hardware power-cut proof")
