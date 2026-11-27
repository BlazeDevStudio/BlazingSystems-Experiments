# BlazePwifi v0.3 Implementation Plan

Spec: `docs/superpowers/specs/2026-10-04-blazepwifi-v0.3-design.md`
Execution: inline, isolated GitHub development branch
Base: `main@9cc8f110ed7b29c06275932444182d5ccff83930`

## Global constraints

- Preserve v0.2 accounting/replay/durability behavior unless a test proves the replacement equivalent or stronger.
- Keep constrained routers Lite: no heavy JS framework, Android fleet DB, charting library, or full WYSIWYG runtime in router images.
- Standard/Full may use the MIT Tabler admin UI; do not bundle ApexCharts or other optional non-MIT/redistribution-sensitive plugins.
- Remove the prohibited commercial vendor name and supplied host URL from public BlazePwifi source/docs/history-facing files modified by v0.3.
- All user-adjustable deployment values live in configuration/profile data, not production source constants.
- No universal production password/secret.
- Build against OpenWrt 25.12.5.
- Publish only successful artifacts. No dummy APK/BIN/IMG/ISO placeholders.

## Task 1 — Publication scrub, version and capability foundation

Files: `VERSION`, `README.md`, `CHANGELOG.md`, `docs/REFERENCE_NOTES.md`, remove old reconciliation doc, `openwrt/rootfs/etc/config/blazepwifi`, new `usr/lib/blazepwifi/capabilities.sh`, tests.

Tests first: prohibited-string scan; config has capability tier and no production default secrets; capabilities resolve lite/standard/full.

## Task 2 — Admin auth/session/lockout core

Files: `common.sh`, new `auth.sh`, CGI admin/login/logout/session endpoints, state dirs, tests.

Implement salted password hashes where platform tools permit, one-time bootstrap secret, IP+account lockouts, exponential delay/lock periods, random session IDs, CSRF, idle/absolute expiry, Admin/Operator/Viewer ACL format, audit log. RAM counters with durable audit.

Tests: successful login, bad login, lockout, expiry, logout invalidation, CSRF, role denial, no WAN listener assumptions.

## Task 3 — Configuration API and safe apply

Files: config CGI/module, installer, validation helpers, network schema docs/tests.

Implement validated configurable ports, rates, VLAN/interface roles, controller network, management network, portal fields, GPIO/profile settings. Stage/validate/commit with rollback marker; never hardcode NIC names.

## Task 4 — Portal renderer + Lite builder

Files: portal renderer, `portal.json`, compact CSS, admin portal-editor page, preview endpoint, tests.

First viewport: brand, status/time/balance, large Insert Coin / Buy Time / Voucher actions, rate cards. Below fold: device name/token suffix, IP/MAC where appropriate, gateway, signal if known, session state, DNS/gateway and non-sensitive connectivity stats. No secrets or invasive fingerprinting.

## Task 5 — Standard/Full Tabler admin shell

Files: vendored minimal Tabler MIT assets + license notice, dashboard layout, capability-gated loader.

Use Tabler core only; omit ApexCharts/plugins. Lite uses compact native shell; Standard/Full use richer responsive dashboard.

## Task 6 — Static portal template gallery

Files: `portal-templates/` gallery and required preview pages, template JSON, README, preview routing.

Tests: every required screen linked, static preview contains no live API dependency.

## Task 7 — Controller protocol abstraction

Files: shared protocol docs/server helpers; migrate existing ESP8266 naming/config fields without changing money semantics.

Tests: target-bound signature, idempotency, heartbeat, configurable pulse/polarity settings.

## Task 8 — ESP32 controller

Files: `esp32/BlazePwifiVendo32/*.ino`, README, CI compile matrix.

Use Preferences/NVS for small config, LittleFS pending-event journal, temporary WPA2 setup AP, same protocol as ESP8266.

## Task 9 — Linux GPIO/Orange Pi agent

Files: `linux-agent/`, procd service, profile JSON/uci, tests.

Use libgpiod/gpiomon/gpioset; configurable gpiochip+line/polarity/debounce; durable one-pending-event journal.

## Task 10 — Orange Pi profile/build matrix

Priority: Zero 3, One, PC. Additional: PC Plus, PC2, Zero, Zero2W, One Plus, R1 when upstream profile exists.

Files: target manifest/build scripts/workflow docs.

Build only upstream-supported 25.12.5 profiles. Keep known WLAN limitations documented and never claim unsupported WLAN works.

## Task 11 — x86 Full target

Files: build scripts/setup UI/docs/tests.

Produce x86/64 ext4+squashfs BIOS/UEFI. Enumerate NICs rather than assume `eth0`. Add installer ISO only if reproducible bootable ISO pipeline passes.

## Task 12 — BlazeRental Android DPC

Files: Android Gradle project package `com.blazesystems.blazerental`, DPC receiver, lease service/client, launcher UI, provisioning generator, tests.

Managed mode: factory-reset QR Device Owner provisioning, lock-task allowlist, boot recovery, server-authoritative lease, one-time enrollment token, policy restrictions supported by API/OEM. Manual APK mode: visibly weaker; no false Device Owner claims.

## Task 13 — QR provisioning artifacts

Files: deterministic provisioning JSON generator, QR PNG build step, docs/tests.

QR includes DPC component/package, APK location/hash and one-time enrollment extras without committing a real secret.

## Task 14 — Release tree and GitHub Release automation

Files: `releases/0.3.0-rc.1/`, `ASSETS.md`, `manifest.json`, release workflow.

Collect successful APK, INO, BIN, IMG.GZ, TAR.GZ, ZIP, provisioning JSON/PNG, portal archive, checksums and SBOM where available. Release folder indexes large GitHub Release assets rather than duplicating binaries in git.

## Task 15 — Documentation and installation guide

README and docs: pin/profile examples, electrical isolation warning, VLAN examples, first admin bootstrap, recovery, Ruijie, Orange Pi SD imaging, x86 BIOS/UEFI, ESP flashing, Android QR/manual install, backup/restore, checksums.

## Task 16 — Final security/build/release verification

Run static/integration/stress/security/portal tests; compile ESP8266/ESP32; build Android release APK; build Ruijie, Zero3, One, PC, x86 BIOS/UEFI; optional targets only if green. Scan public tree for prohibited references/secrets. Generate checksums/manifests. Publish prerelease assets only after checks succeed.

## Review focus

- lost-credit or duplicate-credit regressions under reboot/concurrency;
- auth bypass/lockout bypass/CSRF/session fixation;
- management exposure to WAN/hotspot clients;
- unsafe portal custom-content injection;
- Device Owner provisioning assumptions across Android versions;
- Orange Pi profile mismatch and GPIO line ambiguity;
- build scripts silently publishing wrong-board images;
- asset manifest/checksum mismatch;
- constrained-router flash/RAM growth beyond Lite budget.
