# PHX-HARDWARE handover — encoded C++ raw-string lexer regression

**Date:** 2026-11-21 (UTC04)  
**Role:** PHX-HARDWARE  
**Task:** #266 / #177 / #327 — shared firmware source-extractor correctness  
**Repository:** \`BlazeDevStudio/BlazingSystems-Experiments\`  
**Branch:** \`phoenix/hardware-prepoll-edge-abort-20261119\`  
**Base PR #326:** \`58c558fb6a237935214621adc3dee65a10fe1a51\`  
**Source/test SHA:** \`0f4cf65b33b0f0fa6bc1889b9f7b14025c610245\`  
**PR HEAD before this handover:** \`0f4cf65b33b0f0fa6bc1889b9f7b14025c610245\`

## Selected task and reason

The shared Hardware-owned C/C++ source extractor documented support for C++ raw strings, but only recognized the unprefixed \`R"delimiter(... )delimiter"\` spelling. Valid encoding-prefixed raw literals (\`u8R\`, \`uR\`, \`UR\`, \`LR\`) were scanned as ordinary quoted strings. Embedded quotes, braces and comment-like text could therefore be mistaken for source syntax and truncate an extracted firmware function.

This is a source-tool correctness defect affecting multiple source-extracted host labs. The fix is confined to the Hardware-owned lexer and its lab runner; no firmware behavior or cross-role interface changed.

## Changes

- Added \`firmware_lab_source_lab.py\`, a focused regression for \`R\`, \`u8R\`, \`uR\`, \`UR\` and \`LR\` raw string prefixes.
- Wired the regression into the already-invoked \`poll_loop_blocking_inhibit_lab.py\` runner, avoiding any Release-owned workflow modification.
- Updated \`firmware_lab_source.py\` to recognize all five prefixes, validate the delimiter, mask the complete literal including its encoding prefix, and preserve byte offsets and newline positions.
- The test fixture deliberately places quotes, braces and a block-comment-shaped sequence inside the raw body. It verifies the containing function remains complete after extraction.

## Test-first evidence

**RED — exact pre-fix failure**

- Fixture commit: \`41455d629732479cd2830e04002cef780f3e6926\`.
- Test wiring commit: \`0a288e2dade30ac3d90ac0e74fa22eaaf8f24ff3\`.
- Quarantine PR [run 44867970490](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44867970490), job \`136735828592\`: expected failure at \`u8R: raw literal or encoding prefix was not masked\`.
- Relay/output PR [run 44867970477](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44867970477), job \`136735828890\`: same regression failure through the shared poll-loop runner.

**GREEN — exact fixed source/test SHA**

- Fix commit: \`0f4cf65b33b0f0fa6bc1889b9f7b14025c610245\`.
- Quarantine PR [run 44868064907](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44868064907), job \`136736120221\`: PASS; log reports \`FIRMWARE_SOURCE_EXTRACTOR_RAW_PREFIX_PASS 5/5\`, then existing 17/17 poll-safety parity and all six authority-drift mutation rejections.
- Quarantine push [run 44868059980](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44868059980), job \`136736104909\`: PASS.
- Relay/output PR [run 44868064885](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44868064885), jobs \`136736120275\` and \`136736120479\`: PASS. The source-output job log includes the 5/5 raw-prefix marker and existing output/poll regressions.

**Full validation is not green**

- BlazePwifi build PR [run 44868064906](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44868064906), validation job \`136736190277\`: FAIL at the inherited QA-owned \`Missing poll signature check\` in \`experiment/openwrt/BlazePwifi/tests/controllers.sh\`.
- At handover time, all 13 firmware-target jobs had completed PASS; Android was still running. The run was not yet terminal.
- Downstream production-import, update-bundle and simulation jobs were skipped after validation failed.

## Scope and ownership

Changed only Hardware-owned files under \`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/\` plus this narrow Hardware handover. No production \`.ino\`, server API, receipt format, financial journal, witness, Release workflow, QA-owned assertion, or other-role file changed.

The existing #327 → #326 draft stack is preserved. PR #327 remains OPEN / DRAFT / UNMERGED. No rebase, retarget, force-push or merge occurred.

## Current coordination / blockers

- PHX-MASTER's latest coordination head read during this activation: PR #288 \`3a35cd1c4acf141470393ebfcd6fdc06592fb07d\`. Master must refresh its active-head pin after this Hardware commit; Hardware did not edit \`coordination/phoenix/\`.
- PHX-QA / PHX-CORE still own resolution of the positive poll-signature assertion and canonical authenticated register/poll + event-bound receipt contract. Hardware did not invent \`response_sig\` or weaken default-deny.
- Parallel drafts remain separate: #239 \`d83b715b...\`, #254 \`84c442a4...\`, #283 \`830c3553...\`; no files were copied between them.
- COE main remains \`a6513ab4412b4c014eee2863e45cbe32d06cb243\`; COE #26 remains OPEN / DRAFT / FROZEN at \`b382d233ff06c8791b1028bed3c617cc7b670d12\`.
- The private Drive registry v11 was not found after the full Library listing (8 pages), and no Google Drive connector is exposed in this execution environment. No older registry snapshot was substituted.

## Evidence boundary and next action

**SIMULATED / CI VERIFIED only.** This is host-side lexer/test-harness evidence, not firmware hardware acceptance. Physical coin acceptor, relay/electrical pulse recovery, 150 physical power cuts, 30-device/24-hour soak, protected signer/witness, financial v1→v2 migration and durable accounting/replay remain NOT TESTED or NOT ESTABLISHED. HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.

Next:
1. PHX-MASTER refreshes #172 / \`ROLE_ASSIGNMENTS.md\` / \`INTEGRATION_MATRIX.md\` to the new #327 head without changing stack ancestry.
2. PHX-CORE publishes the approved controller register/poll and event-bound receipt contract with exact bytes and golden vectors.
3. PHX-QA updates its positive poll-signature assertion only against that approved contract and retains negative/default-deny coverage.
4. PHX-HARDWARE revalidates all live heads and continues with one owned, reversible firmware/source-lab task.

No physical flash, live money, production migration, signer provisioning, release tag, deployment or cutover is authorized.