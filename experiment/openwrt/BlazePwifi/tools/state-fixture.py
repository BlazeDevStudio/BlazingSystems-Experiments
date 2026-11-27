#!/usr/bin/env python3
"""TEST FIXTURES ONLY. Do not use for live customer data or as a release backup.

Copy and integrity-check a synthetic BlazePwifi state tree under a sentinel.
This is the first off-device building block of a migration recovery test;
it intentionally cannot connect to a router or restore over existing files.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tempfile

MARKER = ".blaze-fixture-only"
MARKER_BYTES = b"BLAZE-SYNTHETIC-FIXTURE-ONLY\n"
REL = (
    "etc/config/blazepwifi",
    "etc/blazepwifi/state",
    "etc/blazepwifi/portal",
    "etc/uhttpd.crt",
    "etc/uhttpd.key",
)
KEEP = Path(__file__).resolve().parents[1] / "openwrt/rootfs/lib/upgrade/keep.d/blazepwifi"

def abort(message):
    raise ValueError(message)

def private_path(path):
    p = Path(path).expanduser().resolve()
    if str(p) == "/" or p == Path.home() or p in (Path("/etc"), Path("/root"), Path("/var"), Path("/tmp")):
        abort("Refusing protected root/path; synthetic test fixtures only")
    if any(str(p).startswith(prefix) for prefix in ("/etc/", "/root/", "/var/lib/", "/usr/", "/sys/", "/proc/", "/dev/")):
        abort("Refusing system path; synthetic test fixtures only")
    return p

def assert_fixture(root):
    root = private_path(root)
    if not root.is_dir() or not (root / MARKER).is_file():
        abort("Missing test-only marker; refuse real/customer data")
    if (root / MARKER).read_bytes() != MARKER_BYTES:
        abort("Invalid synthetic fixture marker")
    return root

def sha256(path):
    dig = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(1024 * 256)
            if not block:
                break
            dig.update(block)
    return dig.hexdigest()

def fsync_write(path, value):
    with path.open("xb") as f:
        f.write(value)
        f.flush()
        os.fsync(f.fileno())

def safe_rel(name):
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        abort("Invalid manifest path")
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or p.as_posix() != name or name == ".":
        abort("Unsafe manifest traversal path")
    return p

def keep_paths():
    actual = set()
    for ln in KEEP.read_text(encoding="utf-8").splitlines():
        line = ln.strip()
        if line and not line.startswith("#"):
            if not line.startswith("/") or ".." in PurePosixPath(line).parts:
                abort("Unsafe OpenWrt keep.d path")
            actual.add(line.removeprefix("/"))
    if actual != set(REL):
        abort("Keep.d scope changed; reconcile state snapshot prototype first")
    return sorted(actual)

def read_regular(root, dest, relative, entries):
    s = root / relative
    st = os.lstat(s)
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
        abort("Symbolic links, special files and hardlinks are prohibited")
    d = dest / relative
    d.parent.mkdir(parents=True, exist_ok=True)
    # The prototype is for tiny synthetic records only.
    if st.st_size > 4 * 1024 * 1024:
        abort("Synthetic test file too large")
    with s.open("rb") as inp:
        with d.open("xb") as out:
            shutil.copyfileobj(inp, out, length=1024 * 256)
            out.flush()
            os.fsync(out.fileno())
    mode = stat.S_IMODE(st.st_mode)
    os.chmod(d, mode)
    entries.append({"path": relative.as_posix(), "size": st.st_size,
                    "sha256": sha256(d), "mode": mode})

def snapshot(root, output):
    src = assert_fixture(root)
    dest = private_path(output)
    if dest.exists() or dest.is_symlink():
        abort("Destination exists; immutable snapshot overwrite prohibited")
    if dest.is_relative_to(src) or src.is_relative_to(dest):
        abort("Source/destination nesting prohibited")
    dest.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".blaze-snapshot-", dir=dest.parent))
    try:
        files = stage / "files"
        files.mkdir()
        entries = []
        for relative in keep_paths():
            source = src / relative
            if not source.exists() and not source.is_symlink():
                continue  # optional portal and TLS path are permitted to be absent
            st = os.lstat(source)
            if stat.S_ISREG(st.st_mode):
                read_regular(src, files, Path(relative), entries)
            elif stat.S_ISDIR(st.st_mode):
                for here, dirs, names in os.walk(source, followlinks=False):
                    dirs.sort()
                    names.sort()
                    for dirname in dirs:
                        item = Path(here) / dirname
                        if not stat.S_ISDIR(os.lstat(item).st_mode):
                            abort("Unsafe directory link/special file")
                    for name in names:
                        item = Path(here) / name
                        read_regular(src, files, item.relative_to(src), entries)
            else:
                abort("Unsafe root scope entry type")
        if not (src / "etc/config/blazepwifi").is_file() or not (src / "etc/blazepwifi/state").is_dir():
            abort("Synthetic fixture missing config or paid-state directory")
        if not any(x["path"].startswith("etc/blazepwifi/state/") for x in entries):
            abort("Synthetic paid-state fixture empty")
        entries.sort(key=lambda x: x["path"])
        manifest = {"format": "blaze-synthetic-state-v1", "synthetic_only": True,
                    "files": entries, "total_bytes": sum(e["size"] for e in entries)}
        fsync_write(stage / "manifest.json", (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode())
        os.chmod(stage, 0o700)
        os.replace(stage, dest)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    print(f"Synthetic snapshot created: {len(entries)} files, {manifest['total_bytes']} bytes; no contents logged")

def verify(backup):
    src = private_path(backup)
    raw = (src / "manifest.json").read_bytes()
    if len(raw) > 1024 * 1024:
        abort("Manifest too large")
    data = json.loads(raw)
    if data.get("format") != "blaze-synthetic-state-v1" or data.get("synthetic_only") is not True:
        abort("This is not a synthetic test snapshot")
    files = data.get("files")
    if not isinstance(files, list) or not files or len(files) > 2048:
        abort("Invalid fixture manifest count")
    seen, total = set(), 0
    for record in files:
        name = record["path"]
        p = safe_rel(name)
        if name in seen or not any(name == q or name.startswith(q + "/") for q in REL):
            abort("Unexpected or duplicate snapshot path")
        seen.add(name)
        f = src / "files" / Path(*p.parts)
        st = os.lstat(f)
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
            abort("Unsafe snapshot file type")
        if st.st_size != record["size"] or sha256(f) != record["sha256"]:
            abort("Snapshot integrity verification failed")
        if not isinstance(record["mode"], int) or record["mode"] < 0 or record["mode"] > 0o777:
            abort("Invalid source permissions")
        total += st.st_size
    if total != data.get("total_bytes"):
        abort("Snapshot total byte mismatch")
    for here, dirs, filenames in os.walk(src / "files", followlinks=False):
        for dirname in dirs:
            if not stat.S_ISDIR(os.lstat(Path(here) / dirname).st_mode):
                abort("Unsafe directory link")
        for filename in filenames:
            relative = (Path(here) / filename).relative_to(src / "files").as_posix()
            if relative not in seen:
                abort("Unexpected unlisted snapshot file")
    return data

def restore(backup, output):
    src = private_path(backup)
    data = verify(src)
    dest = private_path(output)
    if dest.exists() or dest.is_symlink() or dest.is_relative_to(src) or src.is_relative_to(dest):
        abort("Refuse overwrite or nested fixture restore")
    dest.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".blaze-restore-", dir=dest.parent))
    try:
        fsync_write(stage / MARKER, MARKER_BYTES)
        for rec in data["files"]:
            relative = Path(*safe_rel(rec["path"]).parts)
            out = stage / relative
            out.parent.mkdir(parents=True, exist_ok=True)
            with (src / "files" / relative).open("rb") as inp, out.open("xb") as dst:
                shutil.copyfileobj(inp, dst, length=1024 * 256)
                dst.flush()
                os.fsync(dst.fileno())
            os.chmod(out, rec["mode"])
            if sha256(out) != rec["sha256"]:
                abort("Restore integrity verification failed")
        os.replace(stage, dest)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    print(f"Synthetic fixture restored into NEW directory: {len(data['files'])} verified files")

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    commands = ap.add_subparsers(dest="action", required=True)
    p = commands.add_parser("snapshot")
    p.add_argument("--root", required=True)
    p.add_argument("--output", required=True)
    p = commands.add_parser("verify")
    p.add_argument("--backup", required=True)
    p = commands.add_parser("restore")
    p.add_argument("--backup", required=True)
    p.add_argument("--output", required=True)
    args = ap.parse_args()
    try:
        if args.action == "snapshot":
            snapshot(args.root, args.output)
        elif args.action == "verify":
            data = verify(args.backup)
            print(f"Synthetic snapshot integrity verified: {len(data['files'])} files")
        else:
            restore(args.backup, args.output)
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"FAIL CLOSED: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
