#!/usr/bin/env python3
"""Read-only verification of a disabled LIO lab target.

An active, incomplete, or uncertain target is never reported as healthy.
This command emits no CHAP secret, backing path, or success on refusal.
"""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

from blaze_lio_activate import activation_record
from blaze_lio_prepare import (LioBackend, Refused, private_directory,
                               private_regular, read_secret, read_spec,
                               unique_object)


def inspect(spec_path, secret_path, state_dir, backend, *, require_root=True):
    if require_root and (sys.platform != "linux" or os.geteuid() != 0):
        raise Refused("Linux root is required")
    owner = os.geteuid()
    private_directory(state_dir, owner)
    spec, image_stat = read_spec(spec_path, owner)
    secret = read_secret(secret_path, owner)
    key = hashlib.sha256(spec["target_iqn"].encode("ascii")).hexdigest()
    marker = state_dir / (key + ".json")
    lockfd = os.open(state_dir / ".lock", os.O_RDONLY | os.O_NOFOLLOW)
    try:
        lock_stat = os.fstat(lockfd)
        if (not stat.S_ISREG(lock_stat.st_mode) or lock_stat.st_nlink != 1 or
                lock_stat.st_uid != owner or stat.S_IMODE(lock_stat.st_mode) != 0o600):
            raise Refused("unsafe preparation lock")
        fcntl.flock(lockfd, fcntl.LOCK_SH)
        private_regular(marker, owner)
        if marker.stat().st_size > 4096:
            raise Refused("preparation intent too large")
        try:
            recorded = json.loads(marker.read_bytes(), object_pairs_hook=unique_object)
        except (UnicodeError, ValueError) as error:
            raise Refused("preparation intent malformed") from error
        if recorded != activation_record(spec, image_stat, "prepared_disabled"):
            raise Refused("intent, image identity, or state is not safely verifiable")
        backend.inspect_prepared(spec, secret, image_stat)
    finally:
        os.close(lockfd)
    return "PREPARED_DISABLED"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--secret-file", required=True, type=Path)
    parser.add_argument("--state-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = inspect(args.spec, args.secret_file, args.state_dir,
                         LioBackend(Path("/etc/target/saveconfig.json")))
    except Exception:
        print("LIO status uncertain; inspect target and private intent", file=sys.stderr)
        return 8
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
