# Project Phoenix — Canonical Role Assignments & Directory Ownership

**Protocol Specification:** BLAZE-COMMS/1  
**Exact source routing authority:** [OWNERSHIP_ROUTES.json](OWNERSHIP_ROUTES.json) and [REPOSITORY_ROUTING.md](REPOSITORY_ROUTING.md). Broad root paths below do not grant ownership of unrelated products.  
**Team Topology:** FULL (7 CHATS) TEAM  
**Governing Issue:** [#172 — [PHX] CONTROL PLANE](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)  
**Cleanup Gate Issue:** [#266 — [PHX] Code-cleanup-first gate across seven developer roles](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  

---

## 1. Full 7-Role Ownership Table

| Role ID | Role Title | Primary Branch Suggestion | Owned Directory / File Scope | Key Upstream Dependencies | Key Downstream Consumers |
|---|---|---|---|---|---|
| **PHX-MASTER** | Master Auditor / Integration Coordinator | `phoenix/master-coordination` | `coordination/phoenix/`, architecture contracts, release gates | All Roles | All Roles |
| **PHX-CORE** | BlazePwifi Core / Financial Authority Engineer | `phoenix/core-finance` | `experiment/openwrt/BlazePwifi/openwrt/rootfs/usr/lib/blazepwifi/` and `.../rootfs/www/blazepwifi/cgi-bin/vendo`, financial schema | PHX-MASTER | PHX-RENTAL, PHX-PISONET, PHX-QA |
| **PHX-RENTAL** | BlazeRental Android / Rental Server Engineer | `phoenix/rental-android` | `experiment/openwrt/BlazePwifi/android/`, `experiment/openwrt/BlazePwifi/profiles/standalone-rental/`, `experiment/openwrt/Rental-Server-Standalone/` (not root `android/`) | PHX-CORE, PHX-MASTER | PHX-QA, PHX-RELEASE |
| **PHX-PISONET** | BlazePisonet Windows SoftTimer Engineer | `phoenix/pisonet-windows` | `experiment/windows/BlazePisonet-SoftTimer/` (not root `embedded/`) | PHX-CORE, PHX-MASTER | PHX-QA, PHX-RELEASE |
| **PHX-HARDWARE** | Hardware / Firmware Integration Engineer | `phoenix/hardware-firmware` | `experiment/openwrt/BlazePwifi/esp32/`, `.../esp8266/`, pin/debounce pulse ingress | PHX-MASTER | PHX-CORE, PHX-QA |
| **PHX-QA** | Independent QA / Security Engineer | `phoenix/qa-security` | `experiment/openwrt/BlazePwifi/tests/`; other product tests only with scoped owner agreement | All Subsystems | PHX-MASTER, PHX-RELEASE |
| **PHX-RELEASE** | Build / Packaging / Release Engineer | `phoenix/release-engineering` | Phoenix-specific build/signing workflow files (not every `.github/workflows/` entry), packaging and manifests | PHX-QA, PHX-MASTER | Master Release Gate |

---

## 2. Detailed Role Profiles & Active Task Map

### 2.1 PHX-MASTER (Master Auditor / Integration Coordinator)
- **Mission:** Direct development team, reconcile code and evidence, prevent cross-subsystem regressions, enforce release gates.
- **Active Task:** #172 (Control Plane maintenance), #266 (Cleanup-first gate).
- **Active PR:** `phoenix/master-coordination` (Architecture contracts, integration matrix, audit summary).
- **Current Next Action:** Reconcile active draft PRs across the 6 worker roles, establish non-overlapping branches, enforce no-merge policy on P0 blockers, and coordinate verified fixes.

### 2.2 PHX-CORE (BlazePwifi Core & Finance)
- **Mission:** Single-authority durable ledger, transaction-level correctness, admission serialization, crash-atomic transfers.
- **Active Tasks:**
  - [#31](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/31) — Durable prepaid event idempotency & crash-atomic member transfers.
  - [#32](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/32) — Rental coin lease & receipt atomicity.
  - [#43](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/43) — Independent freshness witness.
- **Active PRs:**
  - [PR #215](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/215) — `member_transfer` lock recheck under member fd7.
  - [PR #222](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/222) — RED test-only fixture proving controller disable race.
  - [PR #241](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/241) — Guard signed financial admission with fd4 serialization lock.
  - [PR #248](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/248) — Unresolved controller admission halt after BP_RUN loss.
  - [PR #252](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/252) — Coin fixture fail-closed + HMAC controller reply (DENY only).
- **Assigned Scope Boundaries:** MUST NOT edit Android launcher or Windows SoftTimer UI code. Must coordinate receipt schema changes with PHX-MASTER.

### 2.3 PHX-RENTAL (BlazeRental Android & Rental Server)
- **Mission:** Android launcher, Device Owner lock UX, dual server-authoritative countdowns, authenticated lease persistence.
- **Active PRs:**
  - [PR #240](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/240) — Authenticate device status before lease/timer persistence.
  - [PR #278 / #281 / #285](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/285) — Merged QR builder URL placeholder fix and verification.
  - [PR #284 / #286](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/284) — Standalone rental uninstall directory scoping.
  - [PR #287](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/287) — Standalone backup directory collision & copy failure protection.
- **Assigned Scope Boundaries:** Owns Android and standalone rental client. MUST NOT modify OpenWrt financial ledger scripts.

### 2.4 PHX-PISONET (BlazePisonet Windows SoftTimer)
- **Mission:** Windows SoftTimer, Win32 serial COM discovery (`GUID_DEVINTERFACE_COMPORT`), overflow-denying math (`TimeCreditMath`), session-atomic CTS.
- **Active Tasks:**
  - [#164](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/164) — Optional MCU-free serial coin input for Windows SoftTimer.
- **Active PRs:**
  - [PR #238](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/238) — Session-atomic CTS V4/V5 native C# correction.
  - [PR #255](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/255) — Win32 `GUID_DEVINTERFACE_COMPORT` same-owned-handle transport.
  - [PR #265](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/265) — Separate SoftTimer overlay from banking UI.
  - [PR #268](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/268) — Centralize checked prepaid-time math (`TimeCreditMath.TryAdd`).
  - [PR #279](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/279) — Simplify native SetupAPI device-interface detail parsing.
- **Assigned Scope Boundaries:** Owns Windows SoftTimer C# code, NSIS scripts, and local UI. MUST NOT modify core OpenWrt routing or Android files.

### 2.5 PHX-HARDWARE (Hardware & Firmware)
- **Mission:** ESP32/ESP8266 coin controller firmware, pulse conditioning/debounce, client-side signature verification, LittleFS quarantine.
- **Active Tasks:**
  - [#177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177) — Coin pulse missed during 3.5s synchronous ESP Vendo poll.
- **Active PRs:**
  - [PR #239](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/239) — Phase A fail-closed ESP coin admission pending provisioning.
  - [PR #254](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/254) — ESP32 CORE config authentication primitive.
  - [PR #283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283) — HW client-side response verification, full RNG nonce, setup HTML escaping & LittleFS quarantine.
- **Assigned Scope Boundaries:** Owns firmware `.ino`, pin assignments, and electrical protocols. MUST NOT declare hardware accepted based solely on host C++ simulations.

### 2.6 PHX-QA (Independent QA & Security)
- **Mission:** Challenge claims, build negative tests, run reproducible regression suites, verify failure-injection across all subsystems.
- **Active PRs:**
  - [PR #264](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/264) — Deduplicate native pulse generation transitions.
  - [PR #267](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/267) — Parallel pinned Windows, CORE, ESP and double Android emulator labs (20-job CI fan-out).
- **Assigned Scope Boundaries:** Owns tests and verification suites. Independent test evidence required for every financial or cryptographic change before merge.

### 2.7 PHX-RELEASE (Build, Packaging & Release)
- **Mission:** Reproducible build workflows, SHA256SUMS manifests, Authenticode & Android APK signing pipeline controls, rollback safety.
- **Active PRs:**
  - [PR #217 / #218](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/217) — Pinned Authenticode and production signature gates.
  - [PR #242](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/242) — Fail-closed future SoftTimer Authenticode signing and final package admission.
- **Assigned Scope Boundaries:** Owns `.github/workflows/` and release scripts. Gated by Master Auditor approval and QA verification.


---

## Live role PR / CI reconciliation — 2026-11-16 UTC21

This timestamped snapshot supplements the historical active-PR lists above; it does not transfer ownership or authorize merges.

| Role | Latest inspected draft PR | Exact head | CI observation |
|---|---:|---|---|
| PHX-MASTER | [#288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) | `598131be8eeae65c136e77781fce008b3aeab610` (code/test commit; subsequent coordination docs are on the same branch) | 11 local synthetic tests passed; no PR-triggered workflow run returned |
| PHX-CORE | [#252](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/252) | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [Run 42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) success; CORE source remains separately owned |
| PHX-RENTAL | [#289](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/289) | `68928774d0d7cf65adb26bc6b54199a3159d066c` | [Runs 43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) success |
| PHX-PISONET | [#255](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/255) | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [Run 42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) success |
| PHX-HARDWARE | [#314](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/314) | `556adc20ef0cfd355089aff3b979c0169af79bdd` | [Run 43782088731](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43782088731) and [43782088748](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43782088748) success; no physical acceptance |
| PHX-QA | [#292](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/292) | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No PR-triggered workflow runs returned |
| PHX-RELEASE | [#291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/291) | `2c4edff231d9b2819415086825530d80b8801307` | [Run 43744993487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487) success; no signing/release gate approval |

COE integration [PR #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) remains draft at `b382d233ff06c8791b1028bed3c617cc7b670d12`; its five workflows are queued. These scoped software runs do not constitute integrated acceptance. Preserve PRODUCTION NO-GO and all owner boundaries.


## Live role PR / CI reconciliation — 2026-11-16 UTC23

This snapshot supersedes earlier live-status tables for the observed heads only; historical entries above are retained. Workflow evidence is exact-commit, not integrated acceptance.

| Role | Current open draft stack / exact head | Exact-head CI observation |
|---|---|---|
| PHX-MASTER | [#288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) `8201deb9198a8416a6546584a9a8f5789526ad84` | No PR-triggered workflow runs returned. Full Master suite not executed in this activation. |
| PHX-CORE | [#252](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/252) `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [Run 42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) completed success; financial P0 issues #31/#32 remain open. |
| PHX-RENTAL | [#240](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/240) `a7d113fb8ae3f0c5e838e64d31cae7a154e37b56`; [#289](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/289) `68928774d0d7cf65adb26bc6b54199a3159d066c`; [#287](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/287) `a4fffd01c8fb1818c32a53522e0590c1dc8a77cd` | #240: runs 40910311141/40910311159 success; #289: 43653329235/43653329229 success; #287: 43754089203 success. These are scoped software checks only. |
| PHX-PISONET | [#255](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/255) `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [Run 42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) completed success; native COM/device acceptance remains unverified. |
| PHX-HARDWARE | [#294](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/294) `8cbd4ecec6fcc4a5b0c758c300de986abee5cf40`; [#314](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/314) `556adc20ef0cfd355089aff3b979c0169af79bdd`; [#315](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/315) `953b743f3edc26671ddf7a457c2a4a4ac0de093f`; [#316](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/316) `888e6941e3a7a81641682c23d937f97d8117d2ea`; older #283 `a87567291e80006f3f30cea81fc20e8b299b95e8` | #294 runs 43669122948/43669122828 success; #314 runs 43782088731/43782088748 success; #315 runs 43963997471/43963997475 success; #316 focused lab 43972511337 success but full build 43972511250 failed in validation job 133668043447; #283 run 43634101437 success. No physical acceptance. |
| PHX-QA | [#267](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/267) `ff5367990c2d27b8ebbb822ee208251af0c890e2`; [#292](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/292) `75a3f66d9563e38a0a48b9cf487b0b057a91ea96`; [#279](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/279) `8f476ef05893193325ef3d1f65a35e144ae7a568` | #267 run 41452247439 success; #292 and #279 have no PR-triggered workflow runs returned. #292's verifier blob is `a8a989964c45ab9aef5719e8d17ba3f6fc66e773`, not current Master blob `3a6d0ca34cad54cd113abbda17d90898603547b3`; branch comparison: Master is 63 commits ahead and the QA branch has 6 commits not in Master. Its README's 4/4 claim used a different older verifier blob `903df403...`, so it is not current-head evidence. |
| PHX-RELEASE | [#242](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/242) `734b89d9e7792247e8376335c3f3685500ab3f89`; [#291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/291) `2c4edff231d9b2819415086825530d80b8801307` | #242 run 40882814472 success; #291 run 43744993487 success. These do not authorize signing or publication. |

COE integration [#26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) remains draft at `b382d233ff06c8791b1028bed3c617cc7b670d12`; all five candidate-head workflows remain queued (43096752609, 43096752632, 43096752800, 43096752563, 43096752557).



## Live role routing snapshot — 2026-11-17 UTC00

This snapshot updates PR pointers and evidence only; ownership boundaries remain unchanged. PHX-MASTER did not modify CORE, RENTAL, PISONET, HARDWARE, QA or RELEASE source branches.

| Role | Current source PR / head | Current COE draft(s) | Evidence / owner next action |
|---|---|---|---|
| PHX-MASTER | #288 / 3d3634dfab35d9f427e159b7d392194edda37930 before this snapshot | #26 integration remains b382d233ff06c8791b1028bed3c617cc7b670d12 | No Master PR-triggered CI. Master owns coordination/phoenix only. |
| PHX-CORE | #252 / c82705f2de865c89ab733b10efa84f26f56a5cc4 | COE #29 / d0830332dee8a1844a85606150681b41d91fe796 | Experiments run 42698139210 success; COE runs 43653906675/676 success. CORE owns key provisioning, signature, replay and durable ledger semantics. |
| PHX-RENTAL | #289 / 68928774d0d7cf65adb26bc6b54199a3159d066c | COE #19 / 04c97030096aa5e5a854952e0cc377ffe31d5d07 | Experiments runs 43653329235/229 success; COE 43061768902 case-collision only. |
| PHX-PISONET | #255 / d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | COE #28 / b21b04617d38a177260258de2d56b24382822117; COE #30 / 4897348d94a0cf7884ecd53244bfcd59e7bf2fbc | Experiments run 42462978704 success; COE runs 43632393888 and 43653415598 success. Synthetic CI only; no native COM acceptance. |
| PHX-HARDWARE | #315 / 939e6ae09050e3e7244249acf9c7969301a05363; #316 / 888e6941e3a7a81641682c23d937f97d8117d2ea remains open draft | COE #27 / 009f70cc2c2775039a5fb072c9d4fdedee76cfc7 | #315 focused 43982762795 success, full 43982762668 failed in validation; #316 focused 43972511337 success, full 43972511250 failed. COE #27 runs 43079646393/46264 success. Reconcile #315/#316, deny keyless poll admission, preserve durable rejected-event state. |
| PHX-QA | #292 / 75a3f66d9563e38a0a48b9cf487b0b057a91ea96; older #267 / ff5367990c2d27b8ebbb822ee208251af0c890e2 | COE #32 / 29b6fe08b10688182d981a66745f482758bd6630 | #292 has no PR-triggered workflows; #267 run 41452247439 success; COE #32 run 43653540607 success. QA must add acceptPollResponse to the extractor and test empty-key denial and reboot/failure cases. |
| PHX-RELEASE | #291 / 2c4edff231d9b2819415086825530d80b8801307 | COE #31 / f4f93dd7c5e18eab1a653f1f756eb1dbb0a234ab | Experiments run 43744993487 success; COE #31 validation/ESP32/ESP8266 run 43986022373 and case-collision run 43986022315 success. Synthetic packaging/compile only; no signer or physical release acceptance. |

COE #18 PisoWiFi head 331e14bc63e163148f09813da0fdbf4d13581a19 has case-collision-only run 43061613277. COE #26 remains a draft at b382d233ff06c8791b1028bed3c617cc7b670d12 with five queued workflows (43096752609, 43096752632, 43096752800, 43096752563, 43096752557). No COE role draft is accepted or merged by this snapshot.

Private Drive registry v11 and newer corrections remain BLOCKED pending authorized Drive read access. Do not substitute historical v5-v7 Library files. Production remains NO-GO.
