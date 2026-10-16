#!/usr/bin/env python3
"""Explicit lab-only activation of one previously prepared Linux LIO target."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

from blaze_lio_prepare import (LioBackend, Refused, private_directory,
                               private_regular, image_identity, read_secret, read_spec,
                               unique_object, write_record)


def fsync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def activation_record(spec, image_stat, status):
    return {"status": status, "target_iqn": spec["target_iqn"],
            "initiator_iqn": spec["initiator_iqn"], "image_path": spec["image_path"],
            "image_dev": image_stat.st_dev, "image_ino": image_stat.st_ino,
            "image_size": image_stat.st_size,
            "image_ctime_ns": image_stat.st_ctime_ns,
            "image_mtime_ns": image_stat.st_mtime_ns}


def replace_record(marker, record):
    replacement = marker.with_name("." + marker.stem + ".next")
    write_record(replacement, record)
    os.replace(replacement, marker)
    fsync_directory(marker.parent)


def activate(spec_path, secret_path, state_dir, backend, *, require_root=True):
    if require_root and (sys.platform != "linux" or os.geteuid() != 0):
        raise Refused("Linux root is required")
    owner = os.geteuid()
    private_directory(state_dir, owner)
    spec, image_stat = read_spec(spec_path, owner)
    secret = read_secret(secret_path, owner)
    key = hashlib.sha256(spec["target_iqn"].encode("ascii")).hexdigest()
    marker = state_dir / (key + ".json")
    lockfd = os.open(state_dir / ".lock", os.O_RDWR | os.O_NOFOLLOW)
    try:
        lock_stat = os.fstat(lockfd)
        if (not stat.S_ISREG(lock_stat.st_mode) or lock_stat.st_nlink != 1 or
                lock_stat.st_uid != owner or stat.S_IMODE(lock_stat.st_mode) != 0o600):
            raise Refused("unsafe preparation lock")
        fcntl.flock(lockfd, fcntl.LOCK_EX)
        private_regular(marker, owner)
        if marker.stat().st_size > 4096:
            raise Refused("preparation intent too large")
        try:
            recorded = json.loads(marker.read_bytes(), object_pairs_hook=unique_object)
        except (UnicodeError, ValueError) as error:
            raise Refused("preparation intent malformed") from error
        expected = activation_record(spec, image_stat, "prepared_disabled")
        if recorded != expected:
            raise Refused("preparation intent or image identity changed")
        # Inspect before changing the intent, then inspect again inside the
        # backend immediately before toggling the target.
        backend.inspect_prepared(spec, secret, image_stat)
        replace_record(marker, activation_record(spec, image_stat, "activating"))
        try:
            backend.activate(spec, secret, image_stat)
            current = private_regular(Path(spec["image_path"]), owner)
            if image_identity(current) != image_identity(image_stat):
                raise Refused("backing image changed during activation")
            replace_record(marker, activation_record(spec, image_stat, "active"))
        except Exception:
            # Best effort only: after a crash or storage failure a live target
            # may remain. The 'activating' intent still denies automatic retry.
            try:
                backend.quarantine(spec)
            except Exception:
                pass
            raise
    finally:
        os.close(lockfd)
    return "ACTIVE_LAB_TARGET"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--secret-file", required=True, type=Path)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--confirm-lab-activation", action="store_true")
    args = parser.parse_args()
    if not args.confirm_lab_activation:
        print("explicit lab activation confirmation required", file=sys.stderr)
        return 8
    try:
        result = activate(args.spec, args.secret_file, args.state_dir,
                          LioBackend(Path("/etc/target/saveconfig.json")))
    except Exception:
        # Library errors could include secrets. An 'activating' intent can
        # mean the target is live even if no success line was returned.
        print("LIO activation refused or uncertain; inspect target and intent", file=sys.stderr)
        return 8
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
