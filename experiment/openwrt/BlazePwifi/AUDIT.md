## v0.6.0 whole-product risk-based audit (2026-10-09)

Full platform/competitor/feature coverage and open gates: [docs/V060_COMPETITIVE_SYSTEM_AUDIT.md](docs/V060_COMPETITIVE_SYSTEM_AUDIT.md). Below sections preserve historical v0.2 audit results; they are not evidence of a signed v0.6 production release. Current state in PROJECT_HANDOVER and docs/handover/CURRENT_STATE. v0.6 SAFE RELEASE=0 until paid crash atomicity, migration, Android signing and real hardware acceptance.

# BlazePwifi production-readiness audit

Release candidate: 0.2.0-rc.2

## Audit scope

The audit covers the OpenWrt runtime, captive portal/API, nftables enforcement, persistent accounting, Vendo protocol, ESP8266 firmware, installer/upgrade path, first-boot provisioning, ImageBuilder pipeline, and CI tests.

## Findings fixed in v0.2

| Finding | Risk | Resolution |
|---|---|---|
| MAC-only account identity | Private/random MAC could lose purchased time | Persistent 128-bit browser device token; MAC is now a replaceable network binding |
| Coin ACK loss | Retry could double-credit | Stable ESP event nonce plus server idempotency marker |
| Coin event reusable for another customer | Credit theft/replay | Signature includes active coin-window target nonce |
| Voucher marker shared bounded coin history | Old voucher could eventually become reusable | Voucher markers are retained; only coin markers are bounded |
| Vendo heartbeat persisted every poll | Excessive flash writes | Online Vendo state moved to /tmp |
| Coin target only in RAM | Router brownout could orphan a physically inserted coin | Short coin-window records are persisted atomically; expired targets are cleaned automatically |
| Blaze gate ran before normal firewall4 forwarding | Policy ordering ambiguity | Blaze forward hook moved to priority 10, after firewall4 |
| No payment walled garden | E-payment portals unusable without session | Dynamic IPv4/IPv6 walled garden added |
| Admin token on HTTP | Local token disclosure risk | HTTPS-only admin listener on LAN address |
| ESP setup AP was open | Nearby reconfiguration risk | Per-device WPA2 password plus AP auto-shutdown |
| v0.1 MAC state had no migration path | Upgrade could orphan balances | One-time MAC-to-device-token claim migration |
| Cross-filesystem temp files | `/tmp` → `/etc` move was not a guaranteed atomic rename | Persistent account/voucher/target temp files now stage on the state filesystem |
| Stale/racy global lock | Crashed or concurrent CGI could wedge or overlap accounting | Kernel `flock` serializes writers and is automatically released on process exit |
| Zero-balance visitors persisted | Account file could grow from casual portal views | Read-only visits stay non-persistent until a money/session action |
| ESP/router brownout during coin ACK | Coin could be lost or duplicated | Durable router target + ESP LittleFS event journal + idempotent server marker |
| Runtime scripts stored non-executable | Direct-flash image could boot with unusable service/CGI files | Git executable modes are audited and re-applied before release |
| Local services behind restrictive zone | Portal/Vendo/admin could be unreachable | Installer creates explicit rules on configured local firewall zone only |
| Firmware artifacts lacked local checksum/install image | Deployment integrity/install gap | Per-target SHA256SUMS plus Ruijie initramfs+sysupgrade and x86 BIOS+EFI checks |

## Automated gates

1. Static shell/hardening and executable-mode validation.
2. Accounting integration test, repeated three times per release run.
3. Persistence/replay/migration/concurrency stress test, repeated three times per release run.
4. ESP8266 NodeMCU compilation.
5. OpenWrt 25.12.5 Ruijie RG-EW1200G Pro v1.1 ImageBuilder.
6. OpenWrt 25.12.5 x86_64 ImageBuilder.
7. Release bundle and SHA-256 artifacts.

## Remaining physical validation before calling a specific appliance field-proven

- Flash and recover an actual RG-EW1200G Pro v1.1.
- Measure actual coin-acceptor pulse polarity, width and debounce requirements.
- Verify relay/LED GPIO electrical levels with the chosen ESP8266 board.
- Real power-cut testing during coin acknowledgement, ESP flash journaling and router state replacement (software-level reboot/tmpfs-loss paths are covered automatically).
- Sustained multi-client traffic and portal load.
- Real captive-portal behavior on Android, iOS, Windows and ChromeOS.
- Real e-payment provider flows for any configured walled-garden domain list.
- WAN/LAN/VLAN topology used by the intended installation.

The codebase is treated as a release candidate until those hardware/site tests are complete.

---

# v0.6.0 multi-platform research and release-blocking audit (2026-10-08)

