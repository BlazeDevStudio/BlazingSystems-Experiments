# PHX-MASTER UTC04 — coin-authority parity, release source pin and COE #26 exact-tree audit

**Updated:** 2026-11-21T04:02:05Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Execution:** Strict NO CODEX. GitHub connectors and read-only source/tree/CI inspection only.  
**Disposition:** Master coordination update ready for review; COE migration FROZEN; PRODUCTION NO-GO.

## 1. Live refs re-read

| Ref | Exact SHA / state |
|---|---|
| Experiments default `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments v0.6 development | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Experiments legacy v0.5.3 development | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master branch / PR #288 at audit start | `8517d6850589bb213ca1bb2b65882381ff9307ad` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

PR #288 remains OPEN / DRAFT / UNMERGED against Experiments main. At audit start it had 144 changed paths, all under `coordination/phoenix/`. COE #26 remains OPEN / DRAFT / FROZEN with 205 changed files. The source routing manifest is unchanged at `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, PHX-MASTER destination `null`.

Control-plane #172 is OPEN (last body update 2026-11-21T03:44:30Z). Cleanup #266 is OPEN and all seven role checkboxes remain unchecked. Its Master checkbox intentionally stays unchecked because the broader cross-repository duplicate/dead-code inventory is not complete.

## 2. Ownership and role reconciliation

Issue #177 was updated at 2026-11-21T03:57:44Z. Its `PHX-L-VERIFY` label is explicitly historical task-origin metadata; the current full-team owner is PHX-HARDWARE, and PHX-QA owns independent test review. This resolves the earlier routing ambiguity. No Light worker or parallel source owner was started.

| Role | Current PR / ref | Latest evidence |
|---|---|---|
| CORE | #252 `c82705f2...` | Left untouched; separate owner automation remains authoritative. |
| RENTAL | #328 `0e0da62a...` | APK identity #44782114384 PASS; API21/API23 #44782114393 PASS; shared build #44782114390 FAIL at handover freshness / inherited Mbed TLS 4 header. |
| PISONET | #255 `d01fd164...` | Scoped Windows CI #42462978704 PASS; physical USB-RS232 acceptance NOT TESTED. |
| HARDWARE | #327 docs `efb10354...`; source/test `c5cb17b...`; base #326 `58c558fb...` | Focused current-source CI PASS; Full fails at QA-owned poll-signature assertion. |
| QA | #290 `5c29d159...`; #292 `75a3f66d...` | #290 Windows CI #43633486963 PASS but native COM lab not invoked; #292 has no PR-triggered CI and retains historical Master base `b1ca02e...`. |
| RELEASE | #291 `f06ac4df...`; base #242 `734b89d9...` | Compatibility 3/3 PASS; Full poll-fixture failure; Windows canonical handover freshness failure. |

Older RENTAL #240 and #287 remain OPEN/DRAFT at `a7d113fb...` and `a4fffd01...`; their latest scoped runs #40910311141/#40910311159 and #43754089203 passed. These historical scoped successes do not replace current #328 shared-build status.

## 3. HARDWARE #327 — new board-parity coverage

The Hardware-owned host lab now verifies 17 normalized shared ESP8266/ESP32 helpers, including poll-response acceptance, coin disposition, POST admission, one-shot attempt marker, marker identity and pending-clear logic. Six ESP32-only fail-open mutations are rejected. No production sketch, financial schema, API, or other role's source changed in the source/test commit.

**Exact identity:**
- PR/docs head: `efb10354a71c392de8c72b6e73ff7616158cd675`.
- Source/test: `c5cb17bfa35ea24615f53097b936c49ebe5f0104`.
- Base #326: `58c558fb6a237935214621adc3dee65a10fe1a51`.
- Source/test tree: 2,459 entries, `truncated=false`.

