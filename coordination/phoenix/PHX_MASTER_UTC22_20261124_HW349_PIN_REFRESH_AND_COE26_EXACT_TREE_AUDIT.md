# PHX-MASTER UTC22 — HARDWARE #349 exact-pin refresh and COE #26 exact-tree audit

**Observed:** 2026-11-24T22:37:40Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts and cross-repository provenance only  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** phoenix/master-coordination  
**Starting HEAD:** `66a734ee33b7fc9fca8a2dd0b95c7fdd7d29bba3`  
**Base:** main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**PR:** [#288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288), OPEN / DRAFT / UNMERGED

## 1. Scope and outcome

This is a bounded coordination-only refresh requested by the new HARDWARE UTC22 checkpoint. It updates the Master role matrix, integration matrix and index, and records the exact source/test versus docs-head distinction. No CORE/RENTAL/PISONET/HARDWARE/QA/RELEASE source path, ownership manifest, financial state, or COE destination path is changed.

## 2. HARDWARE #349 exact identities

- PR #349: OPEN / DRAFT / UNMERGED; branch `phoenix/hw-json-array-primitive-guard-20261124-utc00`; base #347 `960184670379f01e20f0e7e8bc23b3e5eedacd3f`.
- Source/test SHA: `0aba4cd66deae4c358dec950ace1e86be3241674`.
- Final docs/PR HEAD: `c265eafe83c472ba5355b584454f0fa76f379393`.
- Compare reports four commits ahead / zero behind from source/test to final docs head; only `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md` and `experiment/openwrt/BlazePwifi/docs/handover/2026-11-24-hw-dual-store-shared-runner-utc22.md` changed. No source/test file changed after `0aba4cd`.

### Exact CI

- Source/test Quarantine [#45500875662](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45500875662): SUCCESS; shared C++ runner guard, 8/8 runner contract and dual-store lab on ESP32/ESP8266 pass.
- Source/test Relay [#45500875749](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45500875749): SUCCESS.
- Source Full run was cancelled; it is not a pass.
- Final docs-head Quarantine [#45502304112](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45502304112): SUCCESS.
- Final docs-head Relay [#45502304004](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45502304004): SUCCESS.
- Final docs-head Full [#45502304116](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45502304116): terminal FAILURE. Validation job `138828592534` logs `Missing poll signature check`. All 14 firmware/platform jobs and Android passed; dependent validation/release stages were skipped.

The live PR body still calls Full #45502304116 pending. HARDWARE must refresh its own description/handover to record the terminal failure. Master does not edit Hardware-owned files. CORE owns the authenticated poll producer contract; QA owns independent assertion reconciliation. Preserve default-deny. Physical coin/relay/power-cut acceptance remains NOT TESTED.

## 3. COE #26 exact source/destination tree audit

- Source: Experiments #349 source/test `0aba4cd66deae4c358dec950ace1e86be3241674`; recursive tree 2,530 entries, non-truncated.
- Destination: COE #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`; recursive tree 286 entries, non-truncated.
- Tests: 47 source / 19 destination; exact blob+mode 1, divergent 3, source-only 43, destination-only 15. Divergent same-name files are `config.sh`, `integration.sh`, `security.sh`.
- Hardware board subtree: 65 source files / 2 destination sketches; 53 Python lab/helper files in the source board subtree / 0 destination Python helpers.
- ESP32 sketch: source `adfd2f110d88243d03f2195658fb456b154dcb84`; destination `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.
- ESP8266 sketch: source `8a0b458b6c7fb99c0913df16c5b4ca94dbcdc50e`; destination `c8be98f72596681e36a3ad1f8939bf8046c96887`.
- `SOURCE_INTAKE.json`: 61 runtime rows; actual status values 46 byte-identical / 15 derived, while the summary claims 47 / 14. All 61 destination blob/mode identities match the recorded destination pins. At current source/test `0aba4cd`, 33/61 rows still match the historical source blob/mode; 28 have source drift (20 changed, 8 absent).
- `MIGRATION_MAP.md`: 4 original-test rows + 14 derived-test rows = 18, versus 15 derived tests in JSON. It omits `voucher_txn_journal.sh`; `run_focus.sh` and `member_txn_journal.sh` hashes are stale. Destination voucher test blob is `4277a56af800b930135745bb942d62b6d580cb99` with no map row.
- PisoWiFi product LICENSE, rootfs QRCode LICENSE and TailAdmin LICENSE/NOTICE have exact counterparts. Source UI QRCode LICENSE and Tabler LICENSE have no destination counterparts. BlazeRentalLauncher LICENSE remains under separate RENTAL routing.
- Five COE #26 workflows remain QUEUED with zero jobs/statuses.

**Disposition:** COE #26 remains FROZEN. No staging, copy, move, overwrite, cherry-pick, rebase or destination write. The intake owner must correct the counts, test map, source pin drift classification and license routing before any staging proposal.

## 4. COE #35 current RELEASE-owned head

- Source/test `39ff80f005ce7ed39e851f3b63ad905c5bce2b16`; final handover/PR HEAD `23dcae0cace76c35dbad0217755af57aec033482`.
- One docs-only commit after source/test modifies `tools/RELEASE_PACKAGER_HANDOVER.md`.
- Shared [#45499282763](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45499282763): 216 host tests, zero test failures; subsequent profile gate fails closed for all 10 profiles because no approved site-scoped RFC 4193 ULA /48 is supplied.
- Sandbox [#45499282825](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45499282825): 40/40 host preflight tests pass; runner then exits 125 because Bubblewrap is absent.
- Case guard [#45499282801](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45499282801): PASS.
- The COE #35 PR body still points to UTC15. RELEASE owns its refresh; these host-CI results are not physical appliance acceptance.

## 5. Other live blockers

- RELEASE #291 remains at `53fc8a1c558f80adde19dc675b879c78797f0cd5`: Windows and build fail CORE-owned CURRENT_STATE freshness; ESP32 compatibility passes for its pinned sketch only.
- HARDWARE #347/#348, RENTAL #328 and the separate owner PRs remain under their respective owners. CORE continuation is not invoked or modified.
- `OWNERSHIP_ROUTES.json` remains 11 routes / `DRAFT_REVIEW_ONLY` / PHX-MASTER target null. Cleanup #266 remains OPEN / 0-of-7.
- Root AGENTS requires private registry, artifact manifest and sync ledger before Drive artifact/folder operations. Canonical private Drive v11 and newer corrections were not surfaced; no Google Drive connector is exposed. Older v3-v7 snapshots and the November 9 checkpoint are not substitutes. No private IDs/content are published.

## 6. Validation and limitations

**Executed:** live issue/PR/ref reads; recursive source and destination trees; test blob/mode comparisons; SOURCE_INTAKE runtime classification; migration-map path/hash checks; license path inventory; exact-head Actions runs and failed-job log inspection; compare-commit checks separating source/test from docs-only commits.

**Not executed:** Master Python unittest suite, `verify_coordination.py`, native hardware tests, power cuts, 30-device soak, physical acceptance or financial migration. No authenticated local checkout is available. The audit assertions are read-only source/metadata checks, not a Master product-test pass.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device 24-hour soak and owner-authorized release gates remain mandatory.

No merge, release, signing, secret provisioning, hardware flashing, payment operation, customer cutover or migration occurred.
