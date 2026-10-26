#!/usr/bin/env python3
"""Create the EasyMode 10 R281 source snapshot and reversible app update."""
import hashlib, json, os, pathlib, re, shutil, sys
from build import tar

BASE = pathlib.Path(__file__).resolve().parents[2]
SOURCE = BASE / 'releases/v4.2.6-r281-consolidated/root'
OUT = BASE / 'releases/v10.0.0-r281'
ROOT = OUT / 'root'
ARCHIVE_DIR = OUT / 'openwrt'
ARCHIVE = ARCHIVE_DIR / 'EasyMode-v10.0.0-R281-app-update.tar.gz'
PRIVATE = [value for value in os.environ.get('EASYMODE_PRIVATE_MARKERS', '').splitlines() if value]

INSTALL = r'''#!/bin/sh
set -eu
cd "$(dirname "$0")"
[ "$(cat /tmp/sysinfo/board_name 2>/dev/null)" = notion,r281 ] || { echo 'Requires verified board notion,r281.'; exit 1; }
[ "$(. /etc/openwrt_release; echo "$DISTRIB_RELEASE")" = 24.10.8 ] || { echo 'Requires OpenWrt 24.10.8.'; exit 1; }
v=$(tr -d '\r\n' </etc/blaze/easymode-version 2>/dev/null || true)
[ "$v" = 4.2.6 ] || [ "$v" = 10.0.0 ] || { echo 'Requires the R281 EasyMode 4.2.6 baseline or v10.'; exit 1; }
for x in tar sha256sum ucode rpcd; do command -v "$x" >/dev/null 2>&1 || { echo "Missing dependency: $x"; exit 1; }; done
sha256sum -c SHA256SUMS
for f in root/usr/libexec/* root/etc/init.d/* root/etc/uci-defaults/*; do
 [ -f "$f" ] || continue
 first=$(head -n1 "$f")
 case "$first" in '#!/bin/sh'|'#!/bin/ash') sh -n "$f";; '#!/usr/bin/ucode') ucode -c -o /tmp/blaze-v10-check.ucb "$f";; esac
done
module_check=/tmp/blaze-v10-module-check.uc
: >"$module_check"; n=0
for f in root/usr/share/blaze/*.uc; do
 [ -f "$f" ] || continue
 if grep -q '^[[:space:]]*export[[:space:]]' "$f"; then
  n=$((n+1));printf "import * as m%s from '%s/%s';\n" "$n" "$(pwd)" "$f" >>"$module_check"
 else
  ucode -c -o /tmp/blaze-v10-check.ucb "$f"
 fi
done
[ ! -s "$module_check" ] || ucode "$module_check"
ucode -c -o /tmp/blaze-v10-check.ucb root/usr/share/rpcd/ucode/blaze
rm -f /tmp/blaze-v10-check.ucb "$module_check"
[ "${1:-}" != --check ] || { echo 'PASS: exact board/release, baseline, dependencies, checksums; no changes.'; exit 0; }
[ "${1:-}" = --apply ] || { echo 'Use --check, then --apply.'; exit 1; }
[ -d root/etc/blaze ] && [ -d root/usr/share/blaze ] && [ -x root/usr/libexec/blaze-health ]
/usr/libexec/blaze-lock-claim job "$$"
umask 077
backup="/root/easymode-before-v10-$(date +%Y%m%d-%H%M%S).tar.gz"
list="/tmp/blaze-v10-files.$$"; missing="/tmp/blaze-v10-missing.$$"
: >"$list"; : >"$missing"
for path in $(find root -type f); do target="${path#root/}"; if [ -f "/$target" ]; then echo "$target" >>"$list"; else echo "$target" >>"$missing"; fi; done
ok=0
finish() {
 if [ "$ok" != 1 ]; then
  while IFS= read -r target; do rm -f "/$target"; done <"$missing"
  [ ! -s "$backup" ] || tar -xzf "$backup" -C /
  /etc/init.d/rpcd restart >/dev/null 2>&1 || true
  /etc/init.d/blaze-health restart >/dev/null 2>&1 || true
  /etc/init.d/blaze-sms-archive restart >/dev/null 2>&1 || true
 fi
 rm -f "$list" "$missing" /tmp/blaze-job.lock/pid /tmp/blaze-job.lock/id
 rmdir /tmp/blaze-job.lock 2>/dev/null || true
}
trap finish EXIT HUP INT TERM
tar -czf "$backup" -C / -T "$list"
tar -tzf "$backup" >/dev/null
# Copy only packaged application files. Runtime UCI and /etc/blaze histories
# are not replaced; this update never writes network/Wi-Fi configuration.
for path in $(find root -type f); do
 target="/${path#root/}";mkdir -p "$(dirname "$target")"
 cp "$path" "$target.v10-new";case "$path" in root/usr/libexec/*|root/etc/init.d/*|root/etc/uci-defaults/*|*.sh) chmod 755 "$target.v10-new";;*) chmod 644 "$target.v10-new";;esac
 mv "$target.v10-new" "$target"
done
for f in /usr/libexec/blaze-health /usr/libexec/blaze-job /etc/init.d/blaze-health /etc/init.d/blaze-sms-archive; do [ ! -f "$f" ] || sh -n "$f"; done
module_check=/tmp/blaze-v10-module-check.uc
: >"$module_check"; n=0
for f in /usr/share/blaze/*.uc; do
 if grep -q '^[[:space:]]*export[[:space:]]' "$f"; then
  n=$((n+1));printf "import * as m%s from '%s';\n" "$n" "$f" >>"$module_check"
 else
  ucode -c -o /tmp/blaze-v10-check.ucb "$f"
 fi
done
[ ! -s "$module_check" ] || ucode "$module_check"
ucode -c -o /tmp/blaze-v10-check.ucb /usr/share/rpcd/ucode/blaze
rm -f "$module_check" /tmp/blaze-v10-check.ucb
chmod 644 /www/index.html /www/easy/app.js /www/easy/core.js /www/easy/style.css /www/easy/refined.css
/etc/init.d/rpcd restart
/etc/init.d/blaze-health restart
/etc/init.d/blaze-sms-archive enable >/dev/null 2>&1 || true
/etc/init.d/blaze-sms-archive restart >/dev/null 2>&1 || true
ok=1
echo "Installed EasyMode v10.0.0 application. Backup: $backup. No network reload or reboot."
'''

