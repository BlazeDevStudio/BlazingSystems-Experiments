"""Offline-only upstream release-metadata assessment with *no* trust promotion.

GitHub API digests are useful integrity references but not supplier attestations.
This module never downloads, extracts, executes or writes an installation target.
"""
from __future__ import annotations
import argparse
from datetime import date
import json
import os
from pathlib import Path
import re
import stat
from urllib.parse import urlsplit

from archive_integrity import audit_zip

DIGEST = re.compile(r'[0-9a-f]{64}\Z')
BLOB_SHA = re.compile(r'[0-9a-f]{40}\Z')
NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z')
MAX_MANIFEST = 128 * 1024
EVIDENCE = 'github_api_metadata_not_independent_authentication'
ROOT_KEYS = {'schema_version', 'observed_on', 'evidence_type', 'components', 'excluded_components'}
COMPONENT_KEYS = {'repository', 'tag', 'asset_name', 'github_api_sha256',
    'github_api_asset_size', 'release_url', 'asset_url', 'source_license_url',
    'source_license_blob_sha', 'source_license_observation',
    'independently_authenticated_publisher', 'binary_redistribution_cleared'}


def _object_no_dupes(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError('Duplicate JSON key: ' + k)
        out[k] = v
    return out


def _reject_nan(value):
    raise ValueError('Unsupported JSON numeric constant: ' + value)


def parse_manifest(data: bytes):
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_MANIFEST:
        raise ValueError('Manifest exceeds allowed size or is empty')
    return json.loads(data.decode('utf-8'), object_pairs_hook=_object_no_dupes,
                      parse_constant=_reject_nan)


def _exact_github_url(actual, expected):
    if not isinstance(actual, str) or any(not 33 <= ord(c) <= 126 for c in actual):
        return False
    try:
        parsed = urlsplit(actual)
        return (parsed.scheme == 'https' and parsed.netloc in ('github.com', 'github.com:443')
                and parsed.path == expected and not parsed.query and not parsed.fragment
                and not parsed.username and not parsed.password)
    except ValueError:
        return False


def _result(errors, count=0):
    return {'metadata_structure_valid': not errors, 'component_count': count,
            'publisher_identity_independently_verified': False,
            'license_redistribution_cleared': False,
            'component_auth_gate_satisfied': False, 'errors': errors}


def inspect_manifest(metadata):
    errors = []
    if not isinstance(metadata, dict):
        return _result(['Manifest root must be an object'])
    if set(metadata) != ROOT_KEYS:
        errors.append('Missing or unexpected root fields')
    if type(metadata.get('schema_version')) is not int or metadata['schema_version'] != 1:
        errors.append('Unsupported schema version')
    if metadata.get('evidence_type') != EVIDENCE:
        errors.append('Unsupported evidence class or false trust claim')
    observation = metadata.get('observed_on')
    try:
        if not isinstance(observation, str) or len(observation) != 10 or date.fromisoformat(observation).isoformat() != observation:
            raise ValueError()
    except ValueError:
        errors.append('Invalid observed_on date')
    excluded = metadata.get('excluded_components')
    if not isinstance(excluded, list) or len(excluded) > 32:
        errors.append('Invalid exclusions list')
    else:
        seen_excluded = set()
        for item in excluded:
            if (not isinstance(item, dict) or set(item) != {'name', 'reason'} or
                    not isinstance(item.get('name'), str) or not NAME.fullmatch(item['name']) or
                    not isinstance(item.get('reason'), str) or not 0 < len(item['reason']) <= 512 or
                    item['name'] in seen_excluded):
                errors.append('Invalid or duplicate exclusion')
            else:
                seen_excluded.add(item['name'])
    items = metadata.get('components')
    if not isinstance(items, list) or not 0 < len(items) <= 32:
        return _result(errors + ['Expected 1-32 component records'])
    seen = set()
    for i, x in enumerate(items):
        if not isinstance(x, dict) or set(x) != COMPONENT_KEYS:
            errors.append(f'{i}: Missing or unexpected component fields')
            continue
        repo, tag, asset = x['repository'], x['tag'], x['asset_name']
        if not all(isinstance(s, str) and NAME.fullmatch(s) for s in (repo, tag, asset)):
            errors.append(f'{i}: Invalid repository/tag/asset identifier')
            continue
        if repo in seen:
            errors.append(f'{i}: Duplicate repository')
        seen.add(repo)
        if not isinstance(x['github_api_sha256'], str) or not DIGEST.fullmatch(x['github_api_sha256']):
            errors.append(f'{i}: Invalid artifact digest')
        if type(x['github_api_asset_size']) is not int or not 0 < x['github_api_asset_size'] <= 1024**3:
            errors.append(f'{i}: Invalid artifact size')
        if not isinstance(x['source_license_blob_sha'], str) or not BLOB_SHA.fullmatch(x['source_license_blob_sha']):
            errors.append(f'{i}: Invalid license blob identifier')
        for field, expected in (
            ('release_url', f'/acidanthera/{repo}/releases/tag/{tag}'),
            ('asset_url', f'/acidanthera/{repo}/releases/download/{tag}/{asset}'),
            ('source_license_url', f'/acidanthera/{repo}/blob/{tag}/LICENSE.txt')):
            if not _exact_github_url(x[field], expected):
                errors.append(f'{i}: Invalid {field}')
        if (x['independently_authenticated_publisher'] is not False or
                x['binary_redistribution_cleared'] is not False):
            errors.append(f'{i}: Unsubstantiated publisher/license clearance')
        observation = x['source_license_observation']
        if not isinstance(observation, str) or not 0 < len(observation) <= 512:
            errors.append(f'{i}: Invalid license observation')
    return _result(errors, len(items))


def inspect_asset(metadata, repository, archive):
    r = inspect_manifest(metadata)
    if not r['metadata_structure_valid']:
        return r
    components = [c for c in metadata['components'] if c['repository'] == repository]
    if len(components) != 1:
        return _result(['Unknown or ambiguous component repository'])
    c = components[0]
    audit = audit_zip(archive, c['github_api_sha256'], c['github_api_asset_size'])
    audit['metadata_structure_valid'] = True
    audit['github_api_digest_match'] = audit['archive_hash_match']
    audit['publisher_identity_independently_verified'] = False
    audit['license_redistribution_cleared'] = False
    return audit


def _read_manifest_file(path):
    p = Path(path)
    if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()):
        raise ValueError('Linked manifest rejected')
    before = p.lstat()
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_MANIFEST:
        raise ValueError('Manifest is not a bounded regular file')
    fd = os.open(p, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0))
    with os.fdopen(fd, 'rb') as f:
        opened = os.fstat(f.fileno())
        if not stat.S_ISREG(opened.st_mode) or opened.st_size != before.st_size:
            raise ValueError('Manifest changed during opening')
        b = f.read(MAX_MANIFEST + 1)
        after = os.fstat(f.fileno())
        if len(b) != opened.st_size or (opened.st_size, opened.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError('Manifest changed while reading')
        return parse_manifest(b)


def main():
    parser = argparse.ArgumentParser(description='Read-only GitHub metadata trust-scope inspector')
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--repository')
    parser.add_argument('--archive')
    args = parser.parse_args()
    try:
        if bool(args.repository) != bool(args.archive):
            raise ValueError('--repository and --archive must be paired')
        metadata = _read_manifest_file(args.manifest)
        r = inspect_asset(metadata, args.repository, args.archive) if args.repository else inspect_manifest(metadata)
    except (OSError, ValueError, UnicodeDecodeError, RecursionError, json.JSONDecodeError) as e:
        r = _result([str(e)])
    print(json.dumps(r, indent=2, sort_keys=True))
    return 0 if not r['errors'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