**State:** development / audit candidate, **NOT v0.6.0 production signed or released**. This section updates the historical v0.2 audit above instead of rewriting its provenance.

## Method and limitations

Review used source inspection of this repository (server shell CGI, nftables accounting, ESP firmware and tests, native Android Launcher3/DPC, separate Windows BlazePisonet SoftTimer), official/documented vendor behavior, and upstream Android/OWASP security guidance. This is **behavioral compatibility research**, not decompilation or copying proprietary software. A completed automated build does not prove electrical pulse timing, watchdog survival, Device Owner enrollment on every OEM, or performance under 30+ devices.

Primary public references, checked 2026-10-08:
- JuanFi: https://github.com/ivanalayan15/JuanFi — ESP wireless/LAN vendo controllers, multi-vendo, paused expiration, abuse prevention, vouchers.
- JuanFi documentation: https://juanfi.juansystems.com/ — coin, bill acceptor, pause/extend, auto-relogin.
- AdoPiSoft: https://www.adopisoft.com/en/guide/wifi-rates — rate plans, time/data quotas, limits on empty coin-window attempts.
- MikroTik User Manager: https://help.mikrotik.com/docs/spaces/ROS/pages/2555940/User%2BManager — RADIUS profiles, voucher generation and session accounting.
- OpenNDS: https://openwrt.org/docs/guide-user/services/captive-portal/opennds — captive token authorization and external authenticators.
- Antamedia Cafe & Kiosk: https://antamedia.com/cafe/ — managed PC stations, staff roles, POS, session/billing reporting.
- TrueCafe: https://www.truecafe.net/doc/session.html — prepaid/postpaid PC session semantics.
- HandyCafe: https://handycafe.com/features — offline-first PC floor, multi-OS client/server, remote assistance, QR member login.
- Android: https://developer.android.com/work/dpc/dedicated-devices/lock-task-mode — lock task depends on Device Owner / allowed app management.
- Android AMAPI provisioning: https://developers.google.com/android/management/provision-device — provisioning extras + APK certificate/hash.
- OWASP: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html — protect session tokens, cookies, CSRF, revocation.

These sources describe different products; don't infer their hidden implementation details from marketing copy.

## Actual architecture and competitive gaps

| Surface | Current code / behavior observed | v0.6.0 target | Verification required |
|---|---|---|---|
| OpenWrt router / x86 / Orange Pi | Persistent prepaid accounts, vouchers and coin targets; nftables MAC access; per-vendo pulses and event IDs | Capability-aware WAN/VLAN/USB routing, stronger anonymous client binding, accounting metrics | packet captures; NAT/IPv6 bypass tests; wired/wireless bridge migrations |
| ESP8266 / ESP32 | Signed shared-key protocol, heartbeat, durable pulse journal, parallel target windows | bounded offline queue and idempotent replay, controller health telemetry | coin pulse electrical testing, outage/reboot/mid-ACK recovery |
| Windows BlazePisonet SoftTimer (separate repository subtree) | .NET Windows EXE, COM auto/manual/exact device, centralized vs local modes, member sync, keyboard/mouse restrictions | monotonic timer correctness, reliable central offline-state semantics, workstation controls | Windows CI with timer regression, serial-device simulation, 10+ PC load |
| Android BlazeRental native Launcher3 | Rental left panel, coin window, paid-state enforcement, native admin, Device Owner / lock task, periodic server HMAC leases | visually coherent native customer/admin flows; heartbeat/device status; robust allowed-app changes | signed APK and DPC provisioning on freshly reset OEMs; non-owner bypass disclosure |
| BlazePwifi admin console | HTML/JS separate role-gated HTTPS admin, CSRF/session, voucher/rental/network controls; update metadata | coherent operator dashboard, plain-language status, explicit security-tier provisioning, role-scoped operations | authenticated browser, keyboard/phone sizes, CSRF and XSS regression |
| Provisioning and binding | Server distinct `rental_binding_qr` and `rental_provisioning_qr`; signed APK checksum in Device Owner payload | explicit mode choice and expiring QR display; no secret in browser after closing; verify cert pin | factory setup wizard vs existing-app QR scans with real devices |
| Multi-location / remote | ZeroTier/WireGuard and authorization gates; no cloud needed for local operations | optional remote observability WITHOUT WAN-open admin | VPN ACL, reconnect/replay, peer disconnect, backup audit |

## Defects found / current patch state

**P0, confirmed from source:** `experiment/windows/BlazePisonet-SoftTimer/src/BlazePisonet.SoftTimer/TimerEngine.cs` used a 250-ms callback and subtracted `Math.Max(1,floor(elapsed))`; a normally scheduled callback debited one whole second for ~0.25 elapsed seconds. *Patch committed on this development branch:* Stopwatch monotonic accumulation and fractional carry. Requires Windows build, randomized cadence regression and a sustained physical 60-minute check; not yet verified.

