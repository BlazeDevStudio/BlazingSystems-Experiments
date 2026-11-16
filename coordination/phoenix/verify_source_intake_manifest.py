#!/usr/bin/env python3
"""Read-only structural gate for COE Pisowifi/SOURCE_INTAKE.json.

Usage: python3 coordination/phoenix/verify_source_intake_manifest.py /path/to/SOURCE_INTAKE.json
No network, Git writes, payment operations or release authorization.
"""
import argparse
from collections import Counter
import json
import sys


def verify(data):
    errors = []
    summary = data.get('summary', {})
    runtime = data.get('runtime', [])
    if not isinstance(runtime, list) or not isinstance(summary, dict):
        return ['summary must be an object and runtime must be an array']
    paths = []
    statuses = Counter()
    for index, entry in enumerate(runtime):
        if not isinstance(entry, dict):
            errors.append(f'runtime[{index}] must be an object')
            continue
        path = entry.get('path')
        if not isinstance(path, str) or not path or path.startswith('/') or '\\' in path or any(p in ('', '.', '..') for p in path.split('/')):
            errors.append(f'runtime[{index}] unsafe or invalid path')
        else:
            paths.append(path)
        src, dst = entry.get('source_git_blob'), entry.get('destination_git_blob')
        if not all(isinstance(v, str) and len(v) == 40 and all(c in '0123456789abcdef' for c in v) for v in (src, dst)):
            errors.append(f'runtime[{index}] invalid blob identity')
        else:
            equal = src == dst
            status = entry.get('status')
            if (status == 'byte_identical') != equal:
                errors.append(f'runtime[{index}] status contradicts recorded blob identities')
        if isinstance(entry.get('status'), str):
            statuses[entry['status']] += 1
    if len(paths) != len(set(paths)):
        errors.append('duplicate runtime path')
    for key, actual in (
        ('recovered_rootfs_file_count', len(runtime)),
        ('recovered_byte_identical_count', statuses['byte_identical']),
        ('locally_derived_files', len(runtime) - statuses['byte_identical']),
    ):
        if type(summary.get(key)) is not int or summary[key] != actual:
            errors.append(f'summary.{key}: expected {actual}, recorded {summary.get(key)!r}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', help='pinned COE SOURCE_INTAKE.json path')
    args = parser.parse_args()
    with open(args.manifest, encoding='utf-8') as handle:
        data = json.load(handle)
    errors = verify(data)
    for error in errors:
        print('FAIL:', error, file=sys.stderr)
    if errors:
        print(f'BLOCKED: {len(errors)} structural errors; no source/destination blob verification', file=sys.stderr)
        return 1
    print('PASS: manifest internal structure only; NOT actual Git blob, license, test or release verification')
    return 0


if __name__ == '__main__':
    sys.exit(main())
