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