**Actual hosted CI:**
- Expected RED for missing parity coverage: [#44863040495](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44863040495).
- Exact-source Quarantine push [#44863161774](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44863161774): PASS.
- Exact-source Quarantine PR [#44863167396](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44863167396): PASS.
- Exact-source Relay/output [#44863167432](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44863167432): PASS.
- Docs-head Quarantine [#44863539280](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44863539280): PASS.
- Docs-head Relay/output [#44863539382](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44863539382): PASS.
- Docs-head Full [#44863539439](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44863539439): validation fails at `Missing poll signature check` in the ESP8266 sketch; 14/14 target+Android builds pass; 12 downstream simulation/update/signing/candidate/publication jobs are skipped.

The exact validation log confirms the failure is the inherited positive marker assertion, not a Hardware compilation failure. Keep poll and coin admission default-deny. QA must align the test only after CORE publishes the approved authenticated register/poll response and event-bound receipt contract.

## 4. RELEASE #291 — immutable source pin remains valid only for the compiled blobs

Current Release head: `f06ac4df2f61b9c39a03a6ff6009b32948b94778`.

Compatibility run [#44862405800](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44862405800) completed 3/3:
- ESP32 core 4.0.0 job 136719044384 PASS.
- Provenance job 136719044536 PASS.
- ESP32 core 3.3.13 job 136719044591 PASS.

The workflow pins Hardware source/test `268ca9bde6d3710b418134ffd328060250fad42f` and ESP32 sketch blob `09c02d589ae15b0c8a4f2a3bbcdee20c41d2cb79`.

A direct commit comparison shows current Hardware source/test `c5cb17b...` is three commits ahead / zero behind. Only two source-test paths differ: the poll-loop host-lab file changed and a Hardware handover was added. The compiled ESP32 sketch blob remains `09c02d...`; ESP8266 sketch blob also remains `dbb289f8d2cb8eedd72742b45dfeb518a4a7afa5`. Therefore the earlier two-core compile remains valid for the exact unchanged ESP32 sketch, but it did not test the new host-lab. Current focused Hardware CI is the evidence for that lab.

- Full BlazePwifi run [#44862406950](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44862406950): validation fails at the QA-owned poll-signature assertion; 14/14 target+Android builds pass; downstream gates skipped.
- Windows run [#44862405809](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44862405809): canonical CORE handover gate fails because `PROJECT_HANDOVER.md` is stale after `.github/workflows/blazepisonet-softtimer-release.yml`; last checkpoint `adcae8141e673dc2147fcad50521ef3a23084d71`; Windows build and publisher skipped.

Next owner actions: RELEASE refreshes its own source/test anchor to `c5cb17b...` and records the unchanged sketch blobs plus the previous exact compile run; CORE's separate owner refreshes the canonical project handover. No Release-owned files were edited by Master.

## 5. COE #26 — exact recursive tree and license/test comparison

All three recursive trees are complete and untruncated:
- Current Hardware source/test `c5cb17b...`: 2,459 entries.
- Release pinned Hardware source `268ca9b...`: 2,458 entries.
- COE destination PR #26 `b382d233...`: 286 entries.

| Route | Source files | Destination files | Identical | Different | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| ESP32 | 16 | 1 | 0 | 1 | 15 | 0 |
| ESP8266 | 24 | 1 | 0 | 1 | 23 | 0 |
| QA tests | 47 | 19 | 1 | 3 | 43 | 15 |

There are 29 board-local Python lab/helper files at source and zero equivalent files under destination Hardware. The current ESP32 sketch source blob `09c02d...` differs from destination `3cc7ec54...`; current ESP8266 source blob `dbb289f8...` differs from destination `c8be98f7...`. The hardening-test blobs differ and the tests retain positive response/register/poll assertions inconsistent with the deny-only contract.

Pisowifi LICENSE matches byte-for-byte at `1ee55b94183417be977ca287cd7391f9a6f7e721`. Source root NOTICE `f6d92cd...` has no COE root counterpart. Hardware-specific license/NOTICE applicability remains unresolved; this is not a legal conclusion.

COE #26 workflow runs #43096752609, #43096752632, #43096752800, #43096752563 and #43096752557 are all QUEUED with zero jobs. No destination acceptance exists. COE #26 remains FROZEN; no copy, move, overwrite, staging, rebase, cherry-pick, route promotion or merge occurred.

## 6. Cleanup-first inventory — Master scope only

At Master branch `8517d685...`, the recursive `coordination/phoenix/` tree contains 144 files: 133 Markdown, 3 JSON and 8 Python. All 144 blobs are unique; there are zero duplicate blob groups.

`ARCHITECTURE_CONTRACTS.md` contains 62 numbered §6 headings and five duplicate heading IDs: **6.9, 6.10, 6.11, 6.25, 6.38**. No headings were renumbered and no reports were deleted or moved because inbound links and consumers have not been fully inventoried. This is a bounded cleanup inventory, not completion of the Master #266 track; its checkbox remains unchecked.

## 7. Governance, tools and evidence limits

The root Experiments `AGENTS.md` was read at blob `d8777e3b...`, together with the current README, the owner-uploaded Master directive, README_FIRST, and BLAZE-COMMS/1. The linked public cloud artifact policy was read at `BlazeDevStudio/BlazingSystems@e89167f...`, policy blob `5e503925...`; the storage recovery handover was read at the same repo head, blob `a15f14cb...`.

The requested private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections remain inaccessible: no Google Drive connector is exposed in this runtime and Library search did not return the canonical file. Older v6/v7 snapshots were not substituted. No private Drive IDs or contents were published.

Branch metadata reports `protected=false`; effective organization-level rules remain unverified. Full Master Python suite NOT RUN; Master-specific Actions run NOT returned. Local GitHub checkout unavailable due DNS. The tree/manifest/commit assertions above are source/tree inspections, not code tests. Hosted worker Actions links above are actual CI executions.

## 8. Next actions

1. PHX-QA replaces the obsolete positive poll-signature fixture with source-linked default-deny assertions only after CORE approves the authenticated response/receipt contract; rerun Hardware Full.
2. PHX-RELEASE refreshes its exact Hardware source/test anchor to `c5cb17b...`, records the unchanged firmware blobs and old exact-source compile boundary, then reruns CI-0701.
3. CORE's separate owner refreshes the canonical `PROJECT_HANDOVER.md`; Master does not take over CORE paths.
4. Registry custodian restores authorized v11/newer-correction access; repository administrator verifies effective branch protection.
5. COE integration keeps #26 frozen until exact per-file provenance, complete test import, license/NOTICE scope, destination CI and independent QA are accepted.
6. PHX-MASTER continues the broader duplicate/dead-code/reference inventory; do not renumber architecture sections until inbound links and consumers are mapped.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates remain mandatory.
