## 2026-10-09 native rental trust UI and Playwright contract extension

On-device managed vs manual, binding and cert pin **read-only** dashboard added to `BlazeAdminActivity.java` (source `5e7e713e27b1487b47abeca8403dbef3041db301`), source privacy test `tests/v060_android_trust_panel.sh` mandatory in Full and fast workflow. HTTPS-only managed QR browser Playwright validates invalid HTTP request is denied and correct HTTPS pinned QR is rendered, with token hidden/reveal semantics (`simulation/browser_v04_audit.py` `cda9ec6b3b707284bd542ec2f29017357f3c196f`). [Fast #37828319441](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/37828319441) PASSED both product-contract and operator-browser jobs. No physical Android or production APK signing evidence. The core P0 money durability and migration remain UNRESOLVED.

# BlazePwifi v0.6.0 — cross-platform competition, product and security audit

**Date:** 2026-10-09 (Asia/Manila). **Status:** design and source-evidence audit, NOT an installed/hardware signoff or permission to publish a production 0.6.0 image. **Working branch:** blazepwifi-v0.6.0-audit-foundation (draft PR #30). **Scope:** OpenWrt, x86/Orange Pi, ESP coin controllers, Windows PisoNet SoftTimer, rental Android Launcher3, Wi-Fi captive portal, administrator console, installation, migration and backups.

## 1. Product definition (restore original intent)

BlazePwifi is ONE server-authoritative, **offline-first** prepaid access/rental platform with **separately installable** network/ESP, Windows and Android components, not a bank ledger or a cloud-only captive portal. It must integrate:

1. **Wi-Fi vendo:** captive portal → device/browser binding → payment window → target-bound coin pulse(s)/voucher → authoritative paid time → nftables access, pause/resume, expiry, retry/ACK, sales reporting; IPv4/IPv6 and captive portal assistance, no offsite service required for local coins.
2. **PisoNet:** one coin slot per PC OR centrally addressed slot, Windows EXE tray/timer/lock/login, USB-serial COM discovery and manual choice; device-admin local escape, robust watchdog, secured server-managed members and credit transfer.
3. **Android rental:** native Launcher3 home/apps, managed lock-task Device Owner mode on factory-reset phones, explicit lower-trust normal APK binding on already configured phones; policy allow/hide, per-device controls, alarms, notifications, time extension, service-managed lease and offline behavior, certificate-pinned binding.
4. **Admin/system:** easy initial setup with auto-discovery and reversible network changes; independent dashboards for Sessions/Sales/Members/Rental/Controllers/WAN/VLAN/Wi-Fi/Portal/Templates/Vouchers/Backups/Security/Remote support/Tools; mobile accessibility; edition tiers so low-flash hardware is not overloaded.
5. **Deployment:** working BIN, IMG.GZ, APK, EXE, INO, installer/bundle and SHA256/manifest; preserves credentials, balances, enrollment secrets and rollback; installability must be actually proven on named hardware.

The above is a **product contract**, not a declaration that every feature is already operating.

## 2. External behavior study — clean-room, documented workflows

Only publicly documented behavior/interface concepts are compared. No access to private systems, closed source, copied assets, unauthorized bypass or proprietary reverse engineering.

| Product/model | What the public documentation establishes | Design pattern BlazePwifi should learn | Differentiator, if implemented and verified |
|---|---|---|---|
| **AdoPiSoft** | Operator-centric PisoWiFi dashboard, sales inventory grouped by dates and by payment portal/subvendo; vouchers include expiry/pause/speed, per-code users and price | Direct, understandable coin→credit UX; simple rates; per-controller sales attribution; operator-focused charts | A single console that also controls native Windows PCs and managed Android rentals; no mandatory cloud for local payments |
| **LPB Piso WiFi** | Prepaid voucher generation/limits and coin-oriented local operator features, supported public documentation varies by distribution | Configurable voucher/rate builder and simple portal with predictable offline behavior | Robust documented backups/migrations and typed centralized controller roles |
| **MikroTik RouterOS HotSpot/User Manager** | Local or RADIUS credentials, portal customization, walled garden, accounting records/limits/quotas | Separate authorization from session accounting; optional standards-based RADIUS integration for non-OpenWrt gateways | Blaze backend controlling multi-platform endpoints without locking operators into RouterOS |
| **Antamedia WiFi Hotspot** | Paid/free guest access, vouchers, quotas, policies, captive UI and analytics, now marketed as cloud platform | Well-structured plan editor, report drilldown, multi-site fleet visibility, transparent quota labels | Local-first sale continuity, low-cost router edition, integration with phone rentals and PisoNet |
| **HandyCafe** | PC access locks, prepaid member wallets/time, remote commands with distinct command IDs and repeat suppression, cashier/session workflows | POS-style accountable corrections/refunds; audit operator identity; idempotent device commands | Wi-Fi + PC + Android consume a shared approved time/credit authority, with safe per-device migration |
| **Antamedia Cafe & Kiosk** | Prepaid vs walk-in pay-after-play, central station/app policy, POS/billing receipts, session dashboards, kiosk modes | Station-centric view and differentiated cashier/administrator roles | One system handles individual/central coin slots, vouchers and device rental together |
| **Headwind MDM / Android Enterprise** | QR/NFC factory-reset fully managed setup, dedicated-device lockdown, Wi-Fi enrollment policies; mere APK install is lower-privilege | Separate Device Owner vs standard binding QR; signer/app checksum; certificate binding; managed lock-task, authorized device owner escape | Offline/local managed rentals tied to same authoritative coin/account backend |

**Authoritative / primary references checked 2026-10-09:**
- AdoPiSoft: https://www.adopisoft.com/ ; sales https://www.adopisoft.com/en/guide/sales-inventory ; vouchers https://www.adopisoft.com/en/guide/vouchers
- LPB: https://lpbpisowifi.com/ (self-described voucher and service features; treat marketing claims as unverified).
- MikroTik: https://help.mikrotik.com/docs/spaces/ROS/pages/56459266/HotSpot%2B-%2BCaptive%2Bportal
- Antamedia Hotspot: https://antamedia.com/hotspot/ ; Cafe & Kiosk https://antamedia.com/cafe-kiosk/
- HandyCafe: https://handycafe.com/cloud (remote commands, replay-safe command IDs).
- Headwind MDM: https://h-mdm.com/kiosk-mode/ ; Android: https://developers.google.com/android/management/provision-device ; https://developer.android.com/reference/android/app/admin/DevicePolicyManager

**Research limits:** no actual commercial-system firmware images, hardware traces or legally obtained protocol captures were inspected. Do NOT claim binary-equivalent compatibility, faster speed or security superiority over these systems from their marketing pages alone.

## 3. Checked repository implementation status and gaps

| Area | Evidenced in current source | Release-blocking/unverified behavior |
|---|---|---|
| Core OpenWrt | /openwrt/rootfs library/CGI/nftables, own auth/CSRF, portal/admin, rollback/initial provisioning, controller interfaces; build matrix | Physical captive-client route success, IPv6/DNS edge cases, unknown OEM revisions, minimum flash/RAM memory profiling |
| Portal | /www/blazepwifi/index.html main Insert Coin/Buy Time/Voucher, remaining-time, separate advanced device details | Real phone CNA/browser edge tests, accessibility/readability, cross-browser latency, 30-client soak |
| Admin | TailAdmin-inspired local CSS, separate BlazeFusion styles, category pages, session trend, rental/member/controllers/remote; existing v0.6 UX branch adds searchable nav and authenticated connection status | CSS design originally static/bland; many UI labels describe intended features but do not establish working backend. Test every button/action against role+CSRF and persistence |
| ESP8266/ESP32 | Dedicated firmware and isolated controller test/build in Full CI | Real pulse timing, noise, queue-on-brownout, multi-controller simultaneity and false-coin fraud; no hardware acceptance |
| Windows PisoNet | Separate \`experiment/windows/BlazePisonet-SoftTimer\` C#/NSIS source, Windows build + serial modules, lock/watchdog/member client | COM/hardware interference, cut-short minute rounding, Ctrl+Alt+Del behavior, actual OEM serial hardware, power loss and 30-station coexistence |
| Android Launcher3 | \`android/BlazeRentalLauncher\` source, Admin receiver, Device Owner policy, allowed/hidden packages, native timer/alarm, stored lease/sync, enrollment & update | Existing installed Device Owner app cannot use unpinned TLS after new guard; actual QR enrollment on OEM setup wizard and signer continuity not validated; lower-security APK cannot enforce same anti-bypass guarantees |
| Rental QR | Distinct \`rental_binding_qr\` vs \`rental_provisioning_qr\`; server requires local TLS pin and signed-channel metadata for managed route; admin policy API | Need signed current/rescue APK with verified Lineage-2 identity and Android provisioning on hardware; missing token custody safeguards and stale modal race addressed in scoped UX code only |
| Paid money | Member event ID retention, 4 MiB quota fail-closed, member/lease receipt EIO quarantines; staged integration tests | **P0: balance/receipt still not one atomic durable transaction**, ordinary account coin history bounded; manually recover uncertain state. Do not advertise perfect replay/physical durability |
| Persistence/updates | Dev source 0.5.3, release v0.5.2 frozen, 0.6 updater intentionally rejects until complete migration; encrypted backups designed | Actual preserve-and-restore of source state/config/admin identities, parent-directory fsync, powercut testing and 0.6 installer acceptance absent |
| Packaging/signing | Full build+Windows green at earlier exact source SHA \`c126781a0097d752590c1fa6793046d554aafb85\`; 0.6 later changes need own CI | Public tag v0.6.0 has not been published; earlier workflows publish only v0.3 by branch conditions, not version 0.6; Android permanent signer and rescue match not proven |

**Evidence quality legend:** \`source present\` != \`build pass\` != \`test pass\` != \`hardware pass\` != \`signed production release\`. Each target must be verified against the exact same commit, not against past SHA.

## 4. Reconciliation architecture to outperform on real metrics

**Server-authoritative universal ledger** (not merely hidden UI): adapter-specific events for Wi-Fi, Windows PC, Android device, voucher, cash/refund, with authenticated controller ID + monotonic sequence (negotiated v2) and atomic durable receipt. Pure UI must never mint time. Restorable revision and conflict handling, bounded storage with non-reusable replay high-water, no silent balance reset.

**Controller abstraction:** coin pulse acquisition runs locally on ESP/Linux/serial adapter; server credit uses stable (controller ID, sequence, target, rate revision) transaction. Offline queue remains local and tamper-evident; ack exactly once after server durable commit. Avoid hardcoded COM1/IP/pins; central slot selects requested station; standard slot binds 1:1.

**Device identity:** 1 user account can have multiple authorized browser/network bindings, Windows station membership or Android rental leases subject to explicit transfer/stacking policy. Random MAC cannot be sole authority; never expose rented-phone secrets in public portal.

**Resilient installers:** capability tiers Lite (small router), Standard (Orange Pi), Full (x86); concrete free-space/RAM/network preflight and staged rollback, *no* automatic upgrades of live finances. Android managed QR requires local pin and app SHA, physical signer and admin recovery. Standard QR advertises lower privilege and does not claim Device Owner.

**UX system:** accessible dark high-contrast information architecture; operational dashboards with truthfully sourced connection/coin/session health, meaningful empty/error/loading states, clear customer coin CTA, offline icon/QR lifetime. No placeholder "live" numbers, no unnecessary video/video-js runtimes on routers, no externally hosted UI code. CoreUI React (5.7.0) and Metis (3.6.0) user archives are MIT, but their full React/Alpine/chart stacks are not transplanted onto Lite; derive original offline styles and credit MIT when incorporating substantial code.

**Competitive acceptance targets (GOALS, NOT ACHIEVED RESULTS):**
- All local payment operations and device policies remain functional with WAN disconnected while local server is up.
- Every payment has a verifiable receipt or an explicit failed/uncertain state. Zero double credits or lost seconds in fault-injection and hardware tests.
- Captive customer path is comprehensible in under three primary actions (Insert Coin, Voucher, Pause/Resume); verify with actual mobile usability testing.
- Admin dashboard clearly shows Wi-Fi sessions, online ESP controllers, assigned Windows stations, rental leases, pending/uncertain transactions and last verified refresh; missing info marked unknown, not 0.
- Installation/rollback evidence on all advertised target hardware revisions; no silently skipped optional targets.
- 30-client mixed-device soak with concurrent coin requests, WAN loss, clock skew and controlled power cut before \`SUCCESS_REPORT=1\`.

## 5. Ordered release gates

1. **P0 financial:** replace containment-only balance/receipt pairs with verified atomic, crash-recoverable, fail-closed real runtime journal for Wi-Fi, member and rental, including account migration/retention and operator reconciliation.
2. **P0 Android:** permanent lineage-2 current+rescue signature verification, true Device Owner provision on supported OEM firmware, normal APK fallback testing, pinned TLS policy and recovery. Never use unverified debug APK as managed release.
3. **P0 install/migration:** read-only inventory, freeze cash acceptance, encrypted verified private snapshot of state/UCI, idempotent schema conversion, restore/forward replay; test power loss at each commit boundary and real reboot. Only then relax 0.6 preflight rejection on safe supported source versions.
4. **P1 function matrix:** all portal/QR/sales/controller/Windows/member actions end-to-end; privilege/CSRF audit, wrong device target, overlapping vended windows, offline handling and real hardware.
5. **P1 UX and performance:** accessible operator console and portal tested at Lite/Standard/Full; mobile browser, keyboard and 30-device load; measure performance instead of asserting faster than competitors.
6. **Release:** version 0.6 source/runtime, signed Android current+rollback matched signing lineage, installable EXE/APK/OpenWrt images/controller INOs, checksum manifest/SBOM/dependency attribution, exact-sha Full+Windows CI + owner-reviewed hardware test log; then publish GitHub \`v0.6.0\` once.

### Decision as of this audit

**Development improvements present, genuine production v0.6.0 NOT RELEASED.** The prior source's \`VERSION\` says 0.5.3, the package manager rejects 0.6, and unresolved P0 paid durability, signer, migration and hardware acceptance make a general public release unsafe. Success cannot be manufactured by changing a green badge or tagging a debug APK.

**Next bounded engineering task:** check targeted new UI/Android pinned-TLS tests and latest build output, reconcile stalled CI, implement real runtime paid journal and reversible migration. Keep source and canonical handover files synchronized at every change, preserving frozen v0.5.2 assets.
