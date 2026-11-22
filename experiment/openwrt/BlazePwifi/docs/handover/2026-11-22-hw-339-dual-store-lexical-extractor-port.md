# PHX-HARDWARE — #339 dual-store fixture lexical extractor port (UTC10)

**Disposition:** focused Quarantine CI VERIFIED · Full build pending/validation gate not cleared · SIMULATED ONLY · HARDWARE ACCEPTED NO · PRODUCTION NO-GO

- Role: PHX-HARDWARE
- Repository: BlazeDevStudio/BlazingSystems-Experiments (repository ID 1389289885)
- Child PR: [#341](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/341) — OPEN / DRAFT / UNMERGED
- Parent PR: [#339](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/339), exact parent head `b3e1558845ae2cd508e42d0d4722fdcd28293e32`
- Parent base: #338 head `1a6a7cacf95722a78330d70de057e858143520f2`
- Branch: `phoenix/hardware-339-fixture-lexical-port-20261122-utc10`
- Test-only RED commit: `dddbe0d5bad07fc15f3bfa947f6c8fb278676c65`
- Source/test commit: `56ce713088fb5dccda5fb5434416fc5b6c75388a`
- Final docs head: recorded in the PR after this handover commit

## Decision and scope

#339 remains a separate Hardware-owned C++ parity-normalizer candidate. It is not a linear successor of the latest #327 branch. Before any future integration, its inherited dual-store host fixture needed the exact-source constant-extraction hardening already present on #327. This child PR ports that bounded fixture behavior without retargeting, rebasing, merging, or rewriting #339.

The inherited #339 fixture module used raw `splitlines()`, `startswith()`, and substring matching. It could select declaration-looking text inside comments/raw strings and accept a longer alias identifier. It also did not filter literal inactive preprocessor branches, including directives formed/continued through C/C++ phase-2 backslash-newline splicing.

## Test-first RED

- Test-only commit: `dddbe0d5bad07fc15f3bfa947f6c8fb278676c65`.
- Quarantine run [#45013924308](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45013924308), job `137182047626`: expected FAILURE at `test_constants_extract_only_active_declarations`.
- The old extractor returned comment/raw-string/inactive-branch decoys and `NOT_POLL_FAULT_EEPROM_OFFSET_ALIAS`; the expected active set was four declarations.
- This is the intended test-first defect reproduction, not an infrastructure failure.

## Source correction and exact-head GREEN

Source/test commit: `56ce713088fb5dccda5fb5434416fc5b6c75388a`.

Only two Hardware-owned host-lab paths changed:
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_fault_dual_store_lab_fixtures.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_fault_dual_store_lab.py`

The fixture now:
- Reuses the existing `mask_non_code()` lexical helper; no duplicate comment/string lexer was added.
- Preserves original source text for emitted declarations while checking mask length and line-count invariants.
- Filters only provably inactive literal `#if/#elif 0` branches after phase-2 logical-line splicing; unknown macro expressions remain conservative.
- Uses exact identifier boundaries, so a longer alias cannot satisfy a requested constant.
- Leaves the C++ harness body and ESP runtime/sketches unchanged.

Exact-source focused run:
- Quarantine [#45013986728](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45013986728), job `137182229109`: **SUCCESS**.
- `POLL_FAULT_CONSTANT_EXTRACTION_NON_CODE_DECOYS_REJECTED 4/4`
- `POLL_FAULT_CONSTANT_EXTRACTION_PREPROCESSOR_INACTIVE_REJECTED 4/4`
- `POLL_FAULT_CONSTANT_EXTRACTION_PHASE2_IF_SPLICE_REJECTED 1/1`
- `POLL_FAULT_CONSTANT_EXTRACTION_PHASE2_ELIF_SPLICE_REJECTED 1/1`
- Existing exact-source host suites also passed: quarantine 72/72; pending-attempt marker 58/58; fake-LittleFS mount/relay 16/16; boot-recovery 32/32; pending-clear 34/34; pending write/readback 22/22 per sketch; coin POST gate 24/24; disposition dispatch 14/14; poll-window drain 11/11 per board; pulse capture 17/17 per board.

The workflow explicitly reported `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_ACCEPTANCE=0`, `PHYSICAL_COIN_ACCEPTOR_VERIFIED=0`, `PHYSICAL_RELAY_POLARITY_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`. These are host/source-extraction checks only; they do not prove flash physics or device behavior.

## Integration and ownership boundaries

- #339 remains OPEN / DRAFT / UNMERGED; this PR is a child of #339 and is itself OPEN / DRAFT / UNMERGED.
- #327 remains the separate primary Hardware line. No merge-base rewrite, rebase, retarget, force-push, or merge was performed.
- #239 Phase-A deny, #254 ControllerAuthV1Lab, #283 both sketches, and #340 pre-poll intake deny remain independent drafts.
- No ESP sketch/runtime, GPIO/relay actuation, coin admission, controller/API, CORE ledger, QA-owned assertion, finance, signer/witness, Release workflow, or production migration changed.
- No flashing, device reset, secret provisioning, signing, release tagging, or deployment occurred.

## Remaining blockers / next action

1. Master to record the canonical stack sequence and exact pins; retain #339 as the normalizer candidate and review this child before any future stack integration.
2. CORE/QA still own the authenticated register/poll `response_sig` contract and the inherited Full validation assertion. Do not invent a signature or weaken default-deny.
3. Run Full workflow on the final docs head; report its actual result separately from the focused Quarantine pass.
4. Physical EEPROM/LittleFS durability, electrical pulse/relay recovery, 150 power cuts, 30-device 24-hour soak, protected anti-rollback witness, v1→v2 financial migration, durable accounting/replay, and independent QA/Release acceptance remain NOT TESTED or NOT ESTABLISHED.

**No production readiness claim.**