README = '''# EasyMode v10.0.0 — R281 application profile

This source snapshot recreates the EasyMode application currently installed on the verified Notion R281, including SMS, cellular controls, bands, Wi-Fi, repeater, ports/VLAN, device filtering, sessions, and Traffic Intelligence navigation. Version 10 is a product revision label; it does not imply universal hardware support.

## Install on the verified R281

The archive is an application update, not firmware. It supports only `notion,r281` running OpenWrt 24.10.8 and EasyMode 4.2.6 or v10. Run `./install.sh --check`, then `./install.sh --apply`. The script backs up replaced files, preserves UCI/network/Wi-Fi settings and SMS histories, and does not reboot or reload networking. Roll back by extracting the printed `/root/easymode-before-v10-*.tar.gz` archive and restarting rpcd/EasyMode services.

## Other OpenWrt devices

The R281 application contains modem, switch-port, antenna, and repeater integrations that are specific to this board and its installed packages. The installer refuses other boards. For other devices, use the shared capability-detected Traffic Intelligence edition under `traffic/`; that does not reproduce every R281 management feature. A unified cross-device control profile and hardware-specific validation are still required before claiming the same complete experience on arbitrary OpenWrt hardware.

## Reset and firmware limits

An application installed into `/overlay` is erased by a factory reset. Hard-reset persistence requires these files and defaults to be built into a board-compatible firmware image under `/rom`. This release contains no R281 flashable image and does not claim reset-proof behavior. Back up configuration and SMS archives before reset or firmware replacement.

See `AUDIT.md`, `HANDOFF.md`, `SOURCE-MANIFEST.json`, and `SHA256SUMS`. No live logs, credentials, SMS, or SIM identity records are included.
'''

