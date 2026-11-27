#!/usr/bin/env python3
"""EBACK-0677: authenticated encrypted backup of disposable v1 TEST FIXTURES.

LAB ONLY: never pass customer data or a production key. The v1 inventory
is UNQUIESCED and neither this tool nor its AES-256-GCM envelope permits
customer migration, router installation, flash writes or v2 authority.
"""
from __future__ import annotations

import argparse
import base64
import ctypes
import json
import errno
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from v060_v1_inventory_fixture import audit, InvalidState, REQUIRED, OPTIONAL, MARKER, MAGIC

MAGIC_SEAL = b"BLAZE-V1-SYNTHETIC-AES256GCM/1\n"
NONCE_BYTES = 12
KEY_BYTES = 32
MAX_FILE = 4 * 1024 * 1024
MAX_BODY = 16 * 1024 * 1024
MAX_BLOB = MAX_BODY + 1024
FILE_RE = re.compile(r"^[A-Za-z0-9_.-]{1,96}\.tsv$")
SOURCE_RE = re.compile(r"^blaze-v1-audit-[A-Za-z0-9_-]+$")
SEAL_RE = re.compile(r"^blaze-v1-seal-[A-Za-z0-9_-]+$")
KEY_RE = re.compile(r"^blaze-v1-key-[A-Za-z0-9_-]+$")


def block():
    raise ValueError("synthetic-only operation refused")


def fixture(path: str, *, must_exist: bool) -> Path:
    p = Path(path)
    if p.parent != Path("/tmp") or not SOURCE_RE.fullmatch(p.name):
        block()
    if p.is_symlink() or (must_exist and not p.is_dir()):
        block()
    return p


def seal_file(path: str, *, must_exist: bool) -> Path:
    p = Path(path)
    parent = p.parent
    if parent.parent != Path("/tmp") or parent.is_symlink():
        block()
    if not ((p.name == "key.bin" and KEY_RE.fullmatch(parent.name)) or
            (p.name == "backup.blaze" and SEAL_RE.fullmatch(parent.name))):
        block()
    if parent.is_dir():
        st = parent.stat()
        if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.geteuid() or (st.st_mode & 0o777) != 0o700:
            block()
    elif must_exist:
        block()
    if p.is_symlink() or (must_exist and not p.is_file()):
        block()
    return p


