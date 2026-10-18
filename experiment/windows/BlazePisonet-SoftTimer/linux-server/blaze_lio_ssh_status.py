#!/usr/bin/env python3
"""Forced SSH command for one operator-provisioned, read-only lab LIO target.

The fixed root-owned configuration supplies paths; the SSH client supplies no
target identity, secret, file path, or action. This script never enables LIO.
"""

import json
import os
from pathlib import Path
import sys

from blaze_lio_prepare import LioBackend, Refused, private_directory, private_regular, unique_object
from blaze_lio_status import inspect


CONFIG = Path("/etc/blaze-lio/ssh-status.json")
FIELDS = {"spec", "secret_file", "state_dir"}


def read_config(path, owner):
    private_directory(path.parent, owner)
    file_stat = private_regular(path, owner)
    if file_stat.st_size > 2048:
        raise Refused("SSH status configuration too large")
    try:
        data = json.loads(path.read_bytes(), object_pairs_hook=unique_object)
    except (UnicodeError, ValueError) as error:
        raise Refused("SSH status configuration malformed") from error
    if (not isinstance(data, dict) or set(data) != FIELDS or
            any(not isinstance(value, str) or not value.startswith("/") or
                value == "/" for value in data.values())):
        raise Refused("SSH status configuration incomplete")
    return {key: Path(value) for key, value in data.items()}


def inspect_configured(config, owner, backend):
    settings = read_config(config, owner)
    return inspect(settings["spec"], settings["secret_file"],
                   settings["state_dir"], backend)


def main():
    try:
        if len(sys.argv) != 1 or os.environ.get("SSH_ORIGINAL_COMMAND") != "blaze-lio-status":
            raise Refused("unexpected SSH command")
        if sys.platform != "linux" or os.geteuid() != 0:
            raise Refused("Linux root required")
        result = inspect_configured(CONFIG, os.geteuid(),
                                    LioBackend(Path("/etc/target/saveconfig.json")))
    except Exception:
        print("LIO status uncertain; inspect target locally", file=sys.stderr)
        return 8
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