AUDIT = '''# R281 log audit — 2026-10-19

Collected current `logread`, `dmesg`, health history, network interface state, routes, process/memory state, and cellular/Wi-Fi status over authenticated SSH. Raw diagnostics are kept on the operator workstation only and are not included in this release.

The router was on OpenWrt 24.10.8, uptime 16h37 at collection, with 30,252 KiB `MemAvailable`, 90,624 KiB overlay free, and LTE on `eth1`. The current cellular health state was online, route present, and ping probe successful. `logread` contained 998 entries; current-boot kernel logs showed no modem USB reset/error or memory exhaustion event.

Health history contains 51 failed samples across this boot, including a six-sample failure burst ending around 07:49 PHT; two reconnect attempts had occurred. The data interface was subsequently up and successful again. The available system log did not identify the underlying carrier-side cause or record a radio detach for that burst. This warrants longer monitoring; it does not prove tower fault, SIM lock, or a specific app-triggered outage.

Older outage captures show repeated cellular DHCP renewal requests with no renew reply, followed by lease expiry and immediate reacquisition of the same private IPv4 address. `netifd` then raised the dynamic interface and reloaded the firewall. This is a short DHCP transition, not evidence that the carrier rotated the address during that event. A separate earlier packet capture of renewal behavior did not establish a workaround; no static addressing or DHCP suppression was introduced.

Candidate fixes: (1) remove the stale high-priority EasyMode unreachable default route when no source has an address, allowing normal netifd routes to work as soon as a lease returns; (2) automatic SIM recovery now reconnects the data session only and never cycles RF/changes cell selection. Cellular IP changes are counted per boot in health status so future outages can be correlated without recording browsing data or full IP-change history.

The v10 application was installed on the verified R281 after a private rollback archive was created. `/etc/blaze/easymode-version` reports `10.0.0`; the root page identifies v10.0.0; JavaScript and CSS assets return HTTP 200; health and SMS-archive services are running; SIM ping passed immediately after installation. The SIM address and route remained available. No reboot, radio reset, network/Wi-Fi config edit, or firmware flash occurred. The backup is `/root/easymode-before-v10-20261019-081032.tar.gz`.

Validated against the running router: shell syntax, four mocked health-routing/recovery regression cases, module/script syntax and import checks, exact-board/release installer preflight, plus post-install version/homepage/assets/services and read-only SIM probe checks. No full per-file readback/hash comparison was performed. Long-term stability, hardware reset persistence, and other boards remain unverified.
'''

HANDOFF = '''# EasyMode v10.0.0 handoff

- Source: this directory, copied from `releases/v4.2.6-r281-consolidated/root` and updated to v10.0.0.
- Reference target: verified Notion R281 (`notion,r281`), OpenWrt 24.10.8, kernel 6.6.144.
- Current runtime after deployment: EasyMode 10.0.0 on the verified R281; online cellular interface; 30,252 KiB MemAvailable at the pre-install audit; 90,624 KiB free overlay before the package backup.
- Confirmed recovery issue and candidate fixes are in `AUDIT.md` and `root/usr/libexec/blaze-health`.
- Regression tests: `traffic/tests/health-routing.sh`; executed on the R281 against the candidate copied to `/tmp`. Installer `--check` passed on the exact target before applying.
- Build: `python traffic/tools/build-r281-v10.py`; package is `openwrt/EasyMode-v10.0.0-R281-app-update.tar.gz`.
- Installer preflight is exact-board and exact-release gated. It preserves UCI, network/Wi-Fi settings, and private `/etc/blaze` data. No reboot is requested.
- Live installation verified: EasyMode version file 10.0.0, root page version marker, JS/CSS HTTP 200, health and SMS archive services active, and SIM ping passed after installation. Backup: `/root/easymode-before-v10-20261019-081032.tar.gz`. No reboot or network config change. A complete per-file source-to-device hash comparison was not run.
- Not complete: extended stability observation, hardware reset persistence, R281 firmware build, or universal parity on other hardware. The app archive is not firmware.
- Private current router logs and collected state remain outside GitHub.
'''

