# Project Phoenix — Source ownership and migration routing (2026-11-15)

This is a **routing and review document**, not a claim that code has been copied, integrated, tested, or released. Machine-readable source paths and role owners are in [OWNERSHIP_ROUTES.json](OWNERSHIP_ROUTES.json). Keep this map scoped to Phoenix; unrelated `android/` and `embedded/` experiments are **not** automatically owned by Rental or Pisonet.

## Verified repository state

- Original: `BlazeDevStudio/BlazingSystems-Experiments` `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`. Real historical code remains under `experiment/openwrt/BlazePwifi/`, `experiment/openwrt/Rental-Server-Standalone/`, and `experiment/windows/BlazePisonet-SoftTimer/`.
- Destination: `BlazeDevStudio/CoinOperatedEcosystem` `main@a6513ab4412b4c014eee2863e45cbe32d06cb243` currently contains only a README and a Pisonet placeholder. **Do not interpret this as a completed migration.**
- Existing staging: [COE draft PR #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12`. It already includes `Pisowifi/`, `Rental/`, `Pisonet/`, `Hardware/`, `Shared/` and `tools/`. Reuse/review; do not overwrite it with a second indiscriminate migration.
- [Experiments draft PR #288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) owns `coordination/phoenix/` and remains draft.

## Review-before-move routing

| Role | Historical source (representative) | Intended COE area | Status |
|---|---|---|---|
| PHX-CORE | `BlazePwifi/openwrt/rootfs/usr/lib/blazepwifi/`, signed `www/blazepwifi/cgi-bin/vendo` | `Pisowifi/openwrt/rootfs/` | Draft: selective comparison needed |
| PHX-RENTAL | `BlazePwifi/android/`; `profiles/standalone-rental/`; `Rental-Server-Standalone/` | `Rental/android/`, `Rental/openwrt/` | Draft: provenance and behavior mapping needed; **not a direct folder rename** |
| PHX-PISONET | `experiment/windows/BlazePisonet-SoftTimer/` | `Pisonet/SoftTimer/` | Draft |
| PHX-HARDWARE | `BlazePwifi/esp32/`, `BlazePwifi/esp8266/` | `Hardware/esp32/`, `Hardware/esp8266/` | Draft; physical acceptance absent |
| PHX-QA | `BlazePwifi/tests/` | `Pisowifi/tests/` | Draft; tests must use corresponding code SHA |
| PHX-RELEASE | `.github/workflows/blazepwifi-build.yml` | `.github/workflows/pisowifi-ci.yml` | **Reimplemented pipeline**, not a byte-for-byte migration |
| PHX-MASTER | `coordination/phoenix/` | No runtime destination | Coordination only |

All paths above are relative to the relevant repo and, unless fully spelled out, abbreviated under `experiment/openwrt/BlazePwifi/`. The manifest contains full paths. The broad old role shorthand `android/`, `embedded/`, `tests/`, or all `.github/workflows/` is **not an exclusive source ownership grant**.

## Mandatory migration sequence

1. Refresh both actual HEAD SHAs, open PRs, handovers and the private project registry before moving code.
2. Inventory source path, destination path, exact blob identity, licenses and dependent tests. Mark divergent implementations as separate candidates; do not silently mix them.
3. Resolve source ownership collision first. The standalone Rental subtree overlaps multiple intended `Rental/` destinations **semantically**, so establish a per-file provenance map before copying anything.
4. Perform small, reversible changes in an owner-scoped branch, retaining historical source until proven and accepted.
5. Verify source/target hashes for exact copies, run focused negative regressions and end-to-end CI at the same candidate SHA, then seek independent QA review.
6. Keep production **NO-GO** pending signed identity, independent freshness witness, durable financial migration, real power-cut and 30-device soak hardware evidence. No production flash or financial cutover based on this document.

## Human debugging guide

Start at `OWNERSHIP_ROUTES.json` to find the owner and both locations; inspect the linked draft PR and commit; reproduce on the **same SHA** using the subsystem's local test harness; inspect the durable state and error codes before modifying UI or payment credit. If a file appears in more than one candidate, record both hashes and the source dependency before choosing a canonical copy. Never delete the original to hide duplication.


## Destination-prefix collision gate (2026-11-15)

A live GitHub-tree inspection of Experiments `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b` and COE candidate PR #26 `b382d233ff06c8791b1028bed3c617cc7b670d12` found **two overlapping target-prefix pairs**, both under Rental:

1. Broad `Rental/` destination from the historical `profiles/standalone-rental/` overlaps the separate `Rental/android/` Android source route.
2. The same broad `Rental/` route overlaps the separate `Rental/openwrt/` standalone service route.

These are **not two duplicate source ownership claims**; they are **destination path collisions for naive recursive copying**. They are not permission to overwrite either subtree. `OWNERSHIP_ROUTES.json` deliberately marks the broad `Rental/` route `kind=manual-file-mapping-required`, `copy_permitted=false`, with an explicit human review reason. The coordination verifier rejects destination prefix overlaps unless the shared owner and non-copyable manual-map guard hold; exact destination duplicates and cross-role overlaps always fail. Four negative unit tests exercise these cases.

**Do not remove this blocker to make tests green.** First prepare an exact per-file route, expected target Git blob SHA/mode, source Git blob SHA/mode, license and user-facing behavior review for each affected item. Obtain PHX-RENTAL and independent QA sign-off on the changed target branch. Original histories remain intact; COE PR #26 remains draft / no production approval.

The verifier and regression source are committed on Phoenix Master draft PR #288, but their Python execution and cross-platform CI results are still to be checked on the exact latest head. Static manifest checks do not establish financial, physical or release readiness.


## Draft routing authorization and source-owner invariant (2026-11-15)

The `OWNERSHIP_ROUTES.json` manifest records **proposed ownership and review routes**, never a migration command. PHX-MASTER can claim only `coordination/phoenix/`, with `target=null` and `kind=coordination-only`: it has no runtime authority over COE's `Pisowifi/`, `Rental/`, `Pisonet/`, `Hardware/`, or `Shared/` trees. All worker code edits remain in their own role branches and draft PRs.

The verifier now fails closed if **any** route under `status=DRAFT_REVIEW_ONLY` explicitly declares `copy_permitted` other than JSON `false` (absence is a routing hint, not authorization), if a Master route attempts to claim runtime source/destination, or if a route uses ambiguous repeated path separators such as `Rental//`. This is independent of the existing overlap guard: even a nonoverlapping draft route cannot silently convert into a copy instruction.

Three additional authored Python negative regression cases assert these invariants (**18 authored Master tests** after the earlier recipient-contract fix). Only a disposable, separately reconstructed eight-case Python guard-semantics harness has been executed; **8/8 PASS in that harness**. This is not a checkout of the exact GitHub blobs, not a full 18-test run, and not a GitHub Actions result. Independent PHX-QA must rerun source-linked [#292](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/292) against the repaired current Master verifier, then execute the full 18-test suite against the same commit.

**Rollback:** revert the three scoped Master commits on PR #288 only; no product runtime or payments have changed. Keep the manifest review-only until an owner-approved per-file migration plan, hash/mode provenance, role approval and independent QA are on record. Production remains **NO-GO**.


## Windows external-board source/staging parity hold (2026-11-15 UTC22)

Independent PHX-QA [control-plane checkpoint](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-6884672106) reports a **conditional active-low read-error fail-open in the older PISONET owner implementation**, not in the already-corrected COE staging implementation. The older `GetSignal` returned false on read exceptions, and the active-low inversion could then count an authoritative active second. The staged implementation uses error-aware `TryGetSignal` and denies unknown status before polarity inversion. This is a **migration parity hazard**: do not overwrite the staged implementation with an older same-named source blob merely because it is from the owner branch.

Source-linked evidence to preserve: [PISONET owner draft #255](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/255), [COE integration draft #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) at `b382d233ff06c8791b1028bed3c617cc7b670d12`, and stacked [COE PISONET draft #30](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/30) at `8144242c0469ffc9fc7757ebe91964caa4a2a527`. [Native CI run 43643411388](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43643411388) is reported **completed/success** for #30's head; it is not a physical-board test or evidence of #26's exact-head equivalence.

**Required before migration:** PHX-PISONET and independent PHX-QA must identify the six differing same-named Windows product blobs with exact source and destination blob SHA, mode, dependency/import and license, test the active-low read-error regression at the **actual proposed integration SHA**, and approve a per-file merge preserving the fail-closed `TryGetSignal` behavior. Until then: **BLOCKED for blind copy, NO-GO for production**. This coordination note is not a code change, release approval or claim that the current staged branch is unsafe.


## Hardware quarantine-evidence migration hold (2026-11-15 UTC05)

New stacked PHX-HARDWARE [draft PR #296](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/296) at `a4989c815b7348cf780c34ec6b7b84c83ebe62d4` (base [#295](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/295) at `7b6e28c9cdc71b5c4b56c54e522ba79a3653f994`) reports a security-relevant source cleanup: ESP setup servers previously accepted an unauthenticated `POST /quarantine/clear` that erased `/quarantine.log`, evidence needed for unpaid-coin reconciliation. The draft changes the POST response to HTTP 403, removes firmware `LittleFS.remove("/quarantine.log")` paths, and preserves read/export behavior. These are PR-author claims, **not independently executed physical or exact-head CI acceptance in this Master pass**.

**Migration invariant:** A destination implementation must not silently restore a remotely callable quarantine-clear/delete pathway, including via an older source copy or alternative endpoint. Before any ESP32/ESP8266 per-file migration, PHX-HARDWARE and independent PHX-QA must compare exact source/destination Git blobs and modes, inspect all write/delete call sites and authentication boundaries, verify license/dependency/import completeness, run a hostile-POST negative regression and read/export positive control at the *proposed integration commit*, and record durable quarantine preservation across reset/power loss separately. An HTTP 403 or green extracted-handler test alone does not prove persistent flash safety or reconciliation correctness.

This is a **cross-repository provenance/review hold only**. PHX-MASTER does not edit firmware, authorize deletion of evidence, certify the hardware, or promote either draft branch. Financial and physical release gates remain **NO-GO**.


## Setup-AP interface provenance hold (2026-11-15 UTC07)

Stacked PHX-HARDWARE [draft #297](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/297) at `cd8b3f9637f770fd609e2de41fc0d1adb299f105` (based on quarantine-clear-deny [#296](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/296)) adds `setupRequestAllowed()` / `requireSetupApRequest()` to ESP32 and ESP8266 setup root, quarantine-view and POST-save handlers. The predicate checks `setupApOn && web.client().localIP()==WiFi.softAPIP()` and denies other requests with HTTP 403. Two exact-commit [workflow runs 43681908681](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43681908681) and [43681908774](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43681908774) report completed success; these are bounded CI/model checks, **not** physical dual-interface acceptance.

**Migration hazard:** importing older firmware source into COE can silently omit this guard or restore quarantine export/configuration access from the station interface. Before any per-file ESP migration, PHX-HARDWARE and independent PHX-QA must inspect exact proposed destination Git blobs/modes, source licenses/imports and route registration for **both** targets, verify the guard executes before sensitive reads/writes, and test separate AP/station clients, AP-disabled behavior, ambiguous network addressing, and denied POST side effects on noncustomer hardware. Preserve the earlier quarantine-clear-deny hold; a successful host mock is not proof of the network interface selected by the device. Do not treat a local-IP equality check alone as independent physical network-boundary evidence.

**Disposition:** review-only provenance hold, no firmware migration or role takeover. No release, flash, real-money operation or acceptance; production remains **NO-GO**.


## Persisted ESP configuration migration hold (2026-11-15 UTC08)

PHX-HARDWARE's stacked **draft** [#298](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/298) at `cbb4fd3f96c4bf2e89dad067a1c68392bbf5987b` and [#299](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/299) at `7e57ffdb3fc647beee484003922cf326b0016b4a` report two distinct persisted-input hardening changes. ESP8266 now validates NUL termination of fixed-size current/v1 EEPROM strings before consuming or migrating them; malformed legacy records must fall back to generated setup defaults rather than read out of bounds. ESP32 now bounds persisted debounce (1–2000 ms) and pulse grouping (10–10000 ms) **before** narrowing to 16 bits, preventing wraparound into pulse processing. These are source-owner PR claims, not a Master physical acceptance result.

**Migration review gate:** Compare exact ESP8266/ESP32 source and proposed COE destination blob SHAs and file modes, all configuration reader/call-site imports, firmware dependencies, storage schema/version handling, licenses and corresponding test identities at the proposed integration SHA. Independently run malformed-current and malformed-v1 EEPROM field cases, oversized/zero persisted ESP32 timing cases, and positive valid-config controls. Check whether the *destination* already has equivalent stronger behavior; never blindly overwrite it with an older owner copy. Confirm reset/reboot recovery and real electrical pulse timing separately on authorized noncustomer hardware. Preserve the earlier quarantine-clear denial and setup-AP isolation holds. Neither isolated host sanitizer success nor a successful build is proof of real EEPROM/Preferences or coin ingress durability.

**Evidence scope:** Two [PR #299 exact-head GitHub Actions runs](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43690790514) and [run 43690790538](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43690790538) were returned as completed/success; job contents and physical behavior were not independently reproduced in this Master pass. COE draft #26 at `b382d233ff06c8791b1028bed3c617cc7b670d12` returned only queued PR-triggered run records. No cross-repo file migration is authorized. **PRODUCTION NO-GO.**


## Pending-journal deletion verification migration hold (2026-11-15 UTC09)

PHX-HARDWARE stacked [draft #300](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/300) at `657cfce54008ccf1c431c4d5d323471cabebb649` (based on #299) identifies a recovery-state hazard in both ESP32 and ESP8266: clearing the RAM pending event before confirming LittleFS journal deletion can leave an on-flash event that replays after reboot while the running device incorrectly treats it as cleared. The owner change makes `clearPending()` return a verified result, checks LittleFS availability and absence of pending journal candidates, and retains the in-memory event plus `journalRecoveryRequired` on failure. Two exact-head Actions runs, [43695539400](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43695539400) and [43695539371](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43695539371), reported completed/success. This is bounded simulated/source-extracted evidence, **not** physical LittleFS or crash-atomic financial acceptance.

**Cross-repo migration gate (review-only):** Before integrating any firmware file into COE, compare exact source and destination Git blob SHA and file mode at the actual proposed commits; check license, dependencies/imports, storage schema and test identities. PHX-HARDWARE and independent PHX-QA must test LittleFS unavailable, deletion failure, residual journal candidate, successful deletion, and reboot/replay behavior for both targets, including negative no-ACK/no-credit and positive verified-clear controls. Verify that no alternate handler clears RAM, `journalRecoveryRequired`, or quarantine evidence on failure; preserve earlier quarantine-clear denial, setup-AP isolation, EEPROM bounds and persisted timing clamps. Hardware reset/power-cut persistence and financial receipt durability require separate independent real-device evidence. Never replace a stronger staged destination implementation merely because an owner branch is newer.

**Disposition:** No source migration, approval, hardware test or release performed by PHX-MASTER. COE integration [draft #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) remains at `b382d233ff06c8791b1028bed3c617cc7b670d12`; its queried workflow records remain queued, not proof of success. **PRODUCTION NO-GO.**


## Quarantine log record-boundary migration hold (2026-11-15 UTC10)

PHX-HARDWARE stacked [draft #301](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/301) on #300 at base `657cfce54008ccf1c431c4d5d323471cabebb649`. The owner reports that ESP32/ESP8266 LittleFS quarantine logging previously interpolated untrusted server rejection bodies and targets into line-oriented records without encoding. Embedded CR/LF, tabs, backslashes and other control bytes could create forged-looking records or ambiguous manual recovery. The proposed `quarantineLogField()` encoder visibly escapes CR/LF/tab/backslash, replaces other controls, bounds variable fields, and marks truncation. These are **source-owner claims**, not independent Master runtime verification; #301 is draft.

**Review-before-move gate:** PHX-HARDWARE and independent PHX-QA must compare exact #301 source and proposed COE PR #26 destination blob SHAs/file modes, license, imported dependencies, quarantine writers/readers, line framing, test-file identities and exact-head CI. Exercise hostile CR/LF, tab, backslash, NUL/control bytes, maximum-length/truncation, normal UTF-8 and reboot/readback cases on **both** targets. Verify one physical log line per event, bounded output, unambiguous evidence and no false positive receipt ACK or quarantine clearing; inspect whether the destination already has stronger encoding. Preserve #300 verified journal-delete-before-RAM-clear, earlier quarantine-clear denial and setup-AP isolation. Do not treat host ASan/UBSan tests as LittleFS crash durability or independent financial acceptance.

**Disposition:** No firmware copy or migration approval. Await exact-head #301 CI status and independent QA plus authorized noncustomer physical persistence evidence. COE draft #26 remains review-only at `b382d233ff06c8791b1028bed3c617cc7b670d12`; production **NO-GO**.


## Pending-journal write/readback migration hold (2026-11-15 UTC11)

PHX-HARDWARE stacked [draft #302](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/302) at `b73403d6daa6f136f136c46d8a90cd99d648e401` (base [#301](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/301) at `d3d1caf1931a0433d43d5007a184fc3fd5d947ad`) changes both ESP32 and ESP8266 `savePending()` paths: after writing and closing `/pending.new`, the code reads it back with the production `readPendingFile()` parser and compares the entire record before rotating journal files. On failed parsing, short read, or mismatched bytes, it attempts to remove the temporary candidate and returns failure. The original pending-journal format and names remain unchanged. This is a **source/diff inspection**, not independent execution or proof of power-loss atomicity.

Two workflow runs associated with #302's exact head were returned as completed/success: [43705921550](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43705921550) and [43705921537](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43705921537). Their successful simulated filesystem cases do **not** establish actual flash persistence or independent QA acceptance.

**Integration invariant:** Never replace a destination firmware implementation with a version that promotes `/pending.new` to `/pending.dat` solely on a successful-length `write()`. Before a per-file move, compare exact source/destination Git blob SHA and mode, license, imports and dependency closure, and source-linked test identities at the proposed COE integration SHA. PHX-HARDWARE and independent PHX-QA must test same-length post-close corruption, short write/read, failed read-open, primary-journal preservation on failure, reboot recovery, and failures of cleanup/rename separately. In particular, a failed `LittleFS.remove("/pending.new")` must not be mistaken for proof of a clean temporary journal; record the remaining state and fail closed. Confirm no credit/relay admission on any uncertain durable state. These are **review requirements**, not claims that all cases are already covered.

COE draft #26 remains at `b382d233ff06c8791b1028bed3c617cc7b670d12`; no firmware migration, QA approval, financial cutover or release is authorized. Production **NO-GO** pending independent protected signing and anti-rollback witness, crash-atomic durable finance, reversible migration, native acceptance, 150 real power cuts and 30-device/24-hour soak.


## Pending-journal rotation verification migration hold (2026-11-15 UTC12)

PHX-HARDWARE [draft #303](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/303) is stacked on #302, source HEAD `1689e215e36f377ddc98c66abdee3d3dffec438f` and parent `b73403d6daa6f136f136c46d8a90cd99d648e401`. It targets ESP32/ESP8266 LittleFS pending-journal rotation, including stale-backup removal, primary-to-backup rename, temporary-to-primary promotion, rollback and cleanup failure paths. This is an owner-branch review checkpoint, not a claim of independently verified durable flash behavior. Associated Actions [43710360969](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43710360969) and [43710360780](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43710360780) returned completed/success at that source SHA; no physical tests were performed by MASTER.

**Mandatory review-before-move:** COE [draft #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) remains at `b382d233ff06c8791b1028bed3c617cc7b670d12`. Before considering any migration, PHX-HARDWARE and independent PHX-QA must map the exact ESP32 and ESP8266 source/destination paths and compare Git blob SHAs, file modes, licenses, imported dependencies, persistent format, recovery readers, and test identities at pinned commits. Inject each LittleFS remove/rename/open/write/readback failure separately, including rollback failure and stale backup collision; after simulated reboot, assert exactly-once recovery or explicit quarantine, never fabricated ACK, premature credit, silent deletion or lost pending evidence. Confirm the #302 full-record readback gate and #300 delete-before-RAM-clear gate remain intact, alongside quarantine log field escaping and setup-route isolation. Source CI alone cannot prove crash-atomic persistence or independent protected financial acceptance.

**Disposition:** Review-only; no source copy, integration approval, financial cutover, merge or release. MASTER exact-head suite not executed and no matching PR workflow runs returned. COE integration PR #26 associated workflow records were queued, not successful. Private registry not located through connected Drive filename searches; do not disclose its identifiers or infer its contents. PRODUCTION NO-GO pending independent QA, protected signing/anti-rollback witness, reversible finance migration, native acceptance, 150 real power cuts and 30-device 24-hour soak.


## ESP remote-configuration source/staging mismatch hold — 2026-11-17 UTC04

The current PHX-HARDWARE source correction is on Experiments PR #315 head 75dc5f0b888f16e2c85e4321f62df4685639ad33. Both source sketches contain only a dormant applyRemoteConfig definition and no response call sites. Focused source-extracted CI run 44013351048 passed the register-config denial matrix; full run 44013351035 failed in the QA-owned poll extractor and is not an overall green build.

COE integration PR #26 at b382d233ff06c8791b1028bed3c617cc7b670d12 still stages older ESP32/ESP8266 firmware with two response-driven applyRemoteConfig call sites per board and keyless sigOk=true defaults in both register and poll paths. Exact destination blob IDs and source owner blob IDs are recorded in REMOTE_CONFIG_MIGRATION_STAGING_AUDIT_20261117_UTC04.md. The candidate's existing Hardware test does not assert the source-side no-callsite/keyless-deny invariant.

**Review-before-move hold:** do not copy the COE candidate over the corrected #315 source, and do not promote the current destination firmware. PHX-HARDWARE owns the source firmware correction; PHX-QA owns independent test verification; the COE integration owner owns the destination candidate. PHX-MASTER owns only this coordination and provenance record. The current OWNERSHIP_ROUTES.json remains DRAFT_REVIEW_ONLY and unchanged.

License/provenance is also unresolved for Hardware: the candidate Hardware subtree has no LICENSE or NOTICE file, the COE root LICENSE path is absent, and the PisoWiFi-only SOURCE_INTAKE manifest does not inventory Hardware. The source project MIT license and destination Pisowifi/LICENSE are byte-identical, but the destination license scope for Hardware must be confirmed by the owner. This is not a legal conclusion.

No file move, source copy, overwrite, merge, release or hardware operation is authorized by this note.


## Current Hardware source/staging provenance hold (2026-11-17 UTC05)

The machine-readable OWNERSHIP_ROUTES.json remains DRAFT_REVIEW_ONLY and pins source_ref to Experiments main f4e8a891..., while the current HARDWARE owner source candidate is draft #315 at 75dc5f0b888f16e2c85e4321f62df4685639ad33. These are distinct source snapshots. For Hardware migration review, use the current owner PR #315 as the source candidate and compare it per file with COE draft #26 at b382d233ff06c8791b1028bed3c617cc7b670d12; do not assume the manifest's main SHA contains the latest owner correction.

The current owner source has dormant remote configuration and denies POST /quarantine/clear with HTTP 403 without deleting /quarantine.log. COE #26 still applies remote configuration from register/poll responses and deletes the quarantine log through POST. Exact ESP32/ESP8266 blobs, modes, source-test imports, license/notice scope and CI are in HARDWARE_STAGING_PARITY_AUDIT_20261117_UTC05.md.

No route permission changed: PHX-MASTER still owns coordination/phoenix only; PHX-HARDWARE owns firmware; PHX-QA owns independent tests; COE integration remains review-only. Do not copy, overwrite, merge, or close owner PRs based on this note.

## Current HARDWARE source-candidate addendum — 2026-11-17 UTC06

The machine-readable `OWNERSHIP_ROUTES.json` remains pinned to Experiments main and COE PR #26 and stays `DRAFT_REVIEW_ONLY`. For current hardware review, PHX-HARDWARE's separate owner-controlled candidate is DRAFT #315 at `c1db0a567500302921c0561bcd31446f12767372`; separate DRAFT #316 at `888e6941e3a7a81641682c23d937f97d8117d2ea` remains open and must not be silently composed.

At #315, the ESP8266/ESP32 source blobs are `35bc5b20...` / `5b448444...`; COE #26 still stages `c8be98f7...` / `3cc7ec54...`. The current source includes a durable one-shot `/pending.attempt` marker, source-extracted negative/failure labs, dormant remote-config mutator and deny/no-delete quarantine-clear route. The destination lacks the marker and current labs, retains keyless-positive register/poll configuration call sites, and deletes `/quarantine.log` through POST /quarantine/clear.

**Review disposition:** retain both histories; no copy, overwrite, path relocation or promotion. PHX-QA must repair and independently run the exact-source extractor; PHX-CORE must review the marker/idempotency contract; the COE integration owner must reconcile source/destination blobs, tests, license/notice scope and all queued workflows. See [UTC06 Master evidence](COIN_POST_ATTEMPT_MARKER_MIGRATION_AND_QA_EXTRACTOR_AUDIT_20261117_UTC06.md).

## Current coin POST disposition source/staging hold — 2026-11-17 UTC07

The machine-readable `OWNERSHIP_ROUTES.json` remains pinned to Experiments main `f4e8a891...` and COE integration PR #26 `b382d233...`, with status `DRAFT_REVIEW_ONLY`. It is a route proposal, not a copy command. The current HARDWARE owner source candidate is draft #315 at `4afc7c8bd8ea410049f1da7bc962bfc989b4ba1b`; it is a distinct, newer source snapshot and must be reviewed per file rather than silently substituted for the manifest's main ref.

At exact #315/#26 commit trees, both ESP firmware paths are mode `100644` but different blobs:
- ESP8266 source `e47d392e5fd3724c414e4ec50b3cb74658047c31` → destination `c8be98f72596681e36a3ad1f8939bf8046c96887`.
- ESP32 source `5de92f01990bd551e4c9dd063ff0eb0572a301e8` → destination `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.

The current source contains a durable `/pending.attempt` marker and a `coinPostDispositionVerified()` function that returns DENY until PHX-CORE supplies an approved event-bound authenticated receipt contract. On unapproved response it preserves the pending journal and marker and denies automatic replay. The COE #26 candidate has none of the marker/disposition helpers, still has keyless-positive register/poll response paths and the earlier destructive quarantine-clear behavior. COE `Hardware/tests/` contains only one shell hardening script; the source poll/disposition lab is not imported. Exact source test blob: `84275ece076295387e468da25df506fda9ff3bfb` mode `100644`; destination shell test blob: `f921c56cecc19cab1989507b9b4ade1f45dac54e` mode `100755`.

The #315 focused run 44038469936 passed source-extracted host/fake-filesystem cases, while Full run 44038469823 failed because the QA-owned extractor omitted five current firmware dependencies. The source lab is not physical flash or coin evidence. No Hardware-local LICENSE/NOTICE was found in the destination candidate; scope remains an owner/custodian review, not a legal conclusion.

**Review-before-move hold:** keep COE #26 draft. Do not copy, overwrite, relocate or promote these firmware files. PHX-HARDWARE owns firmware, PHX-QA owns independent tests, COE integration owns destination staging, and PHX-MASTER owns only coordination and provenance. No merge, release, flash or financial action is authorized.



## Current Hardware staging refresh — 2026-11-17 UTC08

The live OWNERSHIP_ROUTES.json remains DRAFT_REVIEW_ONLY, pins source_ref to Experiments main f4e8a891… and destination_candidate_pr to COE #26 b382d233…, and grants PHX-MASTER only coordination/phoenix/ with target=null. It is not a copy command.

For current hardware parity, compare owner PR #315 at cc0743009f44baeda0ea12d84eb6199a8a6916c7 against COE #26 at b382d233ff06c8791b1028bed3c617cc7b670d12. COE PR #27 at 009f70cc2c2775039a5fb072c9d4fdedee76cfc7 contains the same stale ESP32/ESP8266 firmware blobs as #26; its successful scoped CI does not validate the current #315 source. The exact firmware, helper, quarantine-clear, test-import and license-scope findings are in HARDWARE_STAGING_REFRESH_AND_DUPLICATE_CANDIDATE_AUDIT_20261117_UTC08.md.

**Review-before-move hold:** no source copy, destination overwrite, path relocation, merge or promotion. PHX-HARDWARE owns firmware, PHX-QA owns independent regression/extractor verification, COE integration owns destination staging, and PHX-MASTER owns only coordination and provenance. The exact private Drive registry was not available; no older Library artifact was substituted.


## Poll-admission fixture and Hardware destination provenance — 2026-11-17 UTC09

The current HARDWARE #315 source `84fe6b790139d147f330f13a40b3ae3e89a7042d` intentionally denies all poll responses until the CORE-owned canonical authorization contract and QA vectors exist. The inherited `tests/v05_firmware_hardening_test.sh` still expects the previous positive `|poll|` signature formula; its wrapper invokes it and current Full validation fails at that assertion. The test files are unchanged in #315. PHX-QA must update its own tests; PHX-MASTER must not modify `experiment/openwrt/BlazePwifi/tests/`.

At COE #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`, ESP32 and ESP8266 firmware blobs remain non-identical to current #315, with older response-driven config and quarantine-clear behavior. The destination has only one Hardware shell test and no Hardware-local LICENSE/NOTICE in the inspected tree. The source repository NOTICE and BlazePwifi LICENSE must be considered in the owner/custodian review; `Pisowifi/LICENSE` alone is not evidence that the Hardware subtree's notice scope is resolved.

Keep #26 draft. Do not copy, overwrite or relocate Hardware files. Require exact source/destination blob+mode, dependency/import, test identity, license/NOTICE and exact-head combined CI review before any per-file proposal. `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY` and is not a migration command.


## PISONET candidate-stack routing clarification — 2026-11-17 UTC10

The machine-readable `OWNERSHIP_ROUTES.json` remains unchanged at source `main@f4e8a891...` → COE #26 `b382d233...`, status `DRAFT_REVIEW_ONLY`, with PHX-MASTER target `null`. It is a route proposal, not a copy command.

PISONET owner source PR #255 is `d01fd164...`; COE #28 `b21b046...` and #30 `4897348...` are a separate destination candidate chain, with #30 27 commits ahead of #28. #30 diverges from COE #26 at COE main; it is not a child of #26. Keep the per-file provenance and test-import audit in [PISONET_STACKED_DESTINATION_CANDIDATE_AUDIT_20261117_UTC10.md](PISONET_STACKED_DESTINATION_CANDIDATE_AUDIT_20261117_UTC10.md).

Do not blanket-copy Experiments #255 `SerialHardware.cs` / `AppController.cs`: their boolean active-low status-read path is older and less safe than COE #26/#30 `TryGetSignal` fail-closed handling. Do not promote COE #30's installer until NSIS warning 6000 on the `$COMMONAPPDATA` state guard is corrected and tested. No Pisonet subtree LICENSE/NOTICE was found; owner/custodian must resolve notice scope.

**Review-before-move hold:** no copy, overwrite, relocation, cherry-pick, merge or promotion. PHX-PISONET owns installer/product changes; PHX-QA owns independent native tests; COE integration owner owns destination staging; PHX-MASTER owns only coordination and provenance.

## Current HARDWARE and RELEASE handover heads — 2026-11-17 UTC10

HARDWARE #317 `3ed38225...` is a child of #315 `84fe6b79...`, itself based on #314 `556adc20...`. Focused marker lab [44065129637](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44065129637) succeeds (56/56 source-extracted cases); Full [44065129519](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44065129519) fails at the QA-owned legacy poll-signature assertion. Preserve default-deny and route the fixture repair to QA.

COE RELEASE #31 current head `d9ac5982...` has scoped runs [44064212523](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44064212523) and [44064212547](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44064212547) SUCCESS; this does not open signing/publishing or production gates.

## COE appliance ULA prefix review hold — 2026-11-17 UTC11

COE #26 and its release child #31 emit invalid fd00:db8:blaze::/48 from tools/package_appliance_firmware.py::generate_network_uci(). #31's interface/VLAN validation does not validate the ULA prefix; the profile has no networking.ula_prefix field and packager tests have no ULA/IPv6 assertion. This is a destination integration blocker, not permission for PHX-MASTER to edit the release-owned packager.

PHX-RELEASE owns packager/profile/test correction; PHX-CORE and the COE integration owner define deployment-scoped prefix provisioning; PHX-QA independently verifies exact-head generated UCI; PHX-HARDWARE validates only after correction and explicit noncustomer authorization. Keep #26/#31 draft. OWNERSHIP_ROUTES.json remains unchanged, DRAFT_REVIEW_ONLY; no copy, overwrite or move is proposed.


## COE RELEASE #31 ImageBuilder boundary — 2026-11-17 UTC14

COE #31 remains a child of integration PR #26 at exact head d45b84c67dc587fca6226662cb1d8bc59bdb11ae, based on b382d233ff06c8791b1028bed3c617cc7b670d12. Its current release-owned changes add a sandbox runner and route synthetic test-harness executions through it. They do not change the ownership-routing manifest or establish a source-repository migration.

The packager's generated build script still does not invoke the runner. Treat the current work as a CI test-harness boundary only; actual build invocation remains unproven. The runner shares the host network and must not be described as network-isolated. Exact evidence and owner actions are in [COE_IMAGEBUILDER_RUNTIME_ENFORCEMENT_AND_ULA_AUDIT_20261117_UTC14.md](COE_IMAGEBUILDER_RUNTIME_ENFORCEMENT_AND_ULA_AUDIT_20261117_UTC14.md).

OWNERSHIP_ROUTES.json remains unchanged, DRAFT_REVIEW_ONLY, with PHX-MASTER target null. No source copy, destination overwrite, relocation, cherry-pick, merge or promotion is proposed. COE #26 retains five queued workflows and remains draft.


## COE generated-wrapper runtime finding — 2026-11-17 UTC15

COE RELEASE #31 remains a draft child of integration #26 at exact head `d45b84c67dc587fca6226662cb1d8bc59bdb11ae`. Packager blob `fd558928b2869ce1f4b2cb2776b405b4b723b310`, line 495, embeds literal `\\n` sequences in the generated shell template. A bounded local shell reproduction showed syntax-only `sh -n` exit 0 but runtime exit 2 (`Syntax error: Bad fd number`). The exact-head sandbox workflow [#44104956173](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44104956173) remained IN_PROGRESS at last read; do not claim CI failure or success before its conclusion.

PHX-RELEASE owns the template correction on its own branch; PHX-QA independently verifies the exact final head. PHX-MASTER only records this gate. The packager still emits invalid site ULA `fd00:db8:blaze::/48`, and its generated build entrypoint still does not invoke the test-only sandbox runner. Keep #26/#31 draft. `OWNERSHIP_ROUTES.json` remains unchanged and `DRAFT_REVIEW_ONLY`; no copy, overwrite, move, cherry-pick or promotion is authorized.


## UTC15:14Z COE #31 CI status clarification

The final-head sandbox run [44104956173](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44104956173) completed CANCELLED after 15 packaging tests reported `ok`; the generated-wrapper syntax-only test passed, but the empty-firmware runtime test was not reached. This is incomplete evidence. Do not promote the test-harness sandbox or generated build. PHX-RELEASE owns the literal-escape correction and actual build entrypoint enforcement; PHX-QA independently verifies. No source migration is authorized.


## COE RELEASE #31 UTC16 — operator wrapper source correction and runtime hold

COE #31 exact head is `9c2bebf50030c03bc4dd1e827e050863ba482eab`, based on integration #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`. The current packager wrapper now re-enters through the release-owned sandbox runner for an uncontained operator invocation. This supersedes the prior UTC14/UTC15 source observation that the operator wrapper invoked Make directly. The runner uses a read-only host root, a writable ImageBuilder bind, and `--share-net`; network isolation is not claimed.

Exact-head sandbox run [44125258197](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44125258197) was CANCELLED at its 20-minute workflow timeout after 15 packaging tests reported `ok`; no complete runtime verdict exists. The test helper and runner lack per-invocation timeouts. RELEASE owns bounded process execution and retry; QA independently verifies. The invalid `fd00:db8:blaze::/48` ULA remains in the packager and blocks integration.

HARDWARE #317 is now at `839c21877c27c893e2efc73b3afe7c48e1fcfa4e`. Focused labs pass; Full [44130911522](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44130911522) fails at the legacy positive poll-signature grep. QA owns the fixture correction; preserve firmware default-deny.

COE #26 remains draft at `b382d233ff06c8791b1028bed3c617cc7b670d12` with five queued workflows. #31 remains draft and is not integrated. `OWNERSHIP_ROUTES.json` remains unchanged, DRAFT_REVIEW_ONLY, with PHX-MASTER target null. No source copy, destination overwrite, relocation, cherry-pick, merge, or promotion is authorized.

## Live routing refresh — 2026-11-17 UTC17

- PHX-MASTER remains restricted to `coordination/phoenix/`, architecture/interface contracts, integration provenance and release-gate coordination.
- COE #31 remains RELEASE-owned on `phoenix/release-imagebuilder-failclosed-20261115@411eeb103cfeebc589f6dc9c48b1789ebb047913`; Master makes no edits to its packager, runner, tests or workflow.
- PHX-QA owns independent review of the proposed unprivileged single-ID namespace trial and the exact-head negative/runtime tests. No QA acceptance is inferred from prior scoped CI.
- COE #26 remains the integration owner's draft staging branch at `b382d233ff06c8791b1028bed3c617cc7b670d12`; #31 is a separate draft child and is not treated as integrated.
- `OWNERSHIP_ROUTES.json` is unchanged at blob `e4db324315a1b3543fec17a148fbf960170fcb29`, status `DRAFT_REVIEW_ONLY`, PHX-MASTER target `null`. It remains a review map, not a copy/move command. No destination files, licences, histories or test identities were changed.
- The private registry/correction set is unavailable through the exposed connector; no older snapshot was used as authority and no private identifiers or contents were published.


## Live routing and migration hold — 2026-11-17 UTC18

- PHX-MASTER remains limited to `coordination/phoenix/`, architecture/interface contracts, cross-repository provenance, integration matrices and release-gate coordination.
- COE #26 remains the destination staging candidate at `b382d233ff06c8791b1028bed3c617cc7b670d12`; its five workflows are queued. COE #31 remains a RELEASE-owned draft child, not integrated.
- The current #317 source firmware blobs differ from the staged #26 Hardware ESP32/ESP8266 blobs. Destination code still has active poll authorization defaults and quarantine deletion, while current #317 is default-deny and preserves quarantine evidence. No source copy or destination overwrite is authorized.
- Source QA test `experiment/openwrt/BlazePwifi/tests/controllers.sh` has no exact target at `Pisowifi/tests/controllers.sh`; the distinct `Hardware/tests/test_firmware_hardening.sh` is not an import-equivalent test and retains positive-poll/clear-route expectations.
- Source BlazePwifi MIT license blob is `1ee55b94183417be977ca287cd7391f9a6f7e721`; COE #26 places the same blob only under sibling `Pisowifi/LICENSE`. No Hardware-specific or COE-root LICENSE/NOTICE was found. Resolve applicability before any file move.
- HARDWARE #318 is a separate divergent child from #317 (49 ahead / 40 behind, mergeable=false). Keep both drafts; no rebase, cherry-pick, merge or destination staging from either until owner stack selection and QA review.
- COE #31's unprivileged single-ID runner is source-present but hosted-runner UID-map setup fails. No sandbox acceptance; infrastructure owner must authorize a disposable no-secret runner with user namespaces enabled. No sudo/helper/broad-ID/unsandboxed fallback.
- `OWNERSHIP_ROUTES.json` remains unchanged at blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, PHX-MASTER target `null`. This remains a review map, not a copy/move command.
- Canonical private Drive registry v11/newer corrections remain inaccessible through the exposed connector; no older snapshot was substituted and no private contents/IDs were published.

**No destination file was moved, copied, overwritten, or deleted.**
## Live routing and migration hold — 2026-11-17 UTC19

- PHX-MASTER remains restricted to coordination/phoenix/, architecture/interface contracts, cross-repository provenance, integration matrices and release-gate coordination.
- COE #26 remains the destination staging candidate at b382d233ff06c8791b1028bed3c617cc7b670d12; five PR-triggered workflows are queued with no jobs. COE #31 is RELEASE-owned at 390f2acc45969689caa00a4647d365b0122877ca and remains a separate draft child.
- COE #31 source runner is unprivileged single-ID bubblewrap with bounded timeouts, but the hosted runner denies user-namespace setup. Infrastructure owner must authorize an ephemeral no-secret namespace-capable runner. No sudo/helper/broad-ID/unsandboxed fallback.
- The invalid ULA fd00:db8:blaze::/48 remains in the packager; the EW1200G profile has no ula_prefix field and packaging tests have no ULA assertions. Preserve the site-scoped durable RFC 4193 /48 contract.
- HARDWARE #317 source heads are 6399b471... (ESP32), b0aba5fb... (ESP8266), and f7896647... (controllers test). COE #26 destination blobs 3cc7ec54... / c8be98f... differ; source controllers.sh is absent at Pisowifi/tests/controllers.sh. Destination Hardware test/README retain positive poll and quarantine-clear expectations. No import-equivalence.
- Source MIT license blob equals COE Pisowifi/LICENSE, but no Hardware-specific/root license or NOTICE was found. Resolve applicability and NOTICE mapping before any move.
- HARDWARE #318 is a separate divergent child: current head be371b03..., current #317 parent 7b427133..., 49 ahead/45 behind, mergeable=false, no CI. No rebase/cherry-pick/merge until HARDWARE proposes stack direction and QA verifies exact source/test SHA.
- `OWNERSHIP_ROUTES.json` remains unchanged at blob e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER target null. It is a review map, not a copy/move command.
- Canonical private Drive registry v11/newer corrections remain inaccessible; no older snapshot was substituted and no private contents/IDs were published.

**No destination file was moved, copied, overwritten or deleted.**

## Live routing and migration hold — 2026-11-17 UTC20

- PHX-MASTER remains restricted to `coordination/phoenix/`, architecture/interface contracts, provenance, integration matrices and release-gate coordination.
- Current Experiments refs: main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; development `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`; Master branch before this audit `cdb8c355f82255ccf87aaa78e7afdc99dec6f798`.
- COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243`; #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`, five workflows queued, zero jobs. No combined acceptance.
- COE #31 `93379dde568b956a56c06358d8031f7304667e1a`: packaging validation and both ESP board builds pass, case guard passes, but mandatory sandbox fails because hosted runner denies unprivileged UID-map setup. No sandbox acceptance; no sudo/uidmap/broad-ID/unsandboxed fallback.
- HARDWARE #317 `2e20e21d1129c5b85493c1b48566d7e663fa6ba4`: focused labs pass; Full validation fails at QA-owned stale poll-signature fixture. #318 `be371b03a36306a7691b411bf1b29da60b916646` has no CI and is nonmergeable; keep separate until owner stack resolution and QA.
- QA #292 is a test-only branch based on pre-fix Master. The current Master validator rejects unknown/ambiguous recipients; its regression still needs independent rerun against current exact blob and #288 candidate.
- Invalid ULA `fd00:db8:blaze::/48` remains; site-scoped durable RFC4193 /48 contract still requires CORE/RELEASE definition and QA validation.
- `OWNERSHIP_ROUTES.json` unchanged at blob `e4db324315a1b3543fec17a148fbf960170fcb29`, DRAFT_REVIEW_ONLY, PHX-MASTER target null. No copy/move authorization.
- Canonical private Drive registry v11/newer corrections unavailable through the exposed connector/Library; no older snapshot substituted and no private data published.

**No destination file was moved, copied, overwritten or deleted.**


## UTC21 live stack and migration hold — 2026-11-17

- Experiments main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; development `aad3aade72c1156eecba1fed30907c6d0283b2c5`; Master branch before this audit `b58771d5ac3f3c7489551429ea531c460d0f1185`.
- COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243`; #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`, five workflows queued, zero jobs.
- HARDWARE #317 current head `1d4320fb11c43192c1e27ebb0b69039729abdc1a`; child #318 `696e28ed4cd53b9189b78095b38aee973d774683`. Exact compare: merge base `3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3`, 51 ahead / 63 behind, DIVERGED, #318 mergeable=false, no #318 runs. Child handover's 31/27 and older SHAs are stale.
- #317 Full run 44173107277 fails the QA-owned positive poll-signature assertion; focused labs pass. Keep default-deny.
- COE #31 `7bdba18b86f706d7fb96831094338600e28cc9c5`: shared/hardware and case-collision checks pass; mandatory sandbox 44179122674 fails because hosted runner denies unprivileged UID-map setup.
- No migration route or manifest change is authorized. `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, DRAFT_REVIEW_ONLY, PHX-MASTER target null. No file moved/copied/overwritten/deleted.
- Registry v11 and newer corrections unavailable; no older Library snapshot substituted. **PRODUCTION NO-GO.**


## UTC21 Hardware source routing supplement — PR #283

PR #283 `83646f309a84f3f0de9c1af6dac2c7ee08b61c85` is a third open Hardware candidate based on main. It changes both ESP sketches, `tests/controllers.sh`, and adds a firmware-hardening test under the QA-owned `tests/` path. The source/test blobs differ from #317 and #318; comparisons show #283 diverged 13/272 from #317 and 13/260 from #318. Current-head run 44182715006 is pending; predecessor run 44182117122 is overall cancelled. Require PHX-HARDWARE stack proposal and PHX-QA ownership/test review. No copy/move/rebase/cherry-pick/merge authorization.

## UTC23 migration hold — current Hardware candidates and COE #26

- Current Experiments candidates: #283 `83646f309a84f3f0de9c1af6dac2c7ee08b61c85`, #317 `a166f91d6c790aa81ff98794038d76b39bc6562d`, #318 `696e28ed4cd53b9189b78095b38aee973d774683`. They are three distinct, divergent drafts; do not treat #283's green workflow as proof that its two new host labs ran.
- Exact source/destination ESP32 and ESP8266 blobs all differ. Routed source `tests/controllers.sh` is absent at COE `Pisowifi/tests/controllers.sh`; the distinct `Hardware/tests/test_firmware_hardening.sh` still expects positive poll-signature and quarantine-clear behavior. #283's new LittleFS and quarantine-clear host labs are not in COE #26 and not invoked by its current source workflow.
- COE #26 `SOURCE_INTAKE.json`/`MIGRATION_MAP.md` are still pinned to historical source `6d4c9b...`; the intake explicitly disclaims release authorization, hardware testing, full CI and complete source admission. Refresh only after HARDWARE stack selection and independent QA test-identity review.
- Source BlazePwifi MIT license equals sibling `Pisowifi/LICENSE`, but no Hardware-specific or COE-root LICENSE/NOTICE exists. Resolve license/NOTICE applicability before any Hardware import. Source and destination build workflows differ and require reimplementation review.
- Current #318 compare against #317 is DIVERGED (51 ahead / 68 behind); #318 mergeable=false and no current-head CI. Keep all three Hardware PRs separate pending owner decision.
- #291 current docs head `a74b8b94...`: exact source/test CI 44199068618 SUCCESS, docs-only CI 44199987756 IN_PROGRESS; signing/publisher skipped. COE #31 sandbox 44179122674 remains host-blocked; COE #26 five workflows remain queued.
- `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, PHX-MASTER target null. No destination path is authorized by this audit.
- Canonical private Drive registry v11/newer corrections are not accessible through the exposed connector/Library; no older snapshot substituted.

**No destination file was moved, copied, overwritten or deleted. No subsystem source branch was modified. PRODUCTION NO-GO.**

## 2026-11-18 UTC00 — pending-clear, Hardware stack and COE test parity — current routing hold

PHX-MASTER remains limited to coordination/phoenix/, architecture/interface contracts, provenance and integration matrices. CORE, RENTAL, PISONET, HARDWARE, QA and RELEASE retain their source branches and test ownership.

Current Hardware candidates are #283 e8c6619 (main-based), #317 fce915 (stacked on #315 84fe6b79; source/test ddc7ed1f), and #318 696e28 (nonmergeable divergent child). Pairwise comparisons are DIVERGED: #283/#317 15 ahead / 280 behind; #318/#317 51 ahead / 71 behind; #318/#283 260 ahead / 15 behind. No rebase, cherry-pick, force-push or stack selection was made.

The #317 clearPending source guard matches Master §2.3.1 deletion preconditions, but coinPostDispositionVerified remains false for every response. Helper CI is SIMULATED only and does not authorize financial disposition. QA's static response_sig / |poll| presence checks are not proof of signature acceptance. #283's current green is scoped software CI only; its QA-owned test changes require QA review.

COE #26 remains historical-rootfs staging at SOURCE_INTAKE/MIGRATION_MAP source 6d4c9b..., not a current Hardware import. Current #283/#317/#318 sketches differ from each other and from destination. Source controllers.sh has no target path; destination Hardware test is a different static test. Source MIT license equals Pisowifi/LICENSE, but Hardware/root LICENSE/NOTICE applicability is unresolved. No move/copy/overwrite.

COE #31 still has invalid site ULA fd00:db8:blaze::/48 and hosted user-namespace failure. No privileged or unsandboxed fallback. Private registry v11/newer corrections remain inaccessible; no historical snapshot is substituted.

OWNERSHIP_ROUTES.json remains unchanged at e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER target null.

## 2026-11-18 UTC01 — COE Release stack and destination candidate hold

- COE #31 current head is `20e75fc0e6fb7e7ada560a9ec41cb9695d198fa8`; mandatory sandbox run 44213707995 failed closed at `bwrap: setting up uid map: Permission denied` after 7/7 host-preflight tests passed. Packaging regressions were skipped. Shared/firmware run 44213709669 and case guard 44213707845 passed, scoped only.
- COE #35 `61e2d8ef77e5cd3740ab9e630e5bfcc1994b7d09` is based on old #31 head `7bdba18b...`; compared with current #31 it is DIVERGED 2 ahead / 7 behind and mergeable=false. It modifies the same two Release paths, `tools/package_appliance_firmware.py` and `tools/test_package_appliance_firmware.py`. Its exact-head case/shared/firmware runs pass, but no mandatory sandbox run was returned. The workflow PR trigger only targets COE integration branch and its push trigger only targets the parent Release branch; #35 is outside both filters. Require Release owner reconciliation and exact-head sandbox execution.
- COE #27 `009f70cc2c2775039a5fb072c9d4fdedee76cfc7` is based on COE main, not #26. Compare #26 → #27 is DIVERGED 3 ahead / 83 behind. Its ESP32/ESP8266 blobs are byte-identical to #26 staging, but differ from current Experiments #283 and #317. It is a separate historical destination candidate, not proof of current-source import.
- COE #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`, five workflows queued / zero jobs. Do not use #27's scoped green CI as #26 acceptance.
- Current #317 Full validation 44209812745 fails at the QA-owned legacy positive poll-signature assertion; focused runs pass. Preserve default-deny. #318 has no current-head CI and is nonmergeable.
- `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, PHX-MASTER target null. No destination route is newly authorized.
- No source/destination file was copied, moved, overwritten or deleted. **PRODUCTION NO-GO.**


## UTC03 — Hardware candidate lineage and COE Release exact-head reconciliation

PHX-MASTER accepts the HARDWARE-proposed #314 → #315 → #317 → #320 ancestry as the current candidate lineage for continued review only. Exact compare #317→#320 is 11 ahead / 0 behind with merge base equal to #317 HEAD. #318 remains a divergent 51/71 child of an older #317 base with no current-head CI. #283 remains a separate main-based candidate and its QA-owned test additions require independent review.

COE RELEASE #35 is now a clean child of current #31 at exact base 59ed44d0..., 7 ahead / 0 behind. This supersedes the prior UTC01 stale-child finding. Its mandatory sandbox still fails closed at hosted user-namespace UID-map setup; packaging regressions were skipped. COE #26 remains five queued workflows / zero jobs.

OWNERSHIP_ROUTES.json is unchanged, DRAFT_REVIEW_ONLY, with PHX-MASTER target null. No route or destination copy permission was added. No source/destination files moved or copied.

## UTC03 — current Hardware child and COE destination hold

The current Hardware review lineage is #314 → #315 → #317 → #320 → #322. #322 is a clean child of exact #320 head `b2b41a3d6ce7887b9624137c966f58462895d3fa`; its source/test changes are limited to output-enable ordering in the two firmware sketches, a source-extracted lab, a Hardware-specific focused workflow and a handover. This is a review candidate only. #283 remains main-based, #318 remains divergent, and #321 remains a separate test-only RED branch. PHX-MASTER does not own any of those source paths.

COE #26 remains the destination integration candidate at `b382d233ff06c8791b1028bed3c617cc7b670d12`, but its five workflows are queued with zero jobs. COE #27 remains a separate main-based candidate and is not integrated. COE RELEASE #35 is a child of #31, but the mandatory sandbox remains host-blocked and the current packager ULA placeholder remains invalid.

`OWNERSHIP_ROUTES.json` is unchanged at blob `e4db324315a1b3543fec17a148fbf960170fcb29`: `DRAFT_REVIEW_ONLY`, destination PR #26, PHX-MASTER target `null`. Do not alter route destinations, copy files, or promote staging until exact source/destination blobs, modes, license/NOTICE applicability, import completeness, test identities and exact-head CI are independently reconciled. No migration, merge, copy, overwrite or delete occurred.


## 2026-11-18 UTC04 — COE INTERCON source provenance and routing hold

COE #36's legacy source is a selective import from Labs `embedded/blaze-pisonet-universal/`: the original .ino blob and COE legacy copy are identical (`3fb15ecb9272b65500260bc7c92f05590163fa6d`). The Labs folder also contains README.md and browser-only preview.html; COE adapts the README and omits the non-firmware preview. No explicit license grant was found in the Labs root/source or COE root; NOTICE.md is an engineering handling notice, not a license. Do not copy this source farther into #26/main until rights are confirmed.

The new COE path `Hardware/esp8266/BlazePisonetUniversal/` is absent from the current Phoenix ownership manifest. It is not the Windows `Pisonet/SoftTimer/` route and not the BlazePwifi `Hardware/esp8266/` route. Keep #36–#42 as separate review candidates, with #39/#40/#42 unselected and #41 tied to #39. The manifest remains `DRAFT_REVIEW_ONLY`, PHX-MASTER target null; no copy/move is authorized. See [COE_INTERCON_STAGE3_PARALLEL_JOURNAL_LINEAGE_AUDIT_20261118_UTC04.md](COE_INTERCON_STAGE3_PARALLEL_JOURNAL_LINEAGE_AUDIT_20261118_UTC04.md).

## 2026-11-18 UTC05 — #323 source-to-destination migration hold

The current PHX-HARDWARE candidate is #323 head `f98bc39c29eeb82b292aa83fa680d05d2e36efd5`, based on exact #322 head `50d93e0de3d682550b6f02fb43484e76ad9c7e08`. It changes the ESP32 and ESP8266 BlazePwifi sketches, adds `poll_fault_dual_store_lab.py`, extends the Hardware quarantine/readback workflow and adds a Hardware handover. These paths remain PHX-HARDWARE-owned; PHX-MASTER does not copy them.

At COE #26 head `b382d233ff06c8791b1028bed3c617cc7b670d12`, destination sketch blobs `3cc7ec54...` (ESP32) and `c8be98f...` (ESP8266) differ from source blobs `b0dfe6cf...` and `8e79b9eb...`. The new lab blob `fbfe2c72...` is absent from the destination tree. Experiments workflow blob `2358e4ab...` invokes the dual-store lab; COE hardware workflow `fe79adb...` does not. COE #26 has five queued workflows and zero jobs, so there is no combined destination acceptance.

The source MIT license blob `1ee55b94...` matches COE `Pisowifi/LICENSE`, but the destination tree has no root or Hardware-specific LICENSE/NOTICE. Do not assume the sibling Pisowifi license resolves Hardware subtree applicability. Obtain explicit owner/custodian review.

`OWNERSHIP_ROUTES.json` remains unchanged at `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, destination PR #26, PHX-MASTER target `null`. No copy, move, overwrite, rename, rebase, merge or route change is authorized. Revisit only after exact blobs, license/NOTICE applicability, import completeness, test identities, workflow invocation, exact-head CI and owner/independent QA review all reconcile. **PRODUCTION NO-GO.**

---

## COE INTERCON candidate boundary — 2026-11-18 UTC06

COE PRs #39/#40/#42 introduce three incompatible Stage-3 journal formats (64/76/92 bytes). Stage-4 #41 is a shadow-only child of #39; Stage-4 #43 is a live paid-time/timer child of #42. These are newly staged COE Hardware sources, not byte-identical migrations from the Experiments BlazePwifi firmware route.

OWNERSHIP_ROUTES.json has no route for COE Hardware/BlazePisonetUniversal/INTERCON. Existing PHX-HARDWARE routes cover only BlazePwifi ESP32/ESP8266; PHX-PISONET covers Windows SoftTimer. The COE integration owner must nominate the source owner and define a per-file destination/license/test map before any copy or merge. COE root LICENSE and Hardware/LICENSE were not found; do not assume a sibling Pisowifi license covers this subtree.

No file was copied, moved, renamed, or overwritten. Keep #41 and #43 as separate drafts; compare exact source blobs, journal format, test identities, licensing, owner approval and exact-head CI before any destination staging.

---

## 2026-11-18 UTC07 — no migration; current exact-head source boundary

HARDWARE #323 current PR head `0d6f0c7f4f9d2d07bc43d24e5db63d8bddb11f43` (source/test `a3aa967087680887e925791f83a8fbc48a1e62b9`) remains PHX-HARDWARE-owned. The inherited QA fixture failure does not authorize Master to edit `tests/v05_firmware_hardening_test.sh` or either sketch. QA owns the test correction; HARDWARE owns source/handover freshness; CORE owns the poll schema and golden vectors.

COE Release #35 current docs head `68657a5fcc21df3883c8f3296c3925d5876ac05b` (source/test `5fe815f9e985bf2280b05fb189598826c68a7be6`) remains RELEASE-owned. Its mandatory sandbox still fails closed at UID-map setup. The PR description is stale and must be refreshed by PHX-RELEASE, not Master.

COE #26 remains at `b382d233ff06c8791b1028bed3c617cc7b670d12` with five queued workflows and zero jobs. The new INTERCON path has no route in the ownership manifest. Stage-3 #39/#40/#42 formats remain incompatible; #41/#43 remain separate Stage-4 candidates. No source route is inferred and no destination copy/move is authorized.

`OWNERSHIP_ROUTES.json` remains unchanged at blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, destination PR #26, PHX-MASTER target null. No file was copied, moved, overwritten, renamed, rebased or deleted. Preserve exact source blobs, license/NOTICE applicability, complete import inventory, test identity and exact-head CI as preconditions for any future owner-authorized staging.


## 2026-11-18 UTC08 — poll response producer/consumer migration hold

Source Experiments development vendo blob a1c19180385e618c412b4af21c0e91c1f47da1dd and COE #26 vendo blob 0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e are behaviorally divergent: the source emits no response signature, while the destination contains a derived poll response_sig candidate. The candidate uses keyed SHA-256 concatenation, not standard HMAC, and is not approved by CORE/QA. Current Experiments #323 firmware deliberately denies poll and coin disposition, so the COE expression is not a drop-in-compatible contract.

The #323 source/test sketch blobs are ESP8266 8e79b9eb8856e67d966f4c6385f89fccdc8be7fc and ESP32 bd74b11c1496b0943404ff387ee72bb45d4743e5. The QA-owned positive poll-string fixture fails current Full CI at [run 44262258842](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44262258842), while focused host labs [44262258247](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44262258247) and [44262258937](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44262258937) pass. COE #26 still has five queued workflows and zero jobs.

No copy/move/overwrite is authorized. Preserve the existing exact source/destination blobs, license/NOTICE review, full import inventory, test identities and exact-head CI requirements. Private Drive v11/newer corrections are unavailable; no older snapshot is substituted. OWNERSHIP_ROUTES.json remains DRAFT_REVIEW_ONLY, PHX-MASTER target null. PRODUCTION NO-GO.

## 2026-11-18 UTC09 — current Hardware #323 staging review

#323 branch/docs head 1761bf38 and source/test SHA d37d5da9 remain PHX-HARDWARE-owned. COE #26 b382d233 contains different ESP32/ESP8266 sketch blobs, lacks the new dual-store and related source lab files, and its Hardware workflow invokes a different generic test script. The #26 positive poll-signature grep conflicts with the current deny-only source and is not an acceptable migration test identity.

The source MIT license blob matches sibling Pisowifi/LICENSE, but Hardware/root license and NOTICE applicability remains unresolved. The source root NOTICE is absent from the destination tree. No file-by-file complete import, license/NOTICE approval or combined exact-head CI exists. **No copy/move/overwrite is authorized.** The unchanged manifest remains DRAFT_REVIEW_ONLY, PHX-MASTER target null.

See [HARDWARE323_CURRENT_HEAD_AND_COE26_MIGRATION_PROVENANCE_20261118_UTC09.md](HARDWARE323_CURRENT_HEAD_AND_COE26_MIGRATION_PROVENANCE_20261118_UTC09.md).

## COE Universal / INTERCON source-provenance gate — 2026-11-18 UTC10

COE PR #36 is stacked on integration #26 at `b382d233ff06c8791b1028bed3c617cc7b670d12`; #38 is stacked on #36; #39/#40/#42 are parallel Stage-3 children of #38; #41 is a Stage-4 child of #39; #43 is a Stage-4 child of #42. None of #36–#43 is merged or already present in #26. The #26 integration branch still returns 404 for `Hardware/esp8266/BlazePisonetUniversal/`.

**Verified import scope:** Labs main `5d8e4f1d95b6bfc551996634df9c6f7b86af56b4` contains three files in `embedded/blaze-pisonet-universal/`. COE #36's legacy `.ino` is an exact blob match (`3fb15ecb...`, 73,632 bytes). The source README and browser-only preview are not copied; the destination parent README is a new, different blob. Labs root NOTICE is also absent from COE. No explicit LICENSE was found in the source root/source directory or destination root/Hardware listing. The public-safe NOTICE is not a license grant. Treat the import as **one-file exact archival preservation only**, not a complete source-directory mirror or license-cleared redistribution.

The active staging firmware is a separate V1.5-derived implementation; COE's audit says the locally delivered V1.5 artifact is not verified in GitHub. Experiments main/development ESP8266 trees contain BlazePwifiVendo and README only, not the Universal project. Therefore the existing Experiments-only `OWNERSHIP_ROUTES.json` mapping does not establish provenance for the Labs source or the new COE-native staging code. No route change is authorized.

Stage-3/Stage-4 branches use incompatible record layouts (64 / 76 / 92 bytes) and two different Stage-4 behaviors. Keep all candidate branches draft and separate. Exact CI is host/static simulation plus ESP8266 compile; it is not real flash, coin, relay, brownout or 150-power-cut acceptance. See the current Integration Matrix UTC10 snapshot for exact run IDs and test identities.


## 2026-11-18 UTC10 — corrected COE Universal / INTERCON provenance gate

COE #36 now contains a GitHub Stage-1 staging snapshot at `b4d7434764aab72673de1f496ed9e442f031ddff`; the previous statement that no staging snapshot existed is corrected. The exact Stage-1 sketch/header/types blobs and static/ESP8266 compile run are recorded in `COE_INTERCON_STAGE1_SNAPSHOT_V16_PARALLEL_BRANCH_RECONCILIATION_20261118_UTC10.md`. The original V1.5 local attachment lineage remains unverified; do not describe the staged snapshot as byte-identical or source-cleared.

A separate V1.6 branch `1e9b0269e3ed2138813fcd0c838b0034a08dfd90` has a distinct path and test/workflow identity, with branch CI passing but no open PR. Neither branch is in #26 or selected as canonical.

The legacy Labs import remains one exact `.ino` blob only (`3fb15ecb9272b65500260bc7c92f05590163fa6d`); README, preview and Labs root NOTICE are absent from the COE destination, and explicit redistribution rights remain unverified. `OWNERSHIP_ROUTES.json` has no COE Universal/INTERCON route. Directory placement does not create a formal owner: COE integration owner must nominate an accountable owner; request PHX-HARDWARE firmware-domain review and PHX-PISONET interface review. No route change, copy, move, cherry-pick, rebase or merge is authorized.


## UTC11 — Hardware stack and destination routing hold (2026-11-18)

No Hardware candidate was copied, moved, cherry-picked, rebased, merged or assigned a new route. The current branch families overlap:

- #321 (#317 child) and #322 (#320 child) share four output-preload source/test paths but have different ancestry.
- #323 and #324 are siblings of #322; both edit the ESP32/ESP8266 sketches and poll-loop lab. #323 already applies outputs OFF before both persistence attempts; #324 adds a direct marker-open output-state assertion and mutation that #323's current lab lacks.
- #318's current base SHA `3ed38225...` is not current #317 head `fce915c...`; exact-head CI for #318 `5af39837...` is absent.

PHX-HARDWARE must select the canonical branch family and explicitly decide whether to port #324's regression into #323. PHX-QA owns the stale `Missing poll signature check` fixture. PHX-RELEASE owns COE #35's `exit 125` test/workflow mismatch and sandbox runner request. PHX-MASTER owns only this provenance and routing record.

COE #26 remains at `b382d233...`, five queued workflows / zero jobs. COE #35 current head `ad69c4e9...` has a packaging assertion failure and mandatory sandbox failure. COE #45 is a separate candidate and must not be treated as integrated into #26. Existing COE #36–#43 candidates remain draft-only pending source, license/NOTICE, import completeness, QA and exact-head integration review.

The unchanged `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`, PHX-MASTER target null. Private Drive registry v11/newer corrections are unavailable through the current connector surface; no older Library snapshot substitutes for them. No migration is proposed.

## 2026-11-18 UTC12 — no migration; refreshed owner candidate and sandbox hold

PHX-HARDWARE selected #322 → #323 as a review-candidate stack in control-plane comment 6978026438. #323 current PR/docs head is 0975fe4416daa72c097d3fee2b631950eb64908c; source/test SHA is 176ad50da2180ee085e2fb63ddb23d17b53dd63d. Both board sketches now inhibit outputs before secondary NVS/EEPROM and LittleFS persistence; focused exact-head source-extracted CI passes. Full validation still fails at the QA-owned positive poll-signature string assertion. The current #323 PR description still cites older source/docs SHAs and must be refreshed by PHX-HARDWARE, not Master.

#324 remains a sibling draft on #322 and is diverged from #323; #323 now includes the direct pre-persistence output-inhibit regression. Hardware owner must reconcile #324's remaining five-path delta. #321/#322 are also divergent; #318 has no exact-head CI and is nonmergeable. No branch was rebased, merged, closed or composed.

COE #35 current head ddca6f07c04b6d3772b1f4a55826fce0bbf742d6 has passing case/shared validation, but its mandatory sandbox fails closed at the pre-provisioned bubblewrap availability check because bwrap is absent (exit 125); sandbox packaging tests are skipped. Infrastructure must provide an authorized namespace-capable runner with bubblewrap preinstalled, without privileged install or fallback.

COE #26 remains at b382d233ff06c8791b1028bed3c617cc7b670d12 with five queued workflows and zero jobs. #36–#43 remain separate INTERCON candidates; #45 remains a separate CORE candidate. No file was copied, moved, overwritten, renamed, rebased, merged or deleted. OWNERSHIP_ROUTES.json remains unchanged at e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER target null.

Private Drive registry v11 and newer corrections remain BLOCKED: no Google Drive connector was exposed and Library search did not return the canonical file. The Cloud Artifact Policy and Storage Recovery Handover were read; the policy requires BLOCKED rather than a simulated transfer. No older registry was substituted and no private contents were published. COE root AGENTS.md returned 404.

## 2026-11-18 UTC14 — no migration; current Hardware source/test mismatch

The ownership manifest remains unchanged at blob e4db324315a1b3543fec17a148fbf960170fcb29, status DRAFT_REVIEW_ONLY, with PHX-MASTER target null. It is a review map, not a copy/move instruction.

Do not stage or copy the current #323 ESP8266 local boot-polarity test as an accepted implementation. At exact head 9cd889ec184c81d96569d3994602da3076efb537, the sketch blob 8e79b9eb8856e67d966f4c6385f89fccdc8be7fc lacks the ConfigV3/local-polarity implementation expected by test blob f08e1aadc40acf09e08ad055c92a38073c33f6c2; workflow blob dd2692df58c5311ad5d365a5539279da2018d8f7 folds the second test command into the first shell command. This exact mismatch must be corrected and independently verified before any per-file migration comparison can treat the new lab as included test coverage.

Migration remains blocked on exact source/destination blob comparison, license/NOTICE review, complete import inventory, test identity and exact-head CI, owner assignment, and the private Drive registry/sync-ledger read. No source or destination files were moved, copied, renamed, deleted, overwritten or rebased.

**Governance hold:** Experiments main, development, Master and COE main currently report protected=false / protection.enabled=false, with no repository rulesets returned. Repository administrator must establish and verify branch protection and required checks before release or financial integration.

## 2026-11-18 UTC14 — destination hold refresh

No destination move is authorized. COE #26 remains OPEN / DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12 against COE main a6513ab4412b4c014eee2863e45cbe32d06cb243, with five queued workflows and zero jobs. COE #35 is a Release-owned sandbox/packaging candidate, not a migration destination. Source/test/license provenance and role ownership must be reviewed before any staging proposal. The private Drive v11 registry and newer corrections are unavailable; older Library snapshots are not a substitute. OWNERSHIP_ROUTES.json remains DRAFT_REVIEW_ONLY with PHX-MASTER target null.



## 2026-11-18 UTC15 — migration hold after ConfigV3/board-parity audit

The current routing manifest remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, with PHX-MASTER target null. No route is a copy/move command. COE main is `a6513ab4412b4c014eee2863e45cbe32d06cb243`; integration #26 is `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN/DRAFT, five workflows QUEUED and zero jobs.

Current Hardware #323 source candidate `bc0447f013698a2e45c154b0ae69a098b0e75fe5` contains ESP8266 ConfigV3 but its boot-polarity failure-latch lab fails; ESP32 source blob `bd74b11c1496b0943404ff387ee72bb45d4743e5` does not provide equivalent unknown-polarity boot authority. Do not stage these firmware files as a verified parity set. Before any future proposal, compare exact source/destination blobs and modes, complete tests/imports, license/NOTICE scope, and exact-head CI with role-owner and independent QA review.

Private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections remain unavailable through the complete accessible Library listing and no Google Drive connector is exposed. No older registry was substituted; no private IDs/content published. No files were copied, moved, renamed, deleted, overwritten or rebased. **Migration BLOCKED / PRODUCTION NO-GO.**


## 2026-11-18 UTC16 — exact #323 to COE #26 provenance hold

The manifest remains e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, with PHX-MASTER target null. It is a review map, not a copy/move instruction.

Current #323 head 988904e8bcd058b62a9fac4aa6319a9b7c5b2470 (source/test tree 359bd8f...) is not byte-identical to COE #26. ESP32/ESP8266 source blobs 7ebf0d34... / 312884c5... differ from destination 3cc7ec54... / c8be98f7.... The new ESP32 boot lab 17f45e30..., ESP8266 boot lab db0ac511... and dual-store lab 25f5e8bd... are absent at the destination. The COE generic Hardware test f921c56c... still requires positive poll-signature strings, and workflow fe79adbd... does not invoke the new labs.

Source main/dev poll producers 2e3a1430... / db58041c... emit member-route signatures but no signed poll response; COE #26 destination producer 0a71c4e2... defines vendo_poll_sig. This is an interface divergence, not a safe file-copy candidate. Source project MIT license 1ee55b94... matches Pisowifi/LICENSE, but no Hardware-scoped LICENSE/NOTICE or COE root LICENSE/NOTICE exists at the inspected ref. Import inventory, test identity, producer/consumer contract and license scope remain incomplete.

COE #26 remains OPEN/DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12, five workflows QUEUED / zero jobs. No file was copied, moved, renamed, overwritten, rebased or deleted. No destination staging change is proposed.


## Hardware destination license/test gate — 2026-11-18 UTC17

The manifest still maps Experiments `esp32/` and `esp8266/` into COE `Hardware/esp32/` and `Hardware/esp8266/`, but the current #323 candidate is not yet present byte-for-byte in #26. The source project MIT license is at `experiment/openwrt/BlazePwifi/LICENSE`; COE #26 carries the identical blob only at `Pisowifi/LICENSE`, with no root or Hardware-scoped LICENSE and no imported source `NOTICE.md`. The destination has two different firmware blobs, a different generic test and none of the 17 source board labs. Do not recursively copy or infer legal/test equivalence. Require owner-approved per-file source/test/license mapping and exact-head QA before any destination change. Full details: [UTC17 audit](HARDWARE323_CONFIGV3_LICENSE_AND_TEST_IMPORT_GAP_AUDIT_20261118_UTC17.md).


## UTC17 child-candidate / release safety update — 2026-11-18

Hardware #326 is now an active child of #323 with two firmware blobs and two source-extracted labs changed. Its latest focused and Full CI are still running; the earlier head failed mutation-anchor assertions. Keep #326 review-only until terminal exact-head CI and independent QA. This does not change the COE #26 source/destination blob, 17-lab import, or license/NOTICE gaps above.

COE #35 current head `462d02fb01e689556efcf5bf1019af951807b130` fails the injected parent-symlink staging regression and still cannot run mandatory packaging under bubblewrap on the hosted runner. No destination migration or release approval follows from this work.


## Latest UTC17 exact-head CI correction — 2026-11-18

Hardware #326 current head `28e13fc82a250821e815fd84b5fd61f1769e7106` has focused labs passing but Full validation fails at `Missing poll signature check`; it is not QA-accepted or hardware-accepted. COE #35 current head `91691a377af5fa4251c0f4695dbf4c4484305f83` has shared 102-test and case-collision CI passing, including the symlink-swap staging regression, but mandatory sandbox remains blocked by missing bubblewrap. COE #26 remains unchanged and migration-blocked.


## Live routing gate — 2026-11-18T17:39:33Z

The canonical `OWNERSHIP_ROUTES.json` blob remains `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, with PHX-MASTER target null. It was read at Master head `97c895b699533ec4fd552f433c54210f808eb944` and is not modified by this follow-up. COE #26 remains `b382d233...`, five workflows queued / zero jobs. Current Hardware #326 source/test and COE #26 firmware/test/license trees are not equivalent; 17 source Hardware labs remain absent from the destination and license/NOTICE scope remains unresolved. No copy, move, overwrite or destination proposal is authorized.

The canonical private Drive v11 registry and newer corrections remain unavailable through the exposed tools. Do not substitute v7 or publish private registry material. Preserve all source refs and ask the registry custodian for authorized access.



## 2026-11-18 UTC18 — Hardware #327 / COE #26 exact provenance correction (2026-11-18T18:52Z)

The route manifest remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, with PHX-MASTER target `null`. No route authorizes a recursive copy or move.

Current Hardware source candidate is #327 docs head `0a26468022d25746fdc38525c0c0979da098f6d4` with source/test SHA `e774420c3404141ffe4ec7b9c002c14d3c2286b8`, stacked on #326 `58c558fb...` and #323 `988904e8...`. COE #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`. Exact firmware blobs differ: source ESP32 `ada9723c...` vs destination `3cc7ec54...`; source ESP8266 `dde063b1...` vs destination `c8be98f7...`.

Source has 18 Python board labs (11 ESP8266 + 7 ESP32); COE #26 has no corresponding Hardware lab files and only one generic Hardware shell test `f921c56c...`. That test still asserts positive response signature/poll strings; the current source consumer is deny-only. Destination `pisowifi-ci.yml` `cf18705f...` runs Pisowifi intake/tests only and does not invoke Hardware. Five #26 workflows remain queued with zero jobs. No exact-head combined destination acceptance exists.

License-path correction: project MIT LICENSE `1ee55b94...` matches COE `Pisowifi/LICENSE`; qrcode LICENSE `150770c0...`, TailAdmin LICENSE `cb92d417...`, and TailAdmin NOTICE `f0425bb...` also match their corresponding source/destination vendor paths. The vendor NOTICE is present; the source project-root NOTICE was not found. COE root LICENSE/NOTICE and Hardware-scoped LICENSE/NOTICE are absent. Because Hardware is a sibling of Pisowifi in COE, the intended scope of the Pisowifi project license over Hardware is unresolved and requires owner/legal confirmation.

This narrows and corrects the previous UTC17 notice wording; it does not clear the license-scope gate. Keep the destination blocked until per-file owner-approved source/test/license/import mapping and exact-head destination CI are independently reviewed. No copy, move, overwrite, rebase or deletion occurred.



## UTC21 exact Hardware destination provenance refresh

Source tree: Experiments Hardware candidate #327 head `c51271938c15e13998d1c99f1d311ca777bb1cc2`. Destination tree: COE integration #26 head `b382d233ff06c8791b1028bed3c617cc7b670d12`.

- Source contains 18 Python board-lab files across ESP32/ESP8266; destination Hardware contains zero corresponding Python board labs.
- Both firmware sketches are present but byte-different: ESP8266 source blob `4d73c5dc451c29f2ffd64a5cb2d230cc84a78ed5` vs destination `c8be98f72596681e36a3ad1f8939bf8046c96887`; ESP32 source `ada9723c5f07879775284eb128a986ac865394f7` vs destination `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.
- Destination generic test blob `f921c56cecc19cab1989507b9b4ade1f45dac54e` requires positive response_sig and poll strings; destination workflow blob `fe79adbdb3745a22c5ef6d1f0c87c868b7785793` invokes it. Current source Full validation is deny-only and fails at the inherited positive poll-signature fixture.
- **NOTICE correction:** current source root NOTICE.md exists (blob `f6d92cd21465312be5993631fe26977219be0fb9`) and COE #26 has no corresponding root NOTICE. The earlier statement that source root NOTICE was absent is superseded. TailAdmin vendor NOTICE remains byte-identical. The source MIT LICENSE blob matches COE Pisowifi/LICENSE, but sibling-directory scope over Hardware remains unresolved.
- COE #26 has five queued workflows and zero jobs.

No destination staging file was changed. The ownership manifest remains `DRAFT_REVIEW_ONLY` and PHX-MASTER destination remains null. Do not copy, move, overwrite, rebase or propose a migration until exact per-file provenance, license/notice scope, test identity, import completeness and destination CI are reconciled by the owners.


## UTC21 current Hardware source / COE #26 destination provenance hold

Current Hardware PR #327 head is `b346eba3ebee228abcff03456deb7889f2d39144`; COE integration #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`. The ownership manifest remains unchanged at `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, PHX-MASTER target null.

| Artifact | Experiments #327 | COE #26 |
|---|---|---|
| ESP8266 sketch | `4d73c5dc451c29f2ffd64a5cb2d230cc84a78ed5` | `c8be98f72596681e36a3ad1f8939bf8046c96887` |
| ESP32 sketch | `ada9723c5f07879775284eb128a986ac865394f7` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` |
| Hardware test | source-extracted Python labs; current poll-loop lab `c3e34297...` | generic shell test `f921c56c...` |
| CI entrypoint | source-extracted board labs | workflow `fe79adbd...` invokes generic shell + Shared tests, not source labs |

The source tree has 18 ESP32/ESP8266 Python board labs; #26 has zero corresponding Hardware Python labs. Its generic test still requires positive `response_sig` and `|poll|` strings, inconsistent with the current deny-only source consumer. Source project MIT LICENSE matches COE `Pisowifi/LICENSE`, but sibling `Hardware/` license scope remains unresolved; source root NOTICE exists and COE root NOTICE is absent. No destination route or file mapping is approved. Do not copy, move, overwrite, rebase or promote until per-file blob/license/test/import completeness and exact-head destination CI are reviewed by owners.

## PHX-MASTER UTC22 live exact-head update — exact source/destination provenance (2026-11-18T22:51:38.802Z)

Source #327 PR head f9d1fa165ccc94b18aeac7e85ffd83c29899463f (source/test ed667e88f6844284834ebd3a337dfce07a817e8c); destination COE #26 head b382d233ff06c8791b1028bed3c617cc7b670d12.

| Artifact | Experiments #327 | COE #26 | Result |
|---|---|---|---|
| ESP8266 sketch | cd1acb1da298d4f9598e943dae05918b088e5363 | c8be98f72596681e36a3ad1f8939bf8046c96887 | DIFFERENT |
| ESP32 sketch | ef498761e46d37134730dd41de1cc322d5d443e8 | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 | DIFFERENT |
| Python board labs | 19 ESP32/ESP8266 Python labs | 0 Hardware Python labs | INCOMPLETE |
| COE Hardware test | source-extracted board labs | Hardware/tests/test_firmware_hardening.sh blob f921c56cecc19cab1989507b9b4ade1f45dac54e | Different test identity |
| COE workflow | source labs run by source workflows | hardware-ci.yml blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793 | Does not invoke source labs |

COE's shell test still positively greps for response_sig and |poll|; current source is deny-only. COE #26 has five queued workflows and zero jobs.

### License / NOTICE scope

- Experiments experiment/openwrt/BlazePwifi/LICENSE and COE Pisowifi/LICENSE are byte-identical blob 1ee55b94183417be977ca287cd7391f9a6f7e721.
- Experiments root NOTICE.md exists (blob f6d92cd21465312be5993631fe26977219be0fb9); COE root NOTICE.md is absent.
- COE Hardware/LICENSE and Hardware/NOTICE.md are absent. Pisowifi/LICENSE is in a sibling directory; its intended scope over Hardware is unresolved.
- QR-code and TailAdmin vendor LICENSE/NOTICE blobs match; that does not resolve root/Hardware scope.

No copy, move, overwrite, rebase or migration proposal. OWNERSHIP_ROUTES remains DRAFT_REVIEW_ONLY, Master destination null.

## Development-branch authority reconciliation — 2026-11-18 UTC23

Live refs:
- Experiments default main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Control-plane development label: blazepwifi-v0.5.3-development at aad3aade72c1156eecba1fed30907c6d0283b2c5; GitHub compare says 293 commits behind main and 0 ahead. Its branch handover is dated 2026-10-06.
- Comparison branch: blazepwifi-v0.6.0-audit-foundation at 2fbd2475e9f54878c316fa7cea2f228386b0e859; GitHub compare says 1,876 commits ahead and 22 behind main (diverged). Control-plane issue #172 labels it comparison-only, while its branch-local handover/policy still describes v0.6 as active. The old Experiments PR #30 is closed at head 9df0a7e7 and is not the current branch head.
- No literal branch named development appeared in the live branch listing.

**Routing decision:** no product implementation branch is selected or promoted by PHX-MASTER. The control plane is the current routing authority, but the stale v0.5.3 handover and conflicting v0.6 branch handover require a product-owner reconciliation before source migration or branch promotion. Do not use either snapshot as a destination source merely because its name or handover says development.

GitHub branch API reports protected=false for Experiments main, v0.5.3-development, v0.6.0-audit-foundation and COE main. The repository rulesets endpoint returned an empty list. Effective required checks/protection must be verified by the repository administrator; PHX-MASTER did not change settings.



## PHX-MASTER UTC01 — release stack ancestry and destination hold (2026-11-19)

The existing routing manifest is unchanged: blob e4db324315a1b3543fec17a148fbf960170fcb29, status DRAFT_REVIEW_ONLY, PHX-MASTER target null. This refresh is coordination-only.

### COE Release stack

- Parent #31: 59ed44d0b911e176f1a95b9cf5585ef811ffd31b, based on COE integration #26 b382d233ff06c8791b1028bed3c617cc7b670d12.
- Release #35 current head: 3455e0ce56bed780a727a6297db14a8e1d345f99; source/test head 5e25e4ceab7c0615bcdad8309d50739e6b255f46.
- ULA child #44 current head: 582fd5d5e83e36b36546ac28534740298ba94af4; base is earlier #35 commit 1a5be48d2845781b0b07bad39a37f8440cea4d4.
- Compare current #35 head to #44 head: #44 is 15 commits ahead and 13 commits behind. The branches are divergent siblings, not one verified integrated release stack.

The #35 overlay-accounting fix is present in the current #35 source/test lineage but is not inherited by #44's current base. #44 contains the ULA provisioner and related tests. PHX-RELEASE must reconcile the branch ancestry using normal history-preserving operations; PHX-MASTER did not rebase, merge, cherry-pick, force-push or change either branch.

### Site identity and migration decision

#44 generates a random ULA prefix per installation and verifies UCI persistence. This does not establish the Master same-site shared-prefix requirement. CORE must provide site-level assignment authority; QA must test same-site and different-site appliances plus reboot/upgrade/restore; HARDWARE must verify target behavior. No replacement prefix is invented.

COE #26 remains OPEN/DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12, with five queued workflows and zero jobs. No new destination staging was reviewed in this activation, so no copy/move/overwrite proposal is made. Exact source blobs, license scope, test identity, import completeness and destination CI remain mandatory before any route is accepted.

### Branch-source authority

Experiments main is f4e8a891aed8af86d5fd315d28750a0ac3a7372b; named v0.5.3 development is aad3aade72c1156eecba1fed30907c6d0283b2c5 (293 behind/0 ahead); v0.6.0 audit foundation is 2fbd2475e9f54878c316fa7cea2f228386b0e859 (1,876 ahead/22 behind). The current #172 body has conflicting development labels. No branch promotion or migration source selection is authorized by this report.


## PHX-MASTER UTC02 — COE #35 toolchain drift and current #44 ancestry (2026-11-19)

COE #26 is b382d233ff06c8791b1028bed3c617cc7b670d12 on main a6513ab4412b4c014eee2863e45cbe32d06cb243. Release #31 is 59ed44d0b911e176f1a95b9cf5585ef811ffd31b. Current #35 is 4843580ec9d901fda523bbf4c29f69e3745c698a, based on #31. ULA #44 is 582fd5d5e83e36b36546ac28534740298ba94af4, based on older #35 commit 1a5be48d2845781b0b07bad39a37f8440cea4d4. CORE #45 is 9d76a134c1f6512aa40c20ec4d247306a71a8cce, separate candidate.

Compare #35 → #44: DIVERGED; #44 is 15 ahead / 16 behind current #35, merge base 1a5be48d2845781b0b07bad39a37f8440cea4d4. Earlier 15/13 count is stale. RELEASE owns history-preserving reconciliation; Master did not alter either branch.

Experiments #327 source sketch blob ef498761e46d37134730dd41de1cc322d5d443e8 differs from COE #35 destination blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422. Source CI #44439616677 resolved ESP32 core 3.3.13 and compiled; COE #35 #44443780617 resolved 4.0.0 and failed because mbedtls/sha256.h was not found. Both workflows are unpinned. RELEASE pins; HARDWARE owns compatibility; QA verifies. Do not claim compatibility from unpinned source CI.

COE #35 case #44443780675 passes; sandbox #44443780613 fails closed because bwrap is absent after 14/14 host-preflight tests (exit 125). COE #26 remains five queued workflows / zero jobs. No staging, copy, move, overwrite or migration is proposed.

Experiments main remains f4e8a891aed8af86d5fd315d28750a0ac3a7372b. v0.6.0 is 2fbd2475e9f54878c316fa7cea2f228386b0e859 (1,876 ahead / 22 behind); v0.5.3 is aad3aade72c1156eecba1fed30907c6d0283b2c5 (0 ahead / 293 behind). No product branch is promoted by Master. OWNERSHIP_ROUTES.json remains e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, Master target null.


## UTC03 — exact Hardware source/destination provenance gate (2026-11-19)

COE #26 remains a draft candidate at b382d233ff06c8791b1028bed3c617cc7b670d12; Experiments #327 is at 11fae729df415cc26b9e1675b1758cd8e4d22648. These refs are not interchangeable.

| Item | Experiments #327 source | COE #26 destination | Result |
|---|---|---|---|
| ESP8266 sketch | 1b32cb90be11da79ba7ea1155f128aee9e495dd2, 67,300 bytes | c8be98f72596681e36a3ad1f8939bf8046c96887, 18,394 bytes | Different blob |
| ESP32 sketch | f54805b17cac45388dfacc5e65eff9b731234316, 60,326 bytes | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422, 18,505 bytes | Different blob |
| Source test corpus | Eight Python source-extracted labs in #327 | One Hardware/tests/test_firmware_hardening.sh (4,118 bytes) | Incomplete / different test identity |
| Hardware behavior | acceptPollResponse() returns false; no positive |poll| token | Old positive-presence grep for response_sig, |register| and |poll| | Contract conflict |
| Toolchain | #327 latest ESP32 compile succeeds on core 4.0.0 after explicit Mbed TLS 3/4 branch | #26 workflow floats core versions; README says ESP32 3.3.12 / ESP8266 3.1.2 | Not reproducible |
| License | BlazePwifi/LICENSE | Pisowifi/LICENSE | Same blob 1ee55b94183417be977ca287cd7391f9a6f7e721 |
| Hardware license/notice | Source NOTICE not found at inspected root | Hardware/LICENSE and Hardware/NOTICE.md absent | Scope unresolved |

The #26 description was edited at 2026-11-19T03:44:46Z to state that the licensing/privacy gate is resolved and software readiness is 95%. The exact source/destination file review does not establish Hardware license/NOTICE scope, and the five #26 workflows remain QUEUED with zero jobs. These narrative claims are not migration evidence.

### Toolchain and release lineage

COE #35 current head a270b547fb5ff570bd2bc49c2e96219043d7c9bd has release-owned pins: Arduino CLI 1.6.0, ESP8266 3.1.2, ESP32 3.3.13, immutable setup action b3cda96fddef6af6c56b4c5efb5c47e2357935db and runtime checks. Shared #44451317780 and case #44451317996 pass; sandbox #44451317807 fails closed because bwrap is absent. This pinning is not present in COE #26.

COE #44 remains based on older #35 commit 1a5be48d2845781b0b07bad39a37f8440cea4d4 and is 15 ahead / 21 behind current #35. Its packager generates a 40-bit random RFC 4193 ULA ID per installation. It does not establish a site-level distribution authority for multiple appliances. PHX-RELEASE owns history-preserving reconciliation; PHX-CORE owns site identity semantics; PHX-QA owns independent tests.

### Staging decision

Do not copy, move, overwrite, cherry-pick, rebase, or stage any Hardware files into COE #26. Required before staging: exact path/mode/blob map; complete eight-lab import or reviewed equivalent; replacement negative/default-deny tests; exact pinned toolchain; destination CI with actual jobs; explicit Hardware license/NOTICE scope; reversible rollback proof; and subsystem-owner acceptance. Keep OWNERSHIP_ROUTES.json unchanged at e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER target null.


## PHX-MASTER UTC04 — exact Hardware provenance and local/financial migration boundary (2026-11-19)

Current Experiments Hardware #327 branch/docs head is e799b0f042889b97ba7bae2ae2e06c1ec76392d6, a documentation-only commit recording the Mbed TLS 3/4 evidence. Its firmware source commit is 11fae729df415cc26b9e1675b1758cd8e4d22648 and source/test lab head is 071a711d6598c67124e84ffd995fd48aa7d9f054. The #327 PR body still identifies a3597125 as current head; the latest Hardware control-plane comment identifies e799b0 correctly. HARDWARE owns the PR description correction.

### Exact source/destination blobs at current refs

| Platform | Experiments #327 | COE #26 |
|---|---|---|
| ESP8266 | 1b32cb90be11da79ba7ea1155f128aee9e495dd2 / 67,300 bytes | c8be98f72596681e36a3ad1f8939bf8046c96887 / 18,394 bytes |
| ESP32 | f54805b17cac45388dfacc5e65eff9b731234316 / 60,326 bytes | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 / 18,505 bytes |

Both platform pairs differ. Source acceptPollResponse() returns false and preserves default-deny. The COE #26 shell test blob f921c56cecc19cab1989507b9b4ade1f45dac54e positively requires response_sig, |register| and |poll| strings; this is not behavior/test parity with the source contract.

The source-side Hardware PR contains eight Python labs. config_load_read_failure_lab.py blob 40dfa46e48d8288bf94ad8c5579bf0d7436d4df6 is invoked by coin_pulse_capture_lab.py blob cdc6d85aed5e5a0c85b154afa67c302023ec20b9, which is invoked by the quarantine workflow. Exact run #44453718564 job 135323579699 logs confirm the lab executed. This is local ESP8266 EEPROM configuration v1/v2-to-v3 recovery only; the lab itself emits FINANCIAL_MIGRATION_TESTED=0 and PHYSICAL_POWER_CUT_VERIFIED=0. It is not evidence for the financial ledger v1-to-v2 migration.

### License and build provenance

Source BlazePwifi/LICENSE and COE Pisowifi/LICENSE are the same MIT blob 1ee55b94183417be977ca287cd7391f9a6f7e721. COE Hardware/LICENSE and Hardware/NOTICE.md return 404 at #26. The Pisowifi license does not by itself establish the Hardware subtree's license/NOTICE scope.

COE #26 hardware-ci.yml blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793 installs unversioned ESP8266/ESP32 cores; Hardware/README.md blob 99af3e5b46cd8b6f35c6479b204683f60c55ebcb documents ESP32 3.3.12 and ESP8266 3.1.2. The pinned #35 toolchain does not flow into #26. All five #26 workflows remain QUEUED with zero jobs.

### Staging decision

Do not copy, move, overwrite, cherry-pick, rebase, or stage any Hardware files into COE #26. Before a future proposal, require per-file path/mode/blob provenance, complete eight-lab import or reviewed equivalents, default-deny negative tests, explicit Hardware license/NOTICE scope, pinned CLI/core/FQBN/options, exact-head destination CI, reversible rollback evidence and Hardware/QA/Release owner acceptance. Keep OWNERSHIP_ROUTES.json unchanged at e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER target null.

RELEASE #291 also remains blocked by the shared PROJECT_HANDOVER.md freshness gate after release workflow changes. CORE and RELEASE must coordinate the canonical handover update; Master does not edit CORE-owned handover files.


## PHX-MASTER UTC06 — exact Hardware staging and release-stack gate (2026-11-19)

Current source candidate: Experiments #327 at ba4c0cb0c5eae4be5e014c0df6f5abe20a67b0bf; source/test commit 0e5514adb0088649eca8bec9df6215faa50b556c. Current destination candidate: COE #26 at b382d233ff06c8791b1028bed3c617cc7b670d12. COE main remains a6513ab4412b4c014eee2863e45cbe32d06cb243.

**No destination staging is approved.** The ESP32 source blob c29483f0761ca6e2db0573bd12d6bfa502f12434 (61,807 bytes) differs from destination 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 (18,505 bytes); ESP8266 source 1b32cb90be11da79ba7ea1155f128aee9e495dd2 (67,300 bytes) differs from destination c8be98f72596681e36a3ad1f8939bf8046c96887 (18,394 bytes). The source now has explicit Mbed TLS 3/4 selection and unsupported-major rejection; the destination has no major guard and retains a positive poll-signature consumer.

The #327 source/test inventory contains nine Python lab files in the current PR diff. COE #26 has one generic Hardware shell test with positive response-signature assertions, and its five workflows have zero jobs. The destination hardware workflow uses unversioned board-core installs; the README's ESP32 3.3.12 statement is not enforced. COE #35 pins are separate and are not inherited by #26.

Source and destination MIT license texts match at blob 1ee55b94183417be977ca287cd7391f9a6f7e721, but COE Hardware/LICENSE and Hardware/NOTICE.md are absent. Do not infer Hardware redistribution scope from Pisowifi/LICENSE.

Before any future migration proposal, require:
1. Exact per-file source path, destination path, mode, blob SHA and size.
2. Complete source test import inventory with owner-reviewed equivalents; preserve the negative/default-deny poll contract.
3. Explicit Hardware license/NOTICE scope from the responsible custodian.
4. Pinned Arduino CLI, ESP32/ESP8266 core, FQBN and build options on the actual #26 destination branch.
5. Runnable exact-head destination CI with all five workflows executing, not queued.
6. Reversible rollback/migration evidence and independent QA at the identical proposed SHA.
7. Hardware, QA and Release owner acceptance; no inference from #35, #39–#43 or other sibling branches.

COE #35 is 108 commits ahead of parent #31. COE #44 is 15 ahead / 25 behind #35 and mergeable=false. RELEASE owns history-preserving reconciliation. INTERCON #39/#40/#42 and #41/#43 remain distinct alternatives; no canonical Stage-3/Stage-4 candidate is selected.

Keep OWNERSHIP_ROUTES.json unchanged at e4db324315a1b3543fec17a148fbf960170fcb29, status DRAFT_REVIEW_ONLY, PHX-MASTER destination null. Do not copy, move, overwrite, cherry-pick, rebase or merge any subsystem files.

## PHX-MASTER UTC07 — poll-deny fixture and release-handover routing (2026-11-19)

**No source migration or staging is approved.** Experiments #327 remains the source candidate at 31f5d727... (source/test c3733843...); COE #26 remains the destination candidate at b382d233... on COE main a6513ab4.... Exact ESP8266/ESP32 source blobs 1b32cb90... / c29483f0... differ from destination blobs c8be98f7... / 3cc7ec54.... The source's deny-only poll/disposition behavior and nine source Python labs plus helper are not equivalent to the destination's one generic positive-presence shell test.

**Route QA:** replace the source-side legacy v05_firmware_hardening_test.sh positive |poll| assertion with source-exact negative/default-deny tests. Keep poll_response_failclosed_lab.py in the Full validation path; its current focused quarantine execution passes 11/11 poll-response cases per board. Do not modify the firmware to satisfy the old string check.

**Route RELEASE:** PR #291 remote branch/PR head is 3ef73265.... Issue progress references b8f4e361..., but that commit is not the branch head and changes only .github/PHX_RELEASE_HANDOVER.md. Exact current #291 Windows and BlazePwifi validation fail at the product handover freshness gate. RELEASE must update the authoritative product handover/current state/change ledger after its workflow changes and rerun the current branch; Master does not edit release or CORE handover files.

**COE #26 admission remains closed** until exact path/mode/blob provenance, full source test import or reviewed equivalents, explicit Hardware license/NOTICE scope, pinned CLI/core/FQBN/options on #26 itself, five runnable exact-head workflows, reversible rollback evidence and Hardware/QA/Release owner acceptance. #35's pins and CI do not transfer to #26; #44 remains diverged 15/25 and Release-owned.

Keep OWNERSHIP_ROUTES.json SHA e4db324315a1b3543fec17a148fbf960170fcb29 unchanged, status DRAFT_REVIEW_ONLY, PHX-MASTER destination null. No copy, move, overwrite, cherry-pick, rebase or merge. Private registry v11 and newer corrections remain BLOCKED because no authorized Google Drive connector is available in this runtime; no private contents or identifiers are published.


## UTC08 destination staging recheck — 2026-11-19

The current routing manifest remains unchanged at blob e4db324315a1b3543fec17a148fbf960170fcb29. It is DRAFT_REVIEW_ONLY and PHX-MASTER has no runtime destination. COE #26 remains the only integration draft candidate, not an approved copy plan.

At exact source #327 head c62af73ec5b45cd87f4c8f3295ede18f307fb359 and destination #26 head b382d233ff06c8791b1028bed3c617cc7b670d12, both board sketch blobs differ in SHA and size. The source has 22 board-local Python lab files; destination Hardware contains one generic shell test whose positive response_sig/register/poll assertions conflict with the current deny-only source. The source BlazePwifi/LICENSE and destination Pisowifi/LICENSE match, but Hardware/LICENSE and Hardware/NOTICE.md are absent. Five destination workflows remain queued with zero jobs. Do not copy, move, overwrite, retarget, or infer completion from the representative routing table.

Release #291 is also not a destination admission signal: its live head d498af has 12 commits beyond the b8f4 SHA named in the UTC08 role checkpoint, and exact-head handover gates fail. No migration staging was changed.


## UTC10 exact Hardware destination recheck — 2026-11-19

The manifest remains unchanged at `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, with PHX-MASTER destination null. COE #26 remains a draft candidate, not a copy plan.

At source PR #327 head `47eceaf2ccd3cfdc3403df6b1964610bd32ed24f`, the source ESP32 sketch blob is `1e720d3b2fc76e348ff77e347e0d472d38559d04` and ESP8266 is `75f62c359bbb69f4f580b7ee0c3875396b12cc7f`. At COE #26 head `b382d233ff06c8791b1028bed3c617cc7b670d12`, destination ESP32 is `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` and ESP8266 is `c8be98f72596681e36a3ad1f8939bf8046c96887`. Neither pair is byte-identical.

The source Hardware subtrees contain 21 board-local Python labs (9 ESP32, 12 ESP8266). COE #26 Hardware contains four blobs: README, two sketches and `Hardware/tests/test_firmware_hardening.sh`. That one test still requires positive `response_sig`, `|register|` and `|poll|` source markers; current #327 poll/disposition functions both return false. Test identity/import completeness is BLOCKED.

Source `BlazePwifi/LICENSE` and destination `Pisowifi/LICENSE` match at blob `1ee55b94183417be977ca287cd7391f9a6f7e721`; destination `Hardware/LICENSE` and `Hardware/NOTICE.md` are absent, and source `BlazePwifi/NOTICE.md` is absent. The shared Pisowifi license is not a complete per-file Hardware migration record. Require explicit scope review and per-file path/mode/blob/license/test mapping before any staging proposal.

No file copy, move, overwrite, route promotion, rebase, merge, or migration staging occurred. Five #26 workflows remain queued with zero jobs.


## UTC10 ULA and Release provenance route — 2026-11-19

COE #35 packager blob `f1d9c8ef1da7e1d3df11f45dfe36f14f5f11a650` emits invalid `fd00:db8:blaze::/48`; test blob `e3f625673bd90bb28e107a88aff9ed4d824a2bb7` lacks ULA validation. Do not patch the Release-owned packager from Master or substitute another hard-coded prefix.

Route the interface decision to the existing PHX-CORE owner and COE integration owner: define one durable site-scoped RFC 4193 prefix authority, shared across appliances at one site and independent across sites, with backup/restore semantics. PHX-RELEASE implements validation/generation only after that decision; PHX-QA supplies independent tests.

Current #291 docs head is `44a2020c52af6beeaa5e6aedf089f8b03a416ed1`, source/test head `ffe4ea8f5eabe23628827e186ebb3f92c9cfcaaf`. Source/test #44503860587 and docs-head #44504554013/#44504561884 succeeded; signing/publishing skipped. Windows docs-head #44504561855 fails in PISONET-owned self-test; #291 ESP32 compatibility pins older Hardware source `0e5514adb008`, not current #327.

COE #31 sandbox fails on unprivileged UID-map permission denial despite bwrap 0.9.0; #35 fails because bwrap is missing. No privileged/unsandboxed fallback. No migration, copy, move, overwrite or route promotion.


## UTC11 ULA and destination-staging guard — 2026-11-19

The machine-readable `OWNERSHIP_ROUTES.json` remains unchanged at blob `e4db324315a1b3543fec17a148fbf960170fcb29`: `DRAFT_REVIEW_ONLY`, Experiments source `main@f4e8a891...`, COE destination PR #26 `b382d233...`, and PHX-MASTER target `null`. It is a review map, not a copy/move instruction.

COE RELEASE #44 is a release-owned first-boot ULA implementation candidate, not a new migration route. Its current head `582fd5d5e83e36b36546ac28534740298ba94af4` is based on `1a5be48...`; current COE #35 is `5047af8...`. The exact compare is diverged 15 ahead / 25 behind. Its per-appliance random first-boot ULA does not establish one shared prefix for multiple appliances at the same site. Keep #44 and #26 draft; PHX-RELEASE owns history-preserving reconciliation, CORE/COE owner selects site authority, and QA independently verifies.

No source or destination file was copied, moved, overwritten, rebased, cherry-picked, merged or staged. No route promotion is proposed.


### UTC11 exact Hardware provenance — COE #26 remains review-only

Current #327 source and #26 destination sketch blobs differ on both boards: ESP32 `528187f68aaad7d76a690bbf1cbe338165ad3839` (64,308 bytes) versus `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` (18,505 bytes); ESP8266 `aa021588b610f928f7af4f5fefb3f32114e6b5ae` (68,127 bytes) versus `c8be98f72596681e36a3ad1f8939bf8046c96887` (18,394 bytes). Source `BlazePwifi/LICENSE` and destination `Pisowifi/LICENSE` match at `1ee55b94183417be977ca287cd7391f9a6f7e721`, but source `BlazePwifi/NOTICE.md`, destination `Hardware/LICENSE` and `Hardware/NOTICE.md` are absent.

The source has 46 scripts in `experiment/openwrt/BlazePwifi/tests/` plus 22 board-local Python labs and one shared extraction helper. COE #26 Hardware has one shell test, blob `f921c56cecc19cab1989507b9b4ade1f45dac54e`; it and the legacy source hardening script still require positive `response_sig`, `|register|` and `|poll|` markers, which conflict with current #327 default-deny behavior. No test import equivalence is established. Five #26 workflows remain queued with zero jobs. No staging/copy/move is authorized.

## Live exact-head reconciliation — 2026-11-19 UTC13

### Pisonet route boundary and separate INTERCON candidates
The unchanged machine-readable route manifest maps `experiment/windows/BlazePisonet-SoftTimer/` to `Pisonet/SoftTimer/` as selective review only. It does not map `Hardware/esp8266/BlazePisonetUniversal/` or `Shared/contracts/pisonet-intercon/`.

COE #36 (base #26, head `b4d7434764aab72673de1f496ed9e442f031ddff`) and COE #43 (base `a35672fb60228fb8f84801405d032293f0266023`, head `8f5eec790dc2a3e25c219a6f51651113cd1c90cd`) are Universal/INTERCON candidate workspaces. Their Stage 1 / Stage 4 CI passes are scoped to those drafts; they do not authorize migration into `Pisonet/SoftTimer` or COE #26. Require private registry v11, explicit product identity and owner route before any route addition.

### Current source and destination refs
- Experiments main `f4e8a891...`; current development reference `blazepwifi-v0.6.0-audit-foundation@2fbd2475...`; legacy `blazepwifi-v0.5.3-development@aad3aade...` remains present but is not the current development reference.
- COE main `a6513ab4...`; integration PR #26 `b382d233...`, OPEN/DRAFT.
- Master PR #288 `d52d346e...`, OPEN/DRAFT. `OWNERSHIP_ROUTES.json` remains unchanged at `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, Master target null.

### No staging decision
COE #26 still has five queued workflows with zero jobs. Current Hardware source/destination blobs differ on both boards, 22 source board-local labs are not imported as equivalent destination tests, and Hardware license/NOTICE files are absent. No copy, move, overwrite, cherry-pick, rebase, merge, staging, or route promotion is authorized.


## UTC14 exact-head supersession — 2026-11-19T14:39:41Z — ULA release candidate and destination staging decision

COE RELEASE #35 is a packager/validation candidate, not a source-migration route. Its final docs head is `0e3662b9aef4b2a2248e3a064b07d07e9097be1b`, with source/test head `90ce4200b66ce0b55f40feaab42cc7b53fad1f2d`. The packager refuses to generate network UCI until an approved site-scoped RFC 4193 /48 is supplied. Its synthetic unit-test prefix is not a deployment value. The exact-head shared workflow passes 116 packager tests (two intentional skips), then fails closed for all 10 appliance profiles because no approved prefix exists. The sandbox fails closed because Bubblewrap is missing.

COE #44 at `582fd5d5e83e36b36546ac28534740298ba94af4` is 15 commits ahead / 29 behind #35 and GitHub marks it non-mergeable. It generates a random /48 for each appliance installation and persists it locally. That is not a same-site shared prefix authority; do not select or merge it as the §6.45 implementation. RELEASE owns branch history; CORE/COE integration owns the authority decision; QA owns independent same-site/different-site/persistence tests.

COE #26 remains the only current integration draft destination, at `b382d233ff06c8791b1028bed3c617cc7b670d12`, with five queued workflows and zero jobs. Current #327-to-#26 sketch blobs differ on both boards; source has 22 board-local Python labs while destination has one generic Hardware shell test with stale positive signature/poll assertions. Pisowifi LICENSE matches the source MIT text, but Hardware LICENSE/NOTICE scope is absent. The Universal/INTERCON #36/#43 paths remain outside the SoftTimer route.

Keep `OWNERSHIP_ROUTES.json` unchanged at `e4db324315a1b3543fec17a148fbf960170fcb29`, status `DRAFT_REVIEW_ONLY`, PHX-MASTER target `null`. No copy, move, overwrite, rebase, cherry-pick, merge, staging or route promotion is authorized.


## UTC15 exact destination provenance — 2026-11-19

Source ref is Experiments HARDWARE PR #327 API head c4954de95e319f7a2acf4bf4ee0bcae44b4b99b5 (source/test 05ddd64f0d982c32d0297010596bfa9bd46bb472). Destination is COE integration PR #26 head b382d233ff06c8791b1028bed3c617cc7b670d12. Both are OPEN/DRAFT review candidates only.

Exact sketch blob comparison:
- ESP32 source 528187f68aaad7d76a690bbf1cbe338165ad3839, 64,308 bytes; destination 3cc7ec54b476943dc04a8d1af5e2df5fe054e422, 18,505 bytes.
- ESP8266 source 5c473693a7ca1e865167217d00af90fc7645b44c, 68,018 bytes; destination c8be98f72596681e36a3ad1f8939bf8046c96887, 18,394 bytes.

The source tree contains 22 board-local Python *_lab.py files, plus a shared helper and a RED fixture. Destination Hardware contains only Hardware/tests/test_firmware_hardening.sh, blob f921c56cecc19cab1989507b9b4ade1f45dac54e. That test still greps for positive response_sig, |register| and |poll| markers; current source poll/disposition consumers return false. Destination .github/workflows/hardware-ci.yml blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793 installs unversioned ESP8266/ESP32 cores. Five #26 workflows remain queued with zero jobs.

Source BlazePwifi/LICENSE and destination Pisowifi/LICENSE match at 1ee55b94183417be977ca287cd7391f9a6f7e721. Source BlazePwifi/NOTICE.md is absent; destination Hardware/LICENSE and Hardware/NOTICE.md are absent. The Pisowifi license does not establish Hardware license/NOTICE scope.

COE #35 remains fail-closed with no approved site ULA and #44 remains per-appliance/diverged; neither authorizes a route or prefix. No copy, move, overwrite, staging, cherry-pick, rebase, merge or route promotion is approved. Keep OWNERSHIP_ROUTES.json unchanged at e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER target null.

## UTC16 live routing and migration hold — 2026-11-19

The unchanged machine-readable route manifest remains e4db324315a1b3543fec17a148fbf960170fcb29, status DRAFT_REVIEW_ONLY, PHX-MASTER target null. This Master update does not change any source/target route.

PR #291 contains cross-owner files: experiment/windows/BlazePisonet-SoftTimer/tests/ReleaseSigning/negative-selftest.ps1 is within the PISONET route, while BlazePwifi project handover files require CORE review. The release workflow may consume these tests and handovers but cannot silently assume ownership of their content. PISONET must repair its uninitialized $buildWorkflow test variable; CORE must review its handover changes.

COE #26 remains the only integration draft destination, at b382d233ff06c8791b1028bed3c617cc7b670d12, with five queued workflows and zero jobs. Source/destination board blobs differ, the 22 source board-local Python labs are not imported as equivalent destination tests, Hardware license/NOTICE scope is incomplete, and destination toolchain/CI are not verified. The ULA authority is undecided; #35 intentionally fails closed with no approved site prefix, while #44's per-appliance random Global ID is not a site-wide authority.

No copy, move, overwrite, cherry-pick, rebase, merge, staging, or route promotion is authorized. Preserve all source histories and owner branches. Require exact per-file source blob, mode, license, import completeness, test identity, toolchain and executable destination CI evidence before any migration proposal.


## UTC17 destination recheck — 2026-11-19T17:42Z

The source remains Experiments main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` with Hardware owner source/test candidate #327 at `ad421e48b2908fab48dc85b40c169450d9c0239c`. COE main remains `a6513ab4412b4c014eee2863e45cbe32d06cb243`; the only integration candidate reviewed here is existing draft #26 at `b382d233ff06c8791b1028bed3c617cc7b670d12` (205 changed paths, five queued workflows, zero jobs).

A fresh exact-blob check found ESP32 source `f89bc561b2093328286d7633da794667b2ab06de` versus destination `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`, and ESP8266 source `284f4337bc9e2aa4d78c61f0d7e4c4163ffb0a82` versus destination `c8be98f72596681e36a3ad1f8939bf8046c96887`. Both pairs differ materially in bytes and size. Source contains 24 board-directory Python files (helpers/RED fixture included); COE Hardware contains one generic shell test with positive poll marker expectations that conflict with current source deny-only poll behavior.

The source BlazePwifi LICENSE and destination Pisowifi LICENSE match at `1ee55b94183417be977ca287cd7391f9a6f7e721`; source NOTICE, Hardware LICENSE and Hardware NOTICE are absent. This is not a complete Hardware license review. No copy, move, overwrite, rebase, cherry-pick, merge, staging or route promotion is authorized. The private v11 registry and newer corrections remain required before any artifact or migration write.


## UTC18 — COE intake manifest scope and firmware/test provenance hold — 2026-11-19

The current COE #26 Pisowifi/SOURCE_INTAKE.json blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f is a schema-v8 intake record for historical source commit 6d4c9b487af4d768c4d7627654d119417fcc6e00, project root experiment/openwrt/BlazePwifi, and destination root Pisowifi/. Its 61-file/47-identical/14-derived/zero-unrecovered summary applies to the declared OpenWrt rootfs scope; its two unchanged original tests do not prove import of the current 38-entry source test tree or any Hardware firmware/test tree.

Current-main source and COE #26 Hardware firmware blobs are non-identical on both boards. ESP32 source main 117c6e937e8f12f3890ace2ae23b3a23ff1c3df0 vs destination 3cc7ec54b476943dc04a8d1af5e2df5fe054e422; ESP8266 source main bfb94920eb0a189ca01d52e5443954fa133f5423 vs destination c8be98f72596681e36a3ad1f8939bf8046c96887. The same destination blobs also differ from the source sketches at the intake's historical commit (29f1125d... and 12c4bb82...). These are derived candidates, not byte-identical copies.

For the manifest's explicit PisoWifi tests route, current Experiments main has 38 files and COE #26 Pisowifi/tests has 19. Four basenames overlap; only portal.sh is byte-identical. COE Hardware/tests contains one generic shell test. Exact per-file source/destination test identity and execution remain incomplete.

License comparison: BlazePwifi/LICENSE and Pisowifi/LICENSE match exactly at 1ee55b94183417be977ca287cd7391f9a6f7e721. Experiments root NOTICE.md exists at f6d92cd21465312be5993631fe26977219be0fb9; COE root NOTICE.md, Hardware/LICENSE and Hardware/NOTICE.md are absent at the inspected destination candidate. The Pisowifi license match is not Hardware license coverage.

**Routing disposition:** keep OWNERSHIP_ROUTES.json at DRAFT_REVIEW_ONLY, PHX-MASTER target null. Do not copy, move, overwrite, cherry-pick, rebase or merge. COE integration owner must produce a Hardware-specific intake manifest with exact source commit/tree, every source/destination blob+mode, derivation notes, license/notice scope, test identity map and exact-head destination CI; PHX-HARDWARE, PHX-QA and licensing owner review their respective scopes before any migration proposal.

## COE #26 exact per-file provenance refresh — 2026-11-19T19:38Z

Source tree: Experiments PR #327 branch phoenix/hardware-prepoll-edge-abort-20261119 at f3be11e3bd7f3f0b9e884165a42cf6b838ef2ef6. Destination tree: COE #26 branch integration/ecosystem-nonproprietary-candidate-20261111 at b382d233ff06c8791b1028bed3c617cc7b670d12. COE main a6513ab4412b4c014eee2863e45cbe32d06cb243 contains only README.md and Pisonet/README.md; #26 is staging, not completed main migration.

### Hardware path comparison

| Source subtree | Source files | Destination files | Exact identity | Missing source files |
|---|---:|---:|---|---:|
| ESP32 BlazePwifiVendo32 | 15 (1 sketch, 9 Python labs, 5 Markdown) | 1 sketch | Sketch SHA differs: f89bc561... vs 3cc7ec54... | 14 |
| ESP8266 BlazePwifiVendo | 18 (1 sketch, 15 Python labs, 2 Markdown) | 1 sketch | Sketch SHA differs: 284f4337... vs c8be98f... | 17 |

All 24 source board-local Python labs and seven board-local documents are absent from Hardware. The one destination Hardware test is a generic shell test, not a source-identical import.

### QA route comparison

Source experiment/openwrt/BlazePwifi/tests/: 47 files (38 .sh, 8 .py, 1 README). Destination Pisowifi/tests/: 19 .sh files. Same-relative-path comparison: 1 identical blob, 3 divergent blobs (config.sh, integration.sh, security.sh), 43 source-only files, 15 destination-only files. This is not complete test migration or test equivalence.

### License/notice

BlazePwifi/LICENSE and Pisowifi/LICENSE match exactly at 1ee55b94183417be977ca287cd7391f9a6f7e721. Experiments repository root NOTICE.md exists at f6d92cd21465312be5993631fe26977219be0fb9. COE root NOTICE.md, Hardware/LICENSE and Hardware/NOTICE.md are absent. Whether the root notice applies to the staged component and how third-party notices should be carried requires licensing-owner review.

### Candidate security discrepancies

At exact destination blobs, ESP32 uses LittleFS.begin(true) (line 337), ESP8266 formats after mount failure (lines 141–145), both expose unauthenticated POST /quarantine/clear deletion, both allow cfg.key empty to bypass response_sig verification because sigOk starts true and verification is conditional on a nonempty key, both call applyRemoteConfig from register/poll responses, and both clear pending evidence unconditionally after an attempted quarantine append. The current source branch instead has fail-closed journal handling and deny-only poll/coin-post disposition. The destination also uses unchecked legacy Mbed TLS SHA calls while current source supports checked Mbed TLS 3/4 branches.

Destination Hardware test blob f921c56cecc19cab1989507b9b4ade1f45dac54e requires positive response_sig and |poll| markers. Current source PR #327 Full validation independently fails on the same stale positive |poll| expectation in QA-owned v05_firmware_hardening_test.sh.

### Disposition

COE #26 remains OPEN/DRAFT with five queued workflows and zero jobs. OWNERSHIP_ROUTES.json remains DRAFT_REVIEW_ONLY; Master destination null. Do not copy, move, overwrite, cherry-pick, rebase, merge or stage. COE integration must produce the complete per-file intake map and remediate/justify the above differences; PHX-HARDWARE, PHX-QA and the licensing owner review their scopes before a new migration proposal.

---

## PHX-MASTER live exact-head refresh — 2026-11-19 UTC20

The unchanged route manifest remains `DRAFT_REVIEW_ONLY`, with PHX-MASTER target null. Source Hardware #327 head `20c73090...` versus COE #26 `b382d233...`: ESP32 16 source files / 1 destination / 0 identical / 1 divergent / 15 source-only; ESP8266 20 / 1 / 0 / 1 / 19. QA route: 47 source / 19 destination / 1 identical / 3 divergent / 43 source-only / 15 destination-only. COE #27 `009f70cc...` is a separate draft on main; its Hardware test blob is identical to #26 and it does not import the source lab set.

Source BlazePwifi LICENSE matches destination Pisowifi LICENSE, but source root NOTICE and destination Hardware LICENSE/NOTICE scope remain unresolved. Destination sketches have key-empty signature bypass, format-on-mount-failure, unauthenticated quarantine clear and pending-evidence clearing after an unverified append. No route promotion, copy, move, overwrite, rebase, cherry-pick, merge or staging is authorized.



## COE #48 Stage 5 Remote CS routing — 2026-11-19 UTC22

COE #48 head `b72ca86a141329b4b401f5d790cfb04a58423331` is 15 commits ahead of #47 `1c10f7421dfaa87fcb2ce89d4a8b2d22422d1597` and changes Hardware ESP8266 staging, its tests and a Stage 5 workflow. It does **not** change `Pisowifi/` backend code and is not part of integration #26. Its `BLZCS1` HMAC protocol is a new device adapter, not the existing `/cgi-bin/vendo` protocol. The added bridge contract is design-only; no customer-credit adapter or durable router-side event ledger exists at this head.

The existing `OWNERSHIP_ROUTES.json` remains `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, with PHX-MASTER target `null`. No route or target path changed. Do not cherry-pick, copy, rebase, move or merge #48 into #26. Before any future proposal, require explicit PHX-HARDWARE and PHX-PISONET owner acknowledgments, CORE's durable credit contract, per-file source/test/license provenance, independent QA, exact destination CI (including ESP32) and physical acceptance. The #48 candidate remains draft/LAB/NO-GO.


## PHX-MASTER UTC23 exact ownership refresh — 2026-11-19

- HARDWARE PR #327 remains on its hardware-owned branch `phoenix/hardware-prepoll-edge-abort-20261119`, base #326 `58c558fb6a237935214621adc3dee65a10fe1a51`, current docs head `06c1cdaa47f2a33594354b014bd0b7445f894aaa`, source/test SHA `291f5206599f033d7e21cd3b031e7dd771afe748`. It is not a Master source path and is not a migration destination. QA owns the stale positive poll-signature fixture; RELEASE owns the build workflow; PISONET owns its separate Windows self-test.
- COE #48 Stage 5 head `b72ca86a141329b4b401f5d790cfb04a58423331` on #47 `1c10f7421dfaa87fcb2ce89d4a8b2d22422d1597` remains **UNASSIGNED / AUDIT-ONLY**. Its PR has no explicit PHX role-owner acknowledgement and `OWNERSHIP_ROUTES.json` has no route for it. Do not infer PHX-HARDWARE ownership solely from its Hardware directory. PHX-HARDWARE and PHX-PISONET must explicitly acknowledge their separate firmware/electrical and adapter/interface review scopes before any future source edit or integration proposal.
- COE #48 is not part of COE #26. No source blob, license, test, workflow or file was copied/moved/rebased/cherry-picked into #26. The current #26 head remains `b382d233ff06c8791b1028bed3c617cc7b670d12`; five unique workflows are queued with zero jobs. The unchanged route manifest remains `e4db324315a1b3543fec17a148fbf960170fcb29`, DRAFT_REVIEW_ONLY, PHX-MASTER destination null.

This is a coordination-only ownership/provenance correction, not a route change, migration authorization or release decision.




## COE #48 Stage 5 Remote CS — separate candidate, no migration route (2026-11-20 UTC00)

COE PR #48 at `8286548e395366f2332830025fed00ceebdfb24a` changes 14 paths, all under `Hardware/esp8266/BlazePisonetUniversal/staging/` plus its scoped workflow. Its changed-file list contains no `Pisowifi/` backend path. It is based on Stage 4.2 PR #47 at `1c10f7421dfaa87fcb2ce89d4a8b2d22422d1597`, not integration PR #26. No route exists for it in `OWNERSHIP_ROUTES.json`; do not copy, cherry-pick, rename or stage it into #26.

The Stage 5 `REMOTE_CS_BLAZEPWIFI_BRIDGE_CONTRACT.md` (blob `1dc0f709167862d543086449d895dd669f49f32d`) explicitly states that the backend bridge is required and not implemented. The current #26 Vendo source blob is `0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e`; the current #26 API source blob is `fabbd6fb28a34c162fb40403aec2a40d6fe1a65b`; the V1 schema blob is `8d0f8553ae53a0b22cb874de833aa21ebc52695e`. These are different wire contracts, not interchangeable files. The bridge requires a durable customer/session/target mapping, stable idempotency nonce, signed backend receipt verification, exact ESP ACK, expiry/reboot reconciliation and default-deny on unknown state.

The PR author declares JuanFi Apache-2.0 material is reference-only and no code/protocol was imported; the 14-path diff shows no third-party source import or license-file change. This declaration is not a legal license audit. Obtain PHX-HARDWARE and PHX-PISONET review-scope ACK/DECLINE plus PHX-CORE's receipt-contract authority before proposing a route. Preserve the original source and all current #26 staging unchanged.


## COE #49 Stage 5.1 — separate, unassigned candidate (2026-11-20 UTC01)

COE #49 `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` is stacked on #48 `8286548e395366f2332830025fed00ceebdfb24a`; it is not based on COE main or #26. Its 7-path diff contains Hardware staging/runtime/docs/tests/tools and the scoped workflow, with no `Pisowifi/` backend change. `OWNERSHIP_ROUTES.json` remains `e4db324315a1b3543fec17a148fbf960170fcb29`, DRAFT_REVIEW_ONLY, PHX-MASTER target null. No route exists for #48 or #49.

Do not copy, move, rebase, cherry-pick or stage #49 into #26. Require explicit PHX-HARDWARE and PHX-PISONET scope ACK/DECLINE, PHX-CORE approval of the backend target-kind/server-time interface, independent QA of the real backend mutation path, exact destination CI and licence/import provenance before any route proposal.


## Live COE candidate separation — 2026-11-20 UTC02

COE integration PR #26 remains the only manifest-pinned destination candidate (`b382d233ff06c8791b1028bed3c617cc7b670d12`), OPEN/DRAFT, with 205 changed paths and five queued workflows / zero jobs. `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`; PHX-MASTER target is `null`.

COE #49 (`aeb8ff11b2f5db9a5f86280ab62ab988245f3919`) is a separate Stage 5.1 adapter candidate stacked on #48, not on #26 and not on COE main. PHX-HARDWARE's review is explicitly audit-only; it declined implementation ownership. Do not copy, cherry-pick, rebase or fold #49 into #26 based on shared product naming.

Before any future migration proposal, compare every selected source/destination blob and file mode at exact SHAs, license/provenance, imports and dependency closure, test identity/fixtures, behavior and rollback, then obtain owner and independent QA review plus completed destination CI. Current #26 queued workflows provide no destination acceptance; the private v11 registry and newer corrections remain BLOCKED. No move is proposed by this refresh.


## PHX-MASTER UTC07 — Hardware #327 → COE #26 migration gate (2026-11-20)

The route manifest remains \`e4db324315a1b3543fec17a148fbf960170fcb29\`, source \`main@f4e8a891...\`, destination #26 \`b382d233...\`, \`DRAFT_REVIEW_ONLY\`; Hardware paths are \`selective-review\`, PHX-MASTER target is null. This manifest does not pin current Hardware #327 head \`63c1d2b...\`.

Exact current #327 source blobs:
- ESP8266 \`b956bc031df32ef69350dec368eaa91073b5a638\`
- ESP32 \`1458f32881d3b340f1101dd0215618b54c1b688b\`

Exact COE #26 destination blobs:
- ESP8266 \`c8be98f72596681e36a3ad1f8939bf8046c96887\`
- ESP32 \`3cc7ec54b476943dc04a8d1af5e2df5fe054e422\`

Both firmware files differ. Source MIT LICENSE blob \`1ee55b94...\` is present under BlazePwifi; no Hardware LICENSE/NOTICE is present in COE #26. The source has 25 board-specific Python lab files and three scoped PHX-HARDWARE workflows; the destination has one generic shell test and one generic Hardware CI workflow. The destination's five workflows remain queued with zero jobs.

No migration is proposed. Any later proposal must compare every selected source/destination blob and mode at exact SHAs, carry license/notice obligations, prove imported test identity and workflow behavior, verify dependencies and rollback, obtain source-owner and independent QA approval, and pass destination CI. COE #48/#49 are outside the manifest and remain unassigned/audit-only.

## PHX-MASTER UTC07 live role-CI and provenance supersession — 2026-11-20 (exact current source/destination recheck)

Source: Experiments HARDWARE PR #327 docs head d9072ce36e87a4bb1b9f1f5f888478a3c35fe236, source/test anchor 726981b49fb415fd10b764cbb8c386a00fcdbcf1 (base #326 58c558fb6a237935214621adc3dee65a10fe1a51). Destination: COE integration PR #26 b382d233ff06c8791b1028bed3c617cc7b670d12, against COE main a6513ab4412b4c014eee2863e45cbe32d06cb243.

| Item | Source #327 exact blob | Destination #26 exact blob | Result |
|---|---|---|---|
| ESP8266 sketch | b956bc031df32ef69350dec368eaa91073b5a638 | c8be98f72596681e36a3ad1f8939bf8046c96887 | Different |
| ESP32 sketch | 1458f32881d3b340f1101dd0215618b54c1b688b | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 | Different |
| Updated source lab pending_attempt_marker_lab.py | 1a6be62160a7bdb1e70fdf63a34ee2233e4e3fa4 | No exact destination identity | Source-only |
| Source Hardware license / notice | BlazePwifi LICENSE 1ee55b94183417be977ca287cd7391f9a6f7e721; root NOTICE f6d92cd21465312be5993631fe26977219be0fb9 | No Hardware/LICENSE, Hardware/NOTICE.md, root LICENSE or root NOTICE | License/notice scope incomplete |

The source tree has 25 board-specific Python files (16 ESP8266, 9 ESP32); destination Hardware/tests/ has one generic shell test (blob f921c56cecc19cab1989507b9b4ade1f45dac54e). Source has three scoped Hardware workflows (poll-edge latch, quarantine byte readback, relay/output polarity); destination has one generic hardware-ci.yml (blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793). The latest source/test commit changes one lab file; firmware sketch blobs are unchanged from the earlier UTC07 snapshot. Test equivalence, import completeness and workflow parity are not established.

The route manifest is unchanged at e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY; Hardware routes are selective-review, PHX-MASTER destination is null. COE #26 has five queued workflows and zero jobs. No copy, move, overwrite, cherry-pick, rebase, staging, route promotion or migration is proposed.

## PHX-MASTER UTC08 terminal CI and license-scope clarification — 2026-11-20

The exact COE #26 tree contains `Pisowifi/LICENSE` at the same MIT blob SHA as source `experiment/openwrt/BlazePwifi/LICENSE` (`1ee55b94183417be977ca287cd7391f9a6f7e721`). It does **not** contain `Hardware/LICENSE`, `Hardware/NOTICE.md`, or root `NOTICE.md`; source root `NOTICE.md` blob `f6d92cd21465312be5993631fe26977219be0fb9` is absent. The sibling `Pisowifi/LICENSE` is not assumed to establish explicit Hardware subtree license/notice scope. This is a review clarification only; no file was copied or moved.


## PHX-MASTER UTC08:40Z — exact destination and cross-role scope hold (2026-11-20)

COE #26 remains the only manifest-pinned integration candidate at `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN/DRAFT, five queued workflows / zero jobs. `OWNERSHIP_ROUTES.json` remains `e4db324315a1b3543fec17a148fbf960170fcb29`, DRAFT_REVIEW_ONLY, PHX-MASTER target null.

At exact #327 source / #26 destination trees, ESP8266 and ESP32 sketch blobs differ; 25 source board-local Python labs have no destination Python identities (destination has one generic shell test); three source Hardware workflows are absent from destination (destination has generic `hardware-ci.yml`); and explicit Hardware license/notice placement remains unresolved. No copy, move, rebase, cherry-pick, staging or route promotion is authorized by this audit.

Separate cross-role scope hold: #291's 22-path diff includes PISONET-owned `experiment/windows/BlazePisonet-SoftTimer/tests/ReleaseSigning/negative-selftest.ps1`. The current failure is an unset `$buildWorkflow` at line 115. PISONET must own/approve the correction; Master will not modify it. RELEASE retains its workflow/ELF tooling scope.

COE #49 remains separate and audit-only; no route exists for it. The private v11 registry/newer corrections remain inaccessible. No migration proposed.


## PHX-MASTER UTC11 — cross-role path hold and COE destination freeze

Current RELEASE #291 head b883662b4faebe05973c9a8bf7ff7ac54d978496 still contains two PISONET-owned paths: experiment/windows/BlazePisonet-SoftTimer/tests/ReleaseSigning/PublisherMockCli.ps1 and negative-selftest.ps1. The current Windows failure is the uninitialized $buildWorkflow in negative-selftest.ps1. PISONET must own/approve the fix; PHX-MASTER and PHX-RELEASE do not edit or absorb those paths.

Current #327/#26 exact tree comparison is recorded in INTEGRATION_MATRIX.md and the UTC11 audit report. Firmware blobs differ; 25 source board-local Python labs have no exact destination Hardware Python identities; three source Hardware workflows do not exist as exact destination workflows; root NOTICE is absent and Hardware license/notice scope remains unresolved. COE #26 has five queued workflows / zero jobs.

OWNERSHIP_ROUTES.json remains e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER target null. COE #48 and #49 are separate stacked candidates with no route; #49 remains audit-only after HARDWARE declined implementation ownership. No copy, move, rebase, cherry-pick, staging, route promotion or migration is proposed.


## PHX-MASTER UTC12 — current source ownership and migration hold (2026-11-20T12:39:46Z)

The live owner heads and exact CI are recorded in the UTC12 audit report and ROLE_ASSIGNMENTS.md. The current HARDWARE #327 and RELEASE #291 findings do not change source ownership: QA owns the stale positive poll fixture; HARDWARE owns firmware; RELEASE owns its release workflow/tooling and must refresh the canonical handover after its latest workflow change; PISONET owns PublisherMockCli.ps1 and negative-selftest.ps1 even though they appear in the broader #291 diff. CORE remains with its separate continuation.

COE #26 remains OPEN/DRAFT/FROZEN. Current source/destination firmware blobs differ, source board-local labs/workflows are not imported with equivalent identities, and root NOTICE / Hardware license-notice scope is incomplete. The sibling Pisowifi MIT license match is not proof of Hardware subtree scope. Keep OWNERSHIP_ROUTES.json unchanged at e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER target null. No move, copy, staging, overwrite, cherry-pick, rebase or route promotion.


## PHX-MASTER UTC13 — cross-role diff and destination routing hold

Current RELEASE #291 head is `dcb905333c8963fb139eeeefa72471738c874fb8`. Its 26-path diff contains three CORE product handover paths (`experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md`, `docs/handover/CHANGE_LEDGER.md`, `docs/handover/CURRENT_STATE.md`) and two PISONET-owned SoftTimer paths (`PublisherMockCli.ps1`, `negative-selftest.ps1`). The current Windows run #44746554630 fails in the PISONET negative self-test because `$buildWorkflow` is unset. CORE/PISONET must review and approve their own files; this audit does not transfer them to RELEASE.

COE #26 remains OPEN/DRAFT/FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`, five workflows QUEUED / zero jobs. Exact #327/#26 tree comparison confirms different ESP32/ESP8266 blobs, 24 source board-local Python lab/helper files with zero destination Hardware Python identities, three source Hardware workflows versus one generic destination workflow, and incomplete root NOTICE / Hardware license-notice scope.

`OWNERSHIP_ROUTES.json` remains unchanged at `e4db324315a1b3543fec17a148fbf960170fcb29`, DRAFT_REVIEW_ONLY, PHX-MASTER target null. No copy, move, overwrite, cherry-pick, rebase, staging, route promotion or migration is proposed.

## PHX-MASTER UTC13 terminal RELEASE CI and owner-path correction

#291 at `dcb905333c8963fb139eeeefa72471738c874fb8`: compatibility #44746554825 PASS on both ESP32 cores; Full #44746554633 CANCELLED at Android emulator with production import/sign/publish skipped; Windows #44746554630 FAIL at PISONET-owned `negative-selftest.ps1` because `$buildWorkflow` is unset. The Full CI-0701 job passed all 24 build-provenance tests, including the new checksum path-alias regression. PISONET still owns the failing test path; CORE still owns the three product handover paths in #291. No ownership transfer or Master source change.
## PHX-MASTER UTC14 routing and migration holds — 2026-11-20

### RELEASE #291 accumulated cross-role paths

The current 26-path #291 diff contains 21 RELEASE paths, three CORE-owned product-handover paths (`PROJECT_HANDOVER.md`, `CHANGE_LEDGER.md`, `CURRENT_STATE.md`), and two PISONET-owned SoftTimer tests (`PublisherMockCli.ps1`, `negative-selftest.ps1`). The current Windows failure is the unset `$buildWorkflow` in PISONET's `negative-selftest.ps1`. RELEASE retains its workflow/tooling scope; PISONET and CORE must review and approve their own files. Presence in the accumulated diff is not an ownership transfer. Master edited none of these paths.

### COE candidate ownership

- COE #48 remains **UNASSIGNED / AUDIT-ONLY** pending an explicit owner scope ACK; its Stage 5 and case-guard CI pass, but Shared Hardware CI fails. No PHX role is silently assigned.
- COE #49 remains **AUDIT-ONLY / NO ROUTE TO #26** after PHX-HARDWARE declined implementation ownership. Its Stage 5.1 and case-guard CI pass, but Shared Hardware CI fails.
- COE #31/#35 ImageBuilder sandbox failures are not waived by passing case or Hardware jobs. Missing Bubblewrap/site-scoped ULA authority remains an infrastructure/ownership gate, not permission to bypass sandboxing.

### Route-manifest invariants

`OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, source ref Experiments main `f4e8a891...`, destination candidate PR #26 `b382d233...`, and PHX-MASTER target `null`. The manifest is not a copy/move instruction. Exact source/destination blobs, licenses, import completeness, test identities, and destination CI must be independently accepted before any per-file route proposal. No route promotion or migration was performed.

## PHX-MASTER UTC15 exact route and migration hold — 2026-11-20

The live machine-readable route manifest remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, status `DRAFT_REVIEW_ONLY`, source ref Experiments main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`, destination candidate COE PR #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`, and PHX-MASTER target `null`. It is not a copy/move instruction.

At current HARDWARE #327 docs head `a2f2d42b1e65ceb0e60ae79517a0edc1d38a0d5d`, the complete source tree has 2,441 entries. COE #26 has 286 complete entries and 205 changed paths. Source and destination firmware blobs differ for both ESP8266 (`a1f12edc...` vs `c8be98f7...`) and ESP32 (`ae0da8e2...` vs `3cc7ec54...`). The source board/test paths contain 33 Python labs/helpers; COE `Hardware/` contains four files total and no Python. Source has three scoped PHX-HARDWARE workflows; destination has only generic `hardware-ci.yml`. The source hardening fixture blob `41211b2c...` differs from destination `f921c56c...`.

The source BlazePwifi MIT license blob `1ee55b94...` matches destination `Pisowifi/LICENSE`. Source root `NOTICE.md` exists, but COE root NOTICE is absent. No dedicated Hardware-specific LICENSE/NOTICE was found in the source board folders; destination `Hardware/LICENSE` and `Hardware/NOTICE.md` are absent, so Hardware notice/license scope remains unresolved. Do not infer Hardware coverage from the sibling Pisowifi license.

RELEASE #291's accumulated 26-path diff contains 21 RELEASE paths, three CORE-owned handover files and two PISONET-owned SoftTimer tests. The current Windows failure is in the PISONET-owned `negative-selftest.ps1`; only the respective owners may approve their files. Separate COE candidates #35/#44/#47/#48/#49/#45 remain independent drafts and do not become #26 acceptance or route authority.

**Disposition:** keep #26 FROZEN. No source/target copy, move, overwrite, cherry-pick, rebase, staging, route promotion or migration. Require exact per-file blob+mode provenance, owner approvals, license/notice review, test identity mapping, and destination CI at one pinned candidate SHA before any proposal.



## PHX-MASTER UTC18 routing and migration holds — 2026-11-20 (2026-11-20T18:06:08Z)

### RELEASE #291 inherited path ownership

Current #291 accumulated diff: 26 paths — 21 RELEASE, three CORE-owned handover paths, two PISONET-owned SoftTimer test paths. PISONET owns negative-selftest.ps1 and PublisherMockCli.ps1; CORE owns PROJECT_HANDOVER.md, CHANGE_LEDGER.md and CURRENT_STATE.md. RELEASE owns its workflow and provenance tools. The current Windows failure is the unset $buildWorkflow in the PISONET-owned test. RELEASE's UTC18 source audit is already IN_PROGRESS; Master will not duplicate or edit its files.

### HARDWARE #327 / QA fixture split

The active child remains #323 → #326 → #327. HARDWARE owns firmware and board-local labs. QA owns the inherited positive poll-signature fixture that conflicts with the current deny-only source. Do not change firmware to satisfy the obsolete assertion; QA must replace it with source-linked negative/default-deny checks.

### COE #26 destination hold

COE #26 remains FROZEN. Its current Pisowifi SOURCE_INTAKE/MIGRATION_MAP do not cover Hardware. Current source/destination sketch blobs and test identities differ; board-local Python labs and three scoped workflows are absent at destination; root NOTICE and Hardware license/notice scope are unresolved. OWNERSHIP_ROUTES.json remains unchanged, DRAFT_REVIEW_ONLY, PHX-MASTER target null. No route promotion or file movement.

## PHX-MASTER UTC19 exact routing and ownership hold — 2026-11-20T19:35Z

- HARDWARE #327 is now at 1a631567eb0c14c12a114f592685f44cc414466f; relay passed, quarantine/build are still running, and no current-head Full result is available. The prior f2fddc Full failure is historical; QA still owns the positive poll-fixture correction.
- RELEASE #291's 26-path diff remains 21 RELEASE, three CORE handover/ledger/state, and two PISONET ReleaseSigning test files. CORE and PISONET must review and approve their own paths.
- RENTAL #328 has six Rental-owned paths. Its shared build failure is inherited: CORE owns stale PROJECT_HANDOVER.md freshness; Hardware/Release own the Mbed TLS 4 firmware/toolchain mismatch. Rental must not edit Hardware or CORE handover files.
- COE #26 remains FROZEN at b382d233ff06c8791b1028bed3c617cc7b670d12. The source tree has 25 board-local Python labs/helpers and three scoped workflows; destination Hardware has zero Python identities and one generic workflow. Firmware/test blobs, behavior and notice scope differ. No destination action is authorized.
- OWNERSHIP_ROUTES.json remains e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER target null. No route promotion, copy, move, overwrite, cherry-pick, rebase or staging.
- CORE remains with the separate Blaze Production Continuation owner; Master performs coordination only.

## PHX-MASTER UTC19 #327 docs-head routing supersession — 2026-11-20T19:52Z

Current HARDWARE #327 docs head 4d651e918f71de2e69d1f3bcfe627c4f944c9c39, source/test 1a631567eb0c14c12a114f592685f44cc414466f. Quarantine #44805905655 and relay #44805905517 PASS; Full #44805905622 fails only at QA-owned positive poll-signature fixture after 14/14 target/Android builds pass. QA owns fixture correction; HARDWARE owns source; no Master source edit.


## PHX-MASTER UTC01 exact route/provenance revalidation — 2026-11-21T01:42Z

The machine-readable route manifest remains blob e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, with PHX-MASTER target null. It is a review map, not a copy/move command.

### Current COE #26 file and test parity

- Source HARDWARE #327 source/test tree 177312434...: 2,453 entries; destination PR #26 tree b382d233...: 286 entries. Both recursive trees are complete.
- 28 board-local Python labs/helpers exist in source; COE Hardware has zero Python test identities and one generic hardware-ci workflow versus three source Hardware workflows.
- ESP32 source/destination sketch blobs ae0da8e2... / 3cc7ec54...; ESP8266 a1f12edc... / c8be98f7...; hardening-test 41211b2c... / f921c56c.... None are byte-identical.
- Routed QA tests: 47 source / 19 destination; 1 identical, 3 divergent, 43 source-only, 15 destination-only.
- Source BlazePwifi MIT LICENSE matches destination Pisowifi/LICENSE at 1ee55b94...; source root NOTICE exists at f6d92cd2... but destination root NOTICE is absent. Hardware-specific license/notice scope is unresolved.
- COE #26 has five queued workflows and zero jobs. Its PR description claims all five modules are unified and 95% software release readiness; exact tree, test imports and CI do not support those claims.

### Cross-role paths requiring owner approval

Current RELEASE #291 has 26 changed paths: 21 RELEASE, 3 CORE handover/ledger/state and 2 PISONET ReleaseSigning tests. Windows fails at handover freshness; full build and compatibility are queued. CORE/PISONET must review their own paths. Similar shared handover/build files appear in #240, #255 and #290; role PR membership does not transfer ownership.

**Disposition:** COE #26 remains FROZEN. No copy, move, overwrite, rebase, cherry-pick, staging, route promotion, merge or destination edit. Keep original source histories intact.


## UTC01 terminal RELEASE #291 CI refresh — 2026-11-21T01:48Z

- RELEASE #291 remains at d04b5be6f177606c62f9b17a9499554275afce83.
- Compatibility #44851462501 completed PASS 3/3 (provenance suite plus ESP32 core 4.0.0 and 3.3.13 on source/test 177312434...).
- Full build #44851462517 completed FAIL at Mandatory handover freshness; target/Android builds passed and downstream simulations, signing and publication were skipped.
- Windows #44851462474 completed FAIL at shared handover freshness; Windows build and publisher were skipped.
- This supersedes the initial UTC01 queued status. PHX-MASTER did not edit RELEASE files or alter the PHX-RELEASE role lock.


## UTC01 destination revalidation — 2026-11-21T01:54Z

COE #26 remains the only destination candidate and is FROZEN at `b382d233...`; main is `a6513ab...`. Manifest `e4db324...` remains DRAFT_REVIEW_ONLY with PHX-MASTER target `null`. No move is proposed.

Current file-level comparison: source/test `28bf18e...` ESP32 blob `ae0da8e...` vs COE `3cc7ec54...`; ESP8266 `a1f12edc...` vs `c8be98f...`; hardening test `41211b2...` vs `f921c56...`. Both tests retain positive response/register/poll marker assertions. Pisowifi LICENSE matches at `1ee55b...`; Experiments root NOTICE `f6d92c...` is absent at COE root; `Hardware/LICENSE` is absent at the checked destination path. License/NOTICE scope remains unresolved; no legal conclusion.

The prior recursive tree count was measured at source/test `177312434...`; Hardware has advanced to `28bf18e...`, so the old count is superseded and not repeated without a fresh recursive inventory. Five COE workflows remain queued / zero jobs. No staging, copy, move, overwrite, cherry-pick, rebase or route promotion occurred.

## UTC02 exact destination revalidation — 2026-11-21T02:41Z

COE #26 remains the only destination candidate and is FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`; COE main remains structure-only at `a6513ab4412b4c014eee2863e45cbe32d06cb243`. Route manifest `e4db324315a1b3543fec17a148fbf960170fcb29` remains `DRAFT_REVIEW_ONLY`, PHX-MASTER target null. No copy/move is proposed.

### Complete exact recursive trees
- HARDWARE #327 PR/docs tree `1db9855a...`: 2,457 entries, `truncated=false`.
- HARDWARE #327 source/test tree `2d10db5...`: 2,456 entries, `truncated=false`; the docs-head commit adds only the one boot-order handover.
- COE #26 tree `b382d233...`: 286 entries, `truncated=false`.

| Route | Source | Destination | Identical | Different | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| ESP32 | 16 | 1 | 0 | 1 | 15 | 0 |
| ESP8266 | 24 | 1 | 0 | 1 | 23 | 0 |
| QA tests | 47 | 19 | 1 | 3 | 43 | 15 |
| OpenWrt overlay | 54 | 62 | 25 | 28 | 1 | 9 |
| Rental Android | 983 | 8 | 0 | 0 | 983 | 8 |
| Standalone rental | 31 | 19 | 0 | 2 | 29 | 17 |
| Rental server | 7 | 4 | 0 | 1 | 6 | 3 |

The broad standalone-rental route remains `manual-file-mapping-required` and `copy_permitted=false`; these counts do not authorize recursive copy.

### Exact current blobs and license/notice
- ESP32 sketch: source `142e1ac098aef2844f7d553771720871ee51d5e9`; COE `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` — different.
- ESP8266 sketch: source `b515b0d00a445eb0c9843659fbbd8c667803b87f`; COE `c8be98f72596681e36a3ad1f8939bf8046c96887` — different.
- Hardening test: source `41211b2c110ab409f6d9d1812ef12fda73b13211`; COE `f921c56cecc19cab1989507b9b4ade1f45dac54e` — different.
- Board-local Python labs/helpers: 28 source / 0 in destination Hardware.
- Routed QA files: 47 source / 19 destination; 1 identical, 3 divergent, 43 source-only, 15 destination-only.
- Source BlazePwifi LICENSE and destination Pisowifi/LICENSE match `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- Source root NOTICE `f6d92cd21465312be5993631fe26977219be0fb9` has no COE root counterpart. Hardware-specific notice/license scope remains unresolved.

COE #26 has five queued workflows and zero jobs. No staging, copy, move, overwrite, cherry-pick, rebase, route promotion or destination edit occurred.



## UTC04 exact-source destination revalidation — 2026-11-21T04:02Z

Source: Experiments HARDWARE #327 source/test `c5cb17bfa35ea24615f53097b936c49ebe5f0104`; destination: COE PR #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`. Recursive Git trees are complete and untruncated (source 2,459 entries; destination 286).

| Route | Source | Destination | Exact blobs | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| Hardware ESP32 | 16 | 1 | 0 | 1 | 15 | 0 |
| Hardware ESP8266 | 24 | 1 | 0 | 1 | 23 | 0 |
| QA tests | 47 | 19 | 1 | 3 | 43 | 15 |

29 source board-local Python lab/helper files have no equivalent in destination Hardware. The current ESP32 sketch source blob `09c02d589ae15b0c8a4f2a3bbcdee20c41d2cb79` differs from destination `3cc7ec54...`; ESP8266 source `dbb289f8d2cb8eedd72742b45dfeb518a4a7afa5` differs from destination `c8be98f7...`. The source and destination hardening tests differ and retain incompatible positive response/register/poll assertions.

Pisowifi LICENSE matches exactly at `1ee55b94183417be977ca287cd7391f9a6f7e721`. Source root NOTICE `f6d92cd...` has no COE root counterpart; Hardware-specific license/NOTICE applicability remains unresolved.

COE #26 workflows #43096752609, #43096752632, #43096752800, #43096752563 and #43096752557 remain QUEUED with zero jobs. The route manifest is unchanged at `e4db324315a1b3543fec17a148fbf960170fcb29`, DRAFT_REVIEW_ONLY, PHX-MASTER target null. **No migration staging or copy is authorized or performed.**


## UTC05 exact source snapshot — migration remains review-only (2026-11-21T05:33Z)

The manifest remains `OWNERSHIP_ROUTES.json@e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, source ref Experiments main `f4e8a891...`, destination candidate COE #26 `b382d233...`, PHX-MASTER target `null`. It does not authorize copying current Hardware #327 source/test `0f4cf65...`.

Exact source/destination review is recorded in [the UTC05 audit](PHX_MASTER_UTC05_20261121_RELEASE_PIN_PARITY_AND_COE26_EXACT_TREE_AUDIT.md): current firmware and hardening-test blobs differ; 30 source board-local Python labs and three scoped workflows are not imported as equivalent Hardware identities; source root NOTICE has no COE root counterpart; Hardware-specific license/notice scope remains unresolved. The Pisowifi LICENSE blob matches exactly but does not by itself settle Hardware subtree licensing.

**Disposition:** no copy, move, overwrite, rebase, cherry-pick, staging, route promotion or destination edit. Keep COE #26 FROZEN pending per-file owner review, exact test identity, license/import provenance and destination CI on the exact candidate SHA.


## PHX-MASTER UTC08 live exact-head reconciliation — 2026-11-21T08:47Z — current routing and migration disposition

- Source/default: Experiments `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; active v0.6 development `2fbd2475e9f54878c316fa7cea2f228386b0e859`; legacy v0.5.3 development `aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Active Hardware review source: #327 `a2d690b511524f8c710813fe4b4fc06cd52de3a8`. COE destination default: `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`; destination review #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- `OWNERSHIP_ROUTES.json` is unchanged at `e4db324315a1b3543fec17a148fbf960170fcb29`; status `DRAFT_REVIEW_ONLY`; PHX-MASTER destination remains `null`.
- Current exact-tree comparison is recorded in `INTEGRATION_MATRIX.md` and the UTC08 audit report. The source tree has 2,468 entries and the COE #26 destination 286; firmware, QA tests, board-local labs, workflows, and NOTICE/license scope remain non-equivalent.
- RELEASE #291's current ESP32 pin is now source-grounded: pinned source `5909e6238bc98f76075d910cf2fd09803cbdae99` and sketch blob `7ffb7b534c7163678726902946a17b04992950a0`; the current #327 ESP32 subtree matches 16/16 blobs. This is compatibility evidence, not migration authority.
- No destination staging, source copying, moving, overwrite, branch rewrite, cherry-pick, route promotion, or migration was performed. COE #26 stays FROZEN pending owner-reviewed exact-source, license, import, test-identity, and destination CI acceptance.

## PHX-MASTER UTC10 live exact-head and ownership supersession — 2026-11-21 — Hardware stack and manifest source separation

The active Hardware source stack is #322 `50d93e0d...` → #323 `988904e8...` → #326 `58c558fb...` → #327 docs HEAD `827fa75...` (source/test `3110a428...`). #329 `29c7f61...` and #330 `1a1e5e...` are sibling child drafts of #327 at the same parent SHA, not a serial chain; neither may be merged independently. Separate #239/#254/#283 drafts remain outside this stack.

The machine manifest remains `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29`, source ref Experiments main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`, COE destination candidate PR #26 `b382d233...`, status DRAFT_REVIEW_ONLY, PHX-MASTER target null. The active Hardware PR tree is not the manifest source ref. No route promotion or migration is authorized.

RELEASE #291 remains owner-controlled. Its 26-path diff contains 21 Release paths, three CORE handover paths and two PISONET test paths; Master will not edit or assume those files. COE #26 remains FROZEN pending per-file blob/test/license/NOTICE provenance and terminal destination CI.

## UTC10 post-owner finalization — 2026-11-21T10:38Z

RELEASE #291 current PR/docs head is `42797e2f3d65c30a1070caf49c93aebec149d897`, source/test anchor `1851f1d06648beed70695528f2799d57154a69237`. Its 26-path diff has 21 Release-owned paths, three CORE-owned handover paths and two PISONET-owned test paths. The exact compatibility run #44894604453 passes 3/3, including 36 provenance tests and 8 archive-verifier tests; Full #44894604464 and Windows #44894604466 remain blocked at CORE-owned handover freshness. The RELEASE route remains `reimplementation-review`; this evidence does not authorize copying Release workflows or any other route into COE #26.

The destination manifest remains unchanged, DRAFT_REVIEW_ONLY, Master target null. No migration staging or file movement was performed.
