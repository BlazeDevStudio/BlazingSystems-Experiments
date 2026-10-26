#!/usr/bin/env python3
"""Create a credential-free LuCI backup archive for the verified R281 runtime.

OpenWrt restores these relative paths to /; uci-defaults enables services on
the next boot. This is an overlay restore, not factory-reset persistence.
"""
import argparse
import gzip
import hashlib
import io
import json
import pathlib
import tarfile

BASE = pathlib.Path(__file__).resolve().parents[1]
APP = BASE / 'releases/v10.2.0-r281-candidate/root'
TRAFFIC = BASE / 'traffic/root'
APP_MANIFEST = json.loads((BASE / 'releases/v10.2.0-r281-candidate/SOURCE-MANIFEST.json').read_text())
APP_MODES = {x['path'].removeprefix('root/'): int(x['mode'], 8) for x in APP_MANIFEST['files'] if x['path'].startswith('root/')}
STARTUP = b'''#!/bin/sh
[ "$(cat /tmp/sysinfo/board_name 2>/dev/null)" = notion,r281 ] || exit 0
. /etc/openwrt_release
[ "$DISTRIB_RELEASE" = 24.10.8 ] || exit 0
if ! uci -q get blaze.main >/dev/null 2>&1; then
 uci set blaze.main=main
 uci set blaze.main.watchdog_enabled=0
 uci set blaze.main.watchdog_reboot_enabled=0
 uci commit blaze
fi
if ! uci -q get easymode_traffic.main >/dev/null 2>&1; then
 uci set easymode_traffic.main=main
 uci set easymode_traffic.main.edition=cellular
 uci set easymode_traffic.main.enabled=1
 uci set easymode_traffic.main.devices=1
 uci set easymode_traffic.main.domains=0
 uci commit easymode_traffic
fi
for service in blaze-access blaze-health blaze-quality blaze-sites blaze-sms-archive easymode-traffic; do
 [ ! -x "/etc/init.d/$service" ] || "/etc/init.d/$service" enable
done
exit 0
'''

def files():
    result = {}
    for source, base in ((APP, APP), (TRAFFIC, TRAFFIC)):
        for path in source.rglob('*'):
            if not path.is_file():
                continue
            name = path.relative_to(base).as_posix()
            if name == 'etc/config/easymode_traffic':
                continue  # Preserve the restored router's own monitoring settings.
            if name.startswith(('etc/config/', 'etc/dropbear/')):
                raise ValueError('Refusing a configuration or identity file: ' + name)
            if name in result:
                raise ValueError('Duplicate archive path: ' + name)
            mode = APP_MODES[name] if source == APP else (0o755 if '/init.d/' in '/'+name or '/libexec/' in '/'+name or '/uci-defaults/' in '/'+name else 0o644)
            result[name] = (path.read_bytes(), mode)
    result['etc/uci-defaults/99-easymode-restore'] = (STARTUP, 0o755)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=pathlib.Path)
    args = parser.parse_args()
    entries = files()
    scan = b'\n'.join(data for data, _ in entries.values())
    if any(token in scan for token in (b'-----BEGIN PRIVATE KEY-----', b'-----BEGIN OPENSSH PRIVATE KEY-----')):
        raise SystemExit('Sensitive content detected; archive not built.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0, filename='') as gz, tarfile.open(fileobj=gz, mode='w') as archive:
        for name, (data, mode) in sorted(entries.items()):
            item = tarfile.TarInfo(name)
            item.uid = item.gid = 0
            item.uname = item.gname = 'root'
            item.mode = mode
            item.mtime = 0
            item.size = len(data)
            archive.addfile(item, io.BytesIO(data))
    with tarfile.open(args.output, 'r:gz') as archive:
        found = {member.name for member in archive}
        if found != set(entries):
            raise SystemExit('Archive path verification failed.')
        for member in archive:
            data, mode = entries[member.name]
            if member.mode != mode or archive.extractfile(member).read() != data:
                raise SystemExit('Archive readback failed: ' + member.name)
    print(f'PASS: {len(entries)} credential-free files; SHA256 {hashlib.sha256(args.output.read_bytes()).hexdigest()}')

if __name__ == '__main__':
    main()