def main():
    if not SOURCE.is_dir(): raise SystemExit(f'Missing source {SOURCE}')
    if OUT.exists(): shutil.rmtree(OUT)
    shutil.copytree(SOURCE, ROOT)
    for f in ROOT.rglob('*'):
        if not f.is_file(): continue
        data=f.read_bytes()
        if b'\0' not in data:
            try: data.decode('utf-8')
            except UnicodeDecodeError: continue
            f.write_bytes(data.replace(b'\r\n',b'\n').replace(b'\r',b'\n'))
    replacements = {
        'etc/blaze/easymode-version': None,
        'www/index.html': [('4.1.0','10.0.0'),('4.2.6','10.0.0')],
        'www/easy/app.js': [('4.2.6-sms2','10.0.0'),("const EASY_VERSION='4.2.6'","const EASY_VERSION='10.0.0'"),('EasyMode 4.1','EasyMode 10.0')],
        'usr/share/rpcd/ucode/blaze': [("||'4.1.0'","||'10.0.0'")],
    }
    for rel, rules in replacements.items():
        f=ROOT/rel
        if rules is None: f.write_text('10.0.0\n',encoding='utf-8',newline='\n');continue
        s=f.read_text(encoding='utf-8')
        for old,new in rules:
            if old not in s: raise SystemExit(f'Expected version marker {old!r} absent in {rel}')
            s=s.replace(old,new)
        f.write_text(s,encoding='utf-8',newline='\n')
    payload={}
    for f in sorted(ROOT.rglob('*')):
        if f.is_file():
            rel=f.relative_to(OUT).as_posix()
            data=f.read_bytes()
            for secret in PRIVATE:
                if secret.encode() in data: raise SystemExit(f'Private value found in {rel}')
            mode=0o755 if ('/libexec/' in '/'+rel or '/init.d/' in '/'+rel or '/uci-defaults/' in '/'+rel) or rel.endswith('.sh') else 0o644
            payload[rel]=(data,mode)
    payload['install.sh']=(INSTALL.encode(),0o755)
    payload['README.md']=(README.encode(),0o644)
    payload['AUDIT.md']=(AUDIT.encode(),0o644)
    payload['HANDOFF.md']=(HANDOFF.encode(),0o644)
    manifest={'version':'10.0.0','kind':'R281 app update; not firmware','board':'notion,r281','openwrt':'24.10.8','files':[]}
    for name,(data,mode) in sorted(payload.items()):
        manifest['files'].append({'path':name,'mode':format(mode,'04o'),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    payload['SOURCE-MANIFEST.json']=(json.dumps(manifest,indent=2)+'\n').encode(),0o644
    payload['VERSION']=(b'10.0.0\n',0o644)
    sums=''.join(hashlib.sha256(d).hexdigest()+'  '+n+'\n' for n,(d,_) in sorted(payload.items()))
    payload['SHA256SUMS']=(sums.encode(),0o644)
    ARCHIVE_DIR.mkdir(parents=True,exist_ok=True)
    (OUT/'README.md').write_text(README,encoding='utf-8',newline='\n')
    (OUT/'AUDIT.md').write_text(AUDIT,encoding='utf-8',newline='\n')
    (OUT/'HANDOFF.md').write_text(HANDOFF,encoding='utf-8',newline='\n')
    (OUT/'SOURCE-MANIFEST.json').write_bytes(payload['SOURCE-MANIFEST.json'][0])
    ARCHIVE.write_bytes(tar(payload))
    (ARCHIVE.with_suffix(ARCHIVE.suffix+'.sha256')).write_text(hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()+'  '+ARCHIVE.name+'\n',encoding='ascii')
    print(f'PASS: EasyMode v10.0.0 R281 payload: {len(payload)} files; archive {ARCHIVE.stat().st_size} bytes')

if __name__=='__main__': main()
