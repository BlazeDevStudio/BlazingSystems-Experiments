# PHX-HARDWARE handover — quarantine disposition callsite dormancy guard

**Updated:** 2026-11-22T18:50:00Z  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Issue:** [#177 — synchronous poll / coin pulse preservation](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Cleanup gate:** [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
**PR:** [#283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283) — OPEN / DRAFT / UNMERGED  
**Branch:** `cleanup/esp-firmware-hardening-and-quarantine-20261111`  
**Base:** `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**Source/test SHA:** `a0b90bb731575afa2746e63d0c9fdd01a7044189`

## Decision

Keep `quarantinePending()` **definition-only** in the #283 candidate until PHX-CORE publishes the authenticated event-bound disposition contract and PHX-QA independently verifies positive and negative vectors. Do not add a runtime callsite, coin replay, or automatic pending clear in this branch.

The current main CGI producer blob `2e3a1430d08cc6606429a042df3b5848f53c7267` still does not emit an approved `response_sig` for `register|ping` or `poll`. Member-endpoint signatures are not interchangeable with controller response authentication. Firmware admission therefore remains deny-only.

## Exact-source audit

Before this test-only change, PR #283 was at `88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d`:

- ESP8266 sketch blob: `70b524485e960665e078856fed8434bc55cb4942`.
- ESP32 sketch blob: `e8dc5c4bfe659326c74bab1aeac367fb5f404afe`.
- Each sketch had exactly one `quarantinePending(` occurrence: the function definition, no active callsite.
- Each helper returned false immediately when `appendQuarantineRecord(reason)` failed; `clearPending()` was reached only after successful append verification.
- The append helper checked the existing-prefix fingerprint, write length, post-close size, and byte-for-byte appended readback.
- `clearPending()` validated the pending record, checked remove success and post-remove absence, and only then cleared RAM state.
- `POST /quarantine/clear` returned HTTP 403 and did not remove `/quarantine.log`.

Thus the specific earlier unconditional-clear and remote-log-deletion audit leads are corrected in this source snapshot and covered by host CI. This does **not** establish a reachable quarantine lifecycle, cross-reboot flash durability, or hardware acceptance.

## Change in this activation

Only the Hardware-owned host lab changed:

`experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/quarantine_append_readback_lab.py`

It now:

1. Requires exactly one `quarantinePending(` reference and one function definition in each production sketch.
2. Rejects any additional reference until CORE/QA approve the event-bound disposition contract.
3. Injects a synthetic unapproved callsite and verifies the guard rejects it.
4. Continues to compile the actual append/quarantine helpers and exercise the existing failure-injection matrix.

No production `.ino`, shared API, QA-owned assertion, Release workflow, financial backend, signer, or migration file changed.

## CI evidence

- Prior exact-head Quarantine [run #44936835281](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44936835281), job `136945197219`, SUCCESS at `88581eef...`: append/readback 13/13 per board; pending-journal boot fail-closed 14/14 per board; clear/commit 10/10 per board with ignored-clear-result mutation rejected; quarantine-clear denial 6 repeated POST attempts per board with the log unchanged.
- New exact-source Quarantine [run #45057300450](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45057300450), job `137315253459`, SUCCESS at `a0b90bb...`: both boards report `MUTATION_REJECTED unapproved quarantinePending callsite`; append/readback 13/13; pending-journal boot 14/14; clear/commit 10/10; quarantine-clear denial 6/6 repeated attempts per board.
- Intermediate harness commit `c396fa55a0e4c62c67881a7e8c815432a482c6bf` failed because the first Python regex was over-escaped. The failure was inspected in the exact Actions log and corrected in `a0b90bb...`; the corrected exact-source Quarantine job passed.
- Full BlazePwifi [run #45057300435](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45057300435) was still in progress at handover creation. No Full aggregate result is claimed here.

## Parallel lineage guardrails

- [#340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/340) remains a separate child of #283 at `20c5889fc4ceeb95ab0b05c7c11952704caff36b`; it carries pre-poll intake denial and the Mbed TLS compatibility candidate. Do not cherry-pick or silently collapse ancestry.
- [#335](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/335) is a separate Hardware lineage with active quarantine callsites. Do not transfer those callsites into #283 without Master/CORE/QA approval.
- [#327 → #342 → #343](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/343) is another distinct child stack. Preserve all current parents and exact heads.
- #239 (Phase A deny) and #254 (ControllerAuthV1Lab) remain separate OPEN / DRAFT / UNMERGED candidates.

## Status and next action

- Append-failure ordering and no-delete behavior: **CI VERIFIED** in host failure-injection labs.
- Quarantine lifecycle activation: **NOT ENABLED**; no active callsite in #283.
- Flash persistence across real power loss: **NOT TESTED**.
- 150 power cuts, 30-device/24-hour soak, electrical pulse/recovery: **NOT TESTED**.
- HARDWARE ACCEPTED: **NO**.
- PRODUCTION READY: **NO-GO**.

**Next exact action:** PHX-CORE publishes the versioned authenticated register/poll and event-bound receipt/disposition contract; PHX-QA independently verifies golden positive/negative vectors; PHX-MASTER selects the integration lineage. Until those reviews are recorded, PHX-HARDWARE keeps `quarantinePending()` dormant and coin/relay admission deny-only.