def strict_file(path: Path, *, length: int | None = None) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid != os.geteuid() or st.st_nlink != 1 or (st.st_mode & 0o777) != 0o600:
            block()
        if st.st_size > MAX_BLOB or (length is not None and st.st_size != length):
            block()
        data = bytearray()
        while len(data) < MAX_BLOB + 1:
            chunk = os.read(fd, min(65536, MAX_BLOB + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        now = os.fstat(fd)
        if len(data) != st.st_size or (st.st_ino, st.st_mtime_ns, st.st_ctime_ns) != (now.st_ino, now.st_mtime_ns, now.st_ctime_ns):
            block()
        return bytes(data)
    finally:
        os.close(fd)


def durable_new(path: Path, content: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        pos = 0
        while pos < len(content):
            n = os.write(fd, content[pos:])
            if n <= 0:
                block()
            pos += n
        os.fsync(fd)
    finally:
        os.close(fd)
    dirfd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(dirfd)
    finally:
        os.close(dirfd)


def publish_no_replace(stage: Path, destination: Path) -> None:
    """Linux renameat2(RENAME_NOREPLACE) works for files and directories."""
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        block()
    renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p,
                          ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    renameat2.restype = ctypes.c_int
    ret = renameat2(-100, os.fsencode(stage), -100,
                    os.fsencode(destination), 1)
    if ret != 0:
        block()


def publish_encrypted_archive(output: Path, contents: bytes) -> None:
    """Never expose a partially written *final* encrypted archive.

    A failed write/fsync/rename leaves backup.blaze uncreated. Once renamed,
    an fsync failure is an UNKNOWN-DURABILITY result, not a success ACK; the
    complete archive is left for authenticated investigation, not overwritten.
    A real appliance power cut must be tested separately.
    """
    if output.exists() or output.is_symlink():
        block()
    fd, name = tempfile.mkstemp(prefix=".blaze-v1-cipher-stage-", dir=output.parent)
    stage = Path(name)
    try:
        try:
            os.fchmod(fd, 0o600)
            pos = 0
            while pos < len(contents):
                n = os.write(fd, contents[pos:])
                if n <= 0:
                    block()
                pos += n
            os.fsync(fd)
        finally:
            os.close(fd)
        publish_no_replace(stage, output)
        parent_fd = os.open(output.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    finally:
        # Only unpublished temporary ciphertext is removed. A published
        # complete file survives a later fsync error for manual investigation.
        if stage.exists():
            stage.unlink()


def keygen(keypath: str) -> None:
    p = seal_file(keypath, must_exist=False)
    if p.name != "key.bin" or not p.parent.is_dir():
        block()
    durable_new(p, os.urandom(KEY_BYTES))
    print("EBACK-0677 synthetic key generated (private bytes NOT displayed)")


def collect(root: Path) -> list[dict]:
    pre = audit(root)
    if pre.get("status") != "SCHEMA_READABLE_UNQUIESCED" or pre.get("migration_authorized") is not False:
        block()
    names = [MARKER, *REQUIRED, *(n for n in OPTIONAL if (root / n).exists())]
    target = root / "targets"
    if target.is_symlink() or not target.is_dir():
        block()
    entries = sorted(target.iterdir())
    for p in entries:
        if not FILE_RE.fullmatch(p.name):
            block()
    names += ["targets/" + p.name for p in entries]
    records = []
    for name in names:
        item = root / name
        content = strict_file(item)
        if len(content) > MAX_FILE:
            block()
        records.append({"path": name, "mode": 0o600,
                        "value": base64.b64encode(content).decode("ascii")})
    # A second scan detects *some* concurrent writes; neither scan provides
    # a source-owned lock, an atomic point-in-time view, or permission to cut over.
    post = audit(root)
    if post != pre:
        block()
    for entry in records:
        if strict_file(root / entry["path"]) != base64.b64decode(entry["value"]):
            block()
    return records


def seal(source: str, backup: str, keyfile: str) -> None:
    src = fixture(source, must_exist=True)
    output = seal_file(backup, must_exist=False)
    keypath = seal_file(keyfile, must_exist=True)
    if output.name != "backup.blaze" or keypath.name != "key.bin" or keypath.parent == output.parent:
        block()
    if output.exists():
        block()
    key = strict_file(keypath, length=KEY_BYTES)
    records = collect(src)
    body = json.dumps({"format": "blaze-v1-synthetic-sealed/1",
                       "fixture_only": True, "migration_authorized": False,
                       "quiesced": False, "files": records},
                      sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(body) > MAX_BODY:
        block()
    nonce = os.urandom(NONCE_BYTES)
    cipher = AESGCM(key).encrypt(nonce, body, MAGIC_SEAL)
    publish_encrypted_archive(output, MAGIC_SEAL + nonce + cipher)
    print("EBACK-0677 sealed synthetic backup created; not customer migration")


def unpack(payload: bytes) -> list[tuple[str, bytes]]:
    if len(payload) > MAX_BODY:
        block()
    doc = json.loads(payload)
    if not isinstance(doc, dict) or set(doc) != {"format", "fixture_only", "migration_authorized", "quiesced", "files"}:
        block()
    if doc["format"] != "blaze-v1-synthetic-sealed/1" or doc["fixture_only"] is not True or doc["migration_authorized"] is not False or doc["quiesced"] is not False:
        block()
    files = doc["files"]
    if not isinstance(files, list) or not (len(REQUIRED) + 1 <= len(files) <= 256):
        block()
    paths, items = set(), []
    for entry in files:
        if not isinstance(entry, dict) or set(entry) != {"path", "mode", "value"}:
            block()
        name, mode, encoded = entry["path"], entry["mode"], entry["value"]
        if not isinstance(name, str) or not isinstance(mode, int) or mode != 0o600 or not isinstance(encoded, str):
            block()
        if name in paths or (name != MARKER and name not in REQUIRED and name not in OPTIONAL
                             and not (name.startswith("targets/") and FILE_RE.fullmatch(name[8:]))):
            block()
        paths.add(name)
        data = base64.b64decode(encoded, validate=True)
        if len(data) > MAX_FILE:
            block()
        items.append((name, data))
    if not set(REQUIRED + (MARKER,)).issubset(paths) or not any(n.startswith("targets/") for n in paths):
        block()
    if dict(items)[MARKER] != MAGIC:
        block()
    return items


def restore(backup: str, keyfile: str, dest: str) -> None:
    input_path = seal_file(backup, must_exist=True)
    keypath = seal_file(keyfile, must_exist=True)
    dst = fixture(dest, must_exist=False)
    if input_path.name != "backup.blaze" or keypath.name != "key.bin" or keypath.parent == input_path.parent:
        block()
    if dst.exists() or dst.is_symlink():
        block()
    blob = strict_file(input_path)
    if not blob.startswith(MAGIC_SEAL) or len(blob) <= len(MAGIC_SEAL) + NONCE_BYTES + 16:
        block()
    nonce_start = len(MAGIC_SEAL)
    nonce = blob[nonce_start:nonce_start + NONCE_BYTES]
    data = AESGCM(strict_file(keypath, length=KEY_BYTES)).decrypt(nonce, blob[nonce_start + NONCE_BYTES:], MAGIC_SEAL)
    records = unpack(data)  # authenticated and validated before writing anything
    stage = Path(tempfile.mkdtemp(prefix="blaze-v1-audit-ebstage-", dir="/tmp"))
    try:
        (stage / "targets").mkdir(mode=0o700)
        for name, contents in records:
            durable_new(stage / name, contents)
        # Fail closed on schema, references, deleted ledgers, or invalid marker.
        result = audit(stage)
        if result.get("status") != "SCHEMA_READABLE_UNQUIESCED":
            block()
        if dst.exists() or dst.is_symlink():
            block()
        publish_no_replace(stage, dst)  # atomic fail-if-exists
        dirfd = os.open("/tmp", os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    print("EBACK-0677 synthetic restore verified to new isolated directory; migration_authorized=0")


def main() -> int:
    p = argparse.ArgumentParser(description="LAB ONLY synthetic sealed v1 fixture: never live data")
    opts = p.add_subparsers(dest="action", required=True)
    gen = opts.add_parser("keygen")
    gen.add_argument("--key-file", required=True)
    enc = opts.add_parser("seal")
    enc.add_argument("--source", required=True)
    enc.add_argument("--backup", required=True)
    enc.add_argument("--key-file", required=True)
    dec = opts.add_parser("restore")
    dec.add_argument("--backup", required=True)
    dec.add_argument("--key-file", required=True)
    dec.add_argument("--output", required=True)
    args = p.parse_args()
    try:
        if args.action == "keygen":
            keygen(args.key_file)
        elif args.action == "seal":
            seal(args.source, args.backup, args.key_file)
        elif args.action == "restore":
            restore(args.backup, args.key_file, args.output)
        return 0
    except (OSError, ValueError, InvalidState, InvalidTag, KeyError, TypeError, OverflowError) as exc:
        # Intentionally no path, account, input or crypto exception details.
        print("EBACK-0677 BLOCKED: unverified/unsafe synthetic operation", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
