#!/usr/bin/env python3
"""Provision only the fixed private, read-only SSH status mapping on a lab host.

The LIO target must already be verifiably disabled. This command does not
create an SSH identity, authorize a key, change sshd, or enable a target.
"""

import argparse
import os
from pathlib import Path
import stat
import sys

from blaze_lio_prepare import (LioBackend, Refused, private_directory,
                               write_record)
from blaze_lio_ssh_status import CONFIG, read_config
from blaze_lio_status import inspect


def secure_ancestors(path, owner):
    if not path.is_absolute() or path == Path("/") or ".." in path.parts:
        raise Refused("unsafe status path")
    current = path.parent
    while True:
        info = current.lstat()
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != owner or
                stat.S_IMODE(info.st_mode) & 0o022):
            raise Refused("unsafe status path ancestor")
        if current == current.parent:
            break
        current = current.parent


def provision(config, spec, secret_file, state_dir, backend, *, owner=None):
    if owner is None:
        owner = os.geteuid()
    for path in (config, spec, secret_file, state_dir):
        secure_ancestors(path, owner)
    private_directory(config.parent, owner)
    try:
        config.lstat()
    except FileNotFoundError:
        pass
    else:
        raise Refused("status configuration already exists")
    if inspect(spec, secret_file, state_dir, backend) != "PREPARED_DISABLED":
        raise Refused("LIO target is not verifiably disabled")
    record = {"spec": str(spec), "secret_file": str(secret_file),
              "state_dir": str(state_dir)}
    # O_EXCL plus file and directory fsync. A partial write remains present
    # and blocks retry until an operator reconciles it; never overwrite it.
    write_record(config, record)
    if read_config(config, owner) != {
            key: Path(value) for key, value in record.items()}:
        raise Refused("status configuration readback mismatch")
    return "STATUS_CONFIGURED"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--secret-file", required=True, type=Path)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--confirm-lab-ssh-status", action="store_true")
    args = parser.parse_args()
    try:
        if (not args.confirm_lab_ssh_status or sys.platform != "linux" or
                os.geteuid() != 0):
            raise Refused("operator confirmation and Linux root required")
        result = provision(CONFIG, args.spec, args.secret_file, args.state_dir,
                           LioBackend(Path("/etc/target/saveconfig.json")))
    except Exception:
        print("SSH status setup uncertain; inspect private config locally", file=sys.stderr)
        return 8
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
