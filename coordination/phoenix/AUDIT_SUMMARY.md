# Project Phoenix — Master Audit Summary & Repository Ground Truth

**Audit Executed By:** Master Auditor / Integration Coordinator (`PHX-MASTER`)  
**Timestamp:** 2026-11-13 UTC  
**Governing Issue:** [#172 — [PHX] CONTROL PLANE](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)  
**Cleanup Gate Issue:** [#266 — [PHX] Code-cleanup-first gate](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
**Primary Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Current HEAD (main):** `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**Active BlazePwifi Development Ref:** `origin/blazepwifi-v0.6.0-audit-foundation@2fbd24754d924f7e26210f44383a1b3be28eeef9`  
**Coordination Ref:** `phoenix/master-coordination`  

---

## 1. Executive Summary & Production Gate Status

Project Phoenix is under active, rigorous multi-agent and developer coordination. In strict compliance with `AGENTS.md` and the Master Development Directive:
- **Commercial & Production Status:** **STRICT NO-GO**.
- **Financial Cutover:** **NO-GO** pending independent durable accounting and anti-rollback witness.
- **Hardware Flashing:** **NO-GO** pending 150 power-cut tests and 30-device 24-hour soak.
- **Merge Restrictions:** All safety-critical PRs must remain as **DRAFT** until full gate clearance.

---

## 2. Historical P0 Blockers Triage Against Current HEAD

| Issue | Title | Classification | Ground Truth & Evidence Citations |
|---|---|---|---|
| **[#31](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/31)** | Durable prepaid event idempotency & crash-atomic member transfers | **OPEN / LAB REPRODUCED RED** | Test fixture [PR #222](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/222) ([Run #40451461476](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40451461476)) reproduces confirmed controller-admission vulnerability where a fresh transfer ACKs despite controller being disabled between fd7/fd9. Candidate fix staged in [PR #241](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/241) and [PR #252](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/252) using fd4 serialization lock. |
| **[#32](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/32)** | Rental coin lease and receipt divergence on crash | **OPEN / KNOWN UNRESOLVED** | Installed `rental.sh` in `experiment/openwrt/BlazePwifi/openwrt/rootfs/usr/lib/blazepwifi/` executes `bp_rental_device_write` followed by `bp_rental_append_paid_receipt` as distinct durable operations. Atomic single-journal commit required. |
| **[#43](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/43)** | Independent prepaid-ledger freshness witness | **OPEN / UNKNOWN** | Evaluated via simulation models in CI (job `125297115375`); physical hardware TPM or secure enclave witness not yet provisioned. |
| **[#34](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/34)** | Real hardware power-cut (150 trials), 30-device soak, financial migration acceptance | **OPEN / NEEDS-HARDWARE** | Laboratory and CI passed synthetic tests, but physical hardware acceptance cannot be established through cloud CI. Production release blocked. |
| **[#164](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/164)** | Optional MCU-free serial coin input (Windows & OpenWrt) | **OPEN / LAB VERIFIED** | Windows SoftTimer `GUID_DEVINTERFACE_COMPORT` transport implemented in [PR #255](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/255); session-atomic CTS pulse correction implemented in [PR #238](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/238). Physical serial stress testing outstanding. |
| **[#177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)** | Coin pulse missed during 3.5s synchronous ESP Vendo poll | **OPEN / LAB VERIFIED** | Hardware firmware hardening completed in [PR #283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283) (signed response verification, 64-bit hardware RNG nonces, LittleFS `/quarantine.log` coin quarantine). Physical electronic bench testing pending. |

---

## 3. Active Pull Requests Triage

| PR | Subsystem | Title / Summary | State | Gate Assessment |
|---|---|---|---|---|
| **#287** | RENTAL | Protect standalone rollback backups on repeat installs | DRAFT | Fixes 1s timestamp collision and copy failure checks. Local reproduction verified. |
| **#285** | RENTAL | Record Full QR merged-head CI completion | MERGED | Successfully integrated into `blazepwifi-v0.6.0-audit-foundation`. |
| **#284** | RENTAL | Preserve unrelated dashboard files during standalone uninstall | MERGED | Scopes standalone rental uninstall strictly to owned files. |
| **#283** | HARDWARE | Client-side signed response verification, full RNG nonce, coin quarantine | DRAFT | Resolves HW-P0-1, HW-P0-2, HW-P1-1, HW-P2-1. Firmware tests pass; bench test required. |
| **#279** | QA | Simplify native SetupAPI device-interface detail parsing | DRAFT | Streamlines Pisonet Windows COM port enumeration without behavioral change. |
| **#268** | PISONET | Centralize checked prepaid-time math (`TimeCreditMath.TryAdd`) | DRAFT | Eliminates integer overflow and negative time mutations across SoftTimer. |
| **#267** | QA | 20-way pinned CI fan-out (Windows, CORE, ESP, 2x Android emulators) | DRAFT | Proven in [Run #41452247439](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/41452247439) with 15/20 successful jobs at checkpoint. |
| **#265** | PISONET | Separate SoftTimer overlay and banking UI responsibilities | DRAFT | Clean separation of UI rendering from timer accounting engine. |
| **#255** | PISONET | Win32 `GUID_DEVINTERFACE_COMPORT` same-owned-handle transport | DRAFT | Hardens Windows SoftTimer against COM port alias spoofing and hotplug swaps. |
| **#254** | HARDWARE | Stage non-actuating ESP32 CORE config authentication primitive | DRAFT | Non-actuating HMAC configuration validation. |
| **#252** | CORE | Ordinary coin fixture fail-closed + HMAC controller reply (DENY only) | DRAFT | Hardens controller communication against unsigned replay attacks. |
| **#248** | CORE | Preserve unresolved controller admission halt after BP_RUN loss | DRAFT | Fails closed on state-loss instead of auto-enabling unauthenticated devices. |
| **#242** | RELEASE | Fail-closed future SoftTimer Authenticode signing and final package admission | DRAFT | Establishes automated CI gates preventing release of unsigned Windows binaries. |
| **#241** | CORE | Guard signed financial admission with fd4 and serialize controller admin | DRAFT | Resolves P0 #31 race by locking fd4 during controller policy replacement. |
| **#240** | RENTAL | Authenticate device status before lease/timer persistence | DRAFT | Prevents unauthenticated lease extensions in Android BlazeRental client. |

---

## 4. Immediate Master Directives & Integration Roadmap

1. **Maintain Role Separation:**
   Each worker must strictly operate within their owned scope defined in `ROLE_ASSIGNMENTS.md`. No cross-subsystem file modifications without explicit Master sign-off.
2. **Reconcile Core Finance Lock (P0 #31):**
   `PHX-CORE` and `PHX-QA` must verify that PR #241 (fd4 serialization lock) passes the real signed CGI regression from PR #222 while preserving idempotent replay of previously committed receipts.
3. **Firmware Verification (HW-P0-1 & HW-P0-2):**
   `PHX-HARDWARE` PR #283 must be maintained in DRAFT until non-customer bench hardware logs verify LittleFS quarantine behavior under simulated link failure.
4. **Windows SoftTimer Stability:**
   `PHX-PISONET` must integrate `TimeCreditMath.TryAdd` (PR #268) with the same-owned-handle COM transport (PR #255) and verify warning-free compilation.
5. **No Production Release:**
   Under all circumstances, production gates remain firmly closed until physical acceptance criteria are fulfilled.


---

## 5. 2026-11-15 live integration candidate reconciliation — independent Master pass

**Scope:** read-only live GitHub source/commit metadata and a narrowly scoped Master coordination verifier enhancement. This subsection updates evidence after the 2026-11-13 historical snapshot above, without rewriting another role's handover or claiming a production release.

| Evidence item | Current observation | Admission assessment |
|---|---|---|
| Historical source `Experiments/main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; active Full development is separately `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` | Main is not the complete current Phoenix development branch |
| COE migration [draft PR #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) | `b382d233ff06c8791b1028bed3c617cc7b670d12` with `Pisowifi/`, `Rental/`, `Pisonet/`, `Hardware/`, `Shared/` staging, but `main@a6513ab4412b4c014eee2863e45cbe32d06cb243` remains structure-only | DRAFT. Do not treat PR body assertion of "95% software release readiness" as verified acceptance. Eight candidate HEAD workflows were reported queued, not passed, during this check |
| CORE default-deny [draft PR #29](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/29) | `6b404e047cdb4dba3d60b1055d991c8050eaa622`, stacked on #26. [POSIX/BusyBox/provenance workflow 43633615058](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43633615058), job `132565494762`, **COMPLETED SUCCESS**; [case collision 43633615065](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43633615065), job `132565494511`, **COMPLETED SUCCESS** | CI VERIFIED on those two bounded checks only; no P0 payment, hardware or production admission implied. This patch is not integrated into COE main or #26 |
| Migration destination path collisions | Two real target-prefix overlaps: `Rental/` ↔ `Rental/android/`, `Rental/` ↔ `Rental/openwrt/`; distinct nonoverlapping original sources | Root `Rental/` route is now `manual-file-mapping-required` and `copy_permitted=false`. No bulk recursive copy or ownership overwrite; per-file immutable provenance + QA sign-off first |
| PHX-MASTER audit & source guards | Draft [PR #288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) now guards source *and destination* overlaps; 13 Python regression cases authored | Independent live tree/manifest checks executed; **Python tests have not been run** on its latest source SHA, and no exact-head Actions run has been identified |

**Priority order:** P0 #31/#32 durable ledger and receipt/lease atomics with independent source-exact QA → P0 #43 protected off-device witness, key custody and safe v1→v2 migration → #34 real electrical/physical acceptance (150 actual power cuts, 30-device 24h soak, noncustomer native targets) → signed release dry run → separately authorized commercial cutover. No manufactured hardware proof, automatic merge or release.


## 6. 2026-11-15 PHX-QA BLAZE-COMMS/1 recipient RED and Master correction

Independent [PHX-QA draft #292](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/292) ran a source-exact, minimal Python fixture against Master verifier blob `a8a989964c45ab9aef5719e8d17ba3f6fc66e773`: **4 tests, 2 pass, 2 fail**. The real `validate_envelope` accepted `to=PHX-UNKNOWN` and `to=PHX-QA;PHX-UNKNOWN`. The QA RED is valid; do not erase or relabel its original evidence.

Master repair [6d4619bd](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/6d4619bd594089d4898564cd6233c79b40c943d2) now accepts only a single exact registered `PHX-*` role or `ALL`, rejects all unknown/multi-target/whitespace/case variants, and retains a distinct missing-recipient error. [15d6839b](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/15d6839b28bc05b1a143c5ea7b76e4621e8fcc0d) adds two source-linked test methods (15 authored Master unit tests total). This is coordination protocol validation only; not a financial state or controller security fix.

**Verification classification:** GitHub exact-source readback and JS source/manifest assertions are static. The QA four-case host RED was actually executed **against the earlier verifier blob**, not the repaired one. Git clone from this runtime could not resolve `github.com`; full Python source-exact execution and GitHub Actions on the corrected HEAD are **NOT RUN / BLOCKED**. PHX-QA should rerun its existing four tests at corrected verifier blob `ea57965fec5bc9ca91b4bb5cbae9e15d51248b0b` and execute all 15 Master tests, reporting exact SHA and stdout before marking GREEN.

Private Drive registry `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was re-read (55 project entries); no private IDs, snapshots or raw registry content were committed or disclosed. This registry is not production approval. All financial, witness, signing, physical and release gates remain **PRODUCTION NO-GO**.


---

## 7. 2026-11-15 21 UTC — draft permission and owner-boundary hardening

**Role:** PHX-MASTER, task [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) and [#172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172). The full-team uploaded Master prompt and BLAZE-COMMS/1 rules remain the contract, with strict no-Codex execution. The private 2026-10-27 v11 project registry remained the latest registry in its Drive folder during this read-only check; no private records/IDs were posted publicly.

**New source-grounded coordination defects:** on original Master verifier blob `ea57965fec5bc9ca91b4bb5cbae9e15d51248b0b`, `safe_repo_path("Rental//")` accepted redundant trailing separators; a Master manifest route could declare a product runtime destination; any draft route outside an overlapping parent/child could set `copy_permitted=true` without triggering the overlap guard. These are draft routing and review-control gaps, **not demonstrated payment or firmware exploits**.

**Test-first, bounded repair:** [test commit 7ecbd012](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/7ecbd0124eb9f82f4fb2bd2eee4a2aa02c022845) authored three negative tests. [source commit a59cbfb3](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/a59cbfb3e599e67905ecbbf36bac933242f353c8) rejects `//` aliases, enforces Master coordination-only `source=coordination/phoenix/`, `target=null`, `kind=coordination-only`, and rejects any draft `copy_permitted` value other than false. [routing note 9cd17cd7](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/9cd17cd7e6af7f4745bb1f84ba91c3cddc356eec) describes the human workflow and rollback. **18 authored Master tests total**, not 18 executed tests. Manifest remains `DRAFT_REVIEW_ONLY`, no product files migrated.

**Executed only as isolated guard-semantics exercise:** 8/8 checks passed on a disposable Python reconstruction of the new guard predicates, **not** on the complete checked-out source, full Master suite, QA #292 or GitHub Actions. GitHub readback confirmed source and test anchors and matching manifest conditions. The exact-head source test outcome is **NOT RUN/UNKNOWN**; no false GREEN.

**Latest worker review (HEAD-sensitive, all DRAFT):** historical COE integration [#26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) remains `b382d233...`; CORE [#29](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/29) `bf6f546d...` has bounded POSIX/BusyBox and case collision [#43634990566](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43634990566) and [#43634990558](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43634990558) **COMPLETED SUCCESS**. Standalone Rental [#289](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/289) `59ff7ecb...` reports a pending four-case installer status instrumentation gate. Windows Pisonet [COE #30](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/30) `8144242c...` reported its latest exact-head synthetic Windows CI **QUEUED**, not passed. ImageBuilder [COE #31](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/31) `478940ba...` remains lab-preview only; independent release/network QA and real target boot/flash acceptance are missing. QA [#292](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/292) preserved the original 2-PASS/2-FAIL recipient RED; corrected Master's same-suite GREEN is not yet shown.

**Master next gate:** Independent PHX-QA executes the unchanged four-case #292 suite against latest Master verifier blob `903df4034f8aa46f66e32de6e0be9b9ab2ca4b48` and exact current Master branch, then all **18** Master tests; capture immutable blob+commit identity, stdout/exit code and a runnable exact-head CI workflow or a source-exact Python checkout. In parallel prepare per-file migration provenance and sign-off for `Rental/` parent destination overlaps. Do not merge, release, flash, sign production or promote paid admission.

**Standing decision:** **PRODUCTION NO-GO**, due ledger/lease atomicity, protected independent monotonic witness, reversible v1→v2 migration, native hardware acceptance, P-256 signing custody, 150 real power cuts and 30-device 24-hour soak.