**P1, confirmed source trust-boundary weakness:** public `cgi-bin/api` fell back to `bp_param mac` when `ip neigh` could not resolve the MAC. Network identity cannot be proven by a self-declared field. *Patch committed:* reject claim and do not open coin window or migrate session; integration regression added. Must verify ARP/ND across VLAN13 hybrids and bridged Wi-Fi; no auto-trust of query MAC permitted.

**P1, confirmed incomplete validation:** rental APK update channel validation previously only checked `https://` prefix plus length/whitespace. *Patch committed:* reject absent authority, fragment, embedded credentials and backslash. The Android app's permanent signer/hash checks remain necessary: URL syntax validation alone is not security.

**P2, confirmed stale UI state:** admin sidebar referenced v0.5.1 while full candidate is v0.5.3, and updater forms supplied older release defaults. *Patch committed:* v0.6 preview badge and blank update metadata when server has no published APK.

**P2, confirmed QR UX issue:** browser-rendered one-time enrollment QR remained displayed indefinitely past its 600-second lifetime and after modal close. *Patch committed:* expire QR locally and clear token on close. Server-side token expiry and single-use enforcement remain authoritative.

**P2, confirmed UX debt:** Android device-rental and admin activities use programmatic native views but minimal visual hierarchy; HTML management console used stale plain cards. *Patch committed:* themed native rental state card and native admin controls, plus operator console responsive design and distinct QR method cards.

### Further risks needing verification, not claims of exploitation

- Random-MAC changes and `bp_bind_device` automatically migrating the browser token to a new MAC could enable a disclosed token to move a paid session; model device recovery, tokens, transfers and limited grace properly before restricting legitimate users.
- Router neighbor identity may be missing for routed VLAN, multi-bridge, IPv6-only or clients behind AP/router NAT. Fail closed is safer but could break those topologies until authentic identity mapping is implemented. The test suite covers a stub ARP neighbor, not real VLAN13 hardware.
- Windows reboot/disconnect/suspend behavior needs an explicit source-of-truth policy: local prepaid time vs remote authoritative time vs banked member credit. Guard wall-clock changes and double spending after replay.
- The SoftTimer communicates over a local HTTP vendo link secured by a shared secret rather than transport TLS; review physical LAN threat model, secret rotation and packet replay.
- Android Device Owner can restrict approved apps and use lock task, but cannot provide absolute protection against physical recovery/wipe, unsupported OEM builds, or hardware compromise. Standard binding mode is **not** equivalent to Device Owner enrollment.
- The admin credential reset/recovery workflows and Standalone Rental have separate release trains. Do not overwrite their state, signer or assets to speed a full BlazePwifi release.
- Extend request-size limits, controller per-source rate limits, exact one-time financial event ledger, signed backup restore and idempotent retry testing.

## Competitive performance acceptance (measure, never fabricate)

Before asserting v0.6 outperforms named systems, run the **same machine, network, and paid workload** for:
1. 30 clients + concurrent coin/rental/accounting operations; record p50/p95/p99 API latency and CPU/memory.
2. 24h real coin pulse soak with 0 duplicate/lost credits across restart, clock change, power cuts and reconnects.
3. End-to-end Windows 60-minute prepaid test, pause/resume, centralized one-slot-to-many-PC and one-to-one mode; expected `60m ± 1s` excluding suspend policy.
4. Android owner QR from true factory setup and distinct in-app binding QR, with allowed-app settings after restart.
5. Complete data export/import/rollback/recovery drill, checking no cross-version account corruption.
6. Mobile 360px, tablet, desktop dashboard usability, keyboard navigation, color contrast, motion reduction, and offline UI.
7. Same-signer verification for each Android APK and separate rescue; never rotate signing keys.

## v0.6.0 release gate / migration blockers

- Branch `blazepwifi-v0.6.0-audit-foundation` is **development**, sourced from the signed-release-independent 0.5.3 security fix; its VERSION and existing signing workflows are still v0.5.3. **Do not tag v0.6.0 from this state.**
- Add explicit 0.5.x → 0.6.0 persistence migrations and rollback tests; review expected config, control API and lease protocol compatibility with existing deployed clients.
- Implement a v0.6.0 build matrix with validated exact-SHA `CANDIDATE-GATE.json`, Android versionCode increment, Windows installer artifacts, ESP builds, Ruijie/x86/Orange Pi target sets and simulations.
- Run full tests on merge SHA after security reviews. Build and sign with permanent Lineage-2 certificate, verify signatures of new APK and rollback rescue, then stage release manifest, checksums and both types of QR setup assets.
- Publish production only after reproducible green CI, signed release-stage QA, and physical operator acceptance. This document does not authorize publication or claim field-proven bypass resistance.
