#!/usr/bin/env python3
"""Fail early if this Linux machine is clearly too small for an Android 16 build."""
import argparse
import os
from pathlib import Path
import shutil

gib = 1024 ** 3
# Conservative hard floor, not a claim that successful builds need only this much.
MIN_RAM = 28 * gib
MIN_FREE_DISK = 300 * gib


def validate_capacity(total_ram, free_disk):
    problems = []
    if total_ram < MIN_RAM:
        problems.append(
            f"RAM: {total_ram/gib:.1f} GiB available physically; "
            f"need at least {MIN_RAM/gib:.0f} GiB (32+ GiB recommended)"
        )
    if free_disk < MIN_FREE_DISK:
        problems.append(
            f"disk: {free_disk/gib:.1f} GiB free; "
            f"need at least {MIN_FREE_DISK/gib:.0f} GiB before source sync"
        )
    if problems:
        raise RuntimeError(
            "BlazeDroid Android 16 build-host preflight failed: "
            + "; ".join(problems)
            + ". Provide a larger dedicated Linux build runner; "
            "do not substitute a generic ISO."
        )


def physical_ram_bytes():
    return os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_directory", type=Path)
    args = parser.parse_args()
    if not args.source_directory.is_dir():
        parser.error(f"source directory does not exist: {args.source_directory}")
    ram = physical_ram_bytes()
    disk = shutil.disk_usage(args.source_directory).free
    print(f"BlazeDroid Android 16 host: physical RAM {ram/gib:.1f} GiB; "
          f"free source filesystem {disk/gib:.1f} GiB")
    try:
        validate_capacity(ram, disk)
    except RuntimeError as exc:
        parser.exit(status=1, message=str(exc) + "\n")
    print("Build-host capacity preflight PASS. This does not prove Android will compile.")


if __name__ == "__main__":
    main()
