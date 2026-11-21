# PHX-HARDWARE handover — ESP quarantine helper board parity

**Date:** 2026-11-21 UTC09  
**Role:** PHX-HARDWARE  
**Tasks:** #177 hardware safety / #266 cleanup-first  
**PR:** [#329 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/329), stacked on [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Branch:** `phoenix/hardware-quarantine-parity-20261121`  
**Parent #327 HEAD at branch creation:** `827fa75fa4e56ff3033076cc2f9b7ebb0cddf1a8`  
**Parent #327 base #326:** `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test commit:** `aaf1a0e7c8012873a3b86c69e3329ed06f1f3beb`

## Selected cleanup / safety-coverage task

The active poll-loop board-parity guard compared 17 shared poll and coin-authority helpers, but omitted the six shared quarantine persistence/cleanup helpers. Exact-source review of both current sketches showed the following six functions were identical after whitespace normalization:

- `quarantineLogTokenValid`
- `quarantineLogField`
- `quarantineLogRecordValid`
- `inspectQuarantineLog`
- `appendQuarantineRecord`
- `quarantinePending`

The Hardware-owned `poll_loop_blocking_inhibit_lab.py` now requires these six helpers as part of the 23-helper ESP8266/ESP32 parity contract. It emits a dedicated 6/6 marker and rejects two fail-open ESP32 mutations:
1. bypassing the append write-length failure guard in `appendQuarantineRecord`;
2. bypassing the append-failure guard in `quarantinePending` before pending cleanup.

This is a test-harness parity/maintenance change only. No production `.ino`, persistence format, API, finance, signer/witness, QA-owned test, Release workflow, COE destination or shared contract changed. Coin admission remains default-deny.

## Exact-head CI evidence — source/test SHA above

- **Quarantine/readback:** [run #44891881754](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44891881754), job `136809273105`: **SUCCESS**. Logs include `POLL_SAFETY_BOARD_PARITY_PASS 23/23`, `POLL_QUARANTINE_HELPER_BOARD_PARITY_PASS 6/6`, both quarantine mutations rejected, `SOURCE_QUARANTINE_PASS 36/36`, and `PENDING_JOURNAL_LAB_PASS 16/16`. Physical power-cut testing was not run.
- **Relay/output:** [run #44891881780](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44891881780), job `136809273532`: **SUCCESS**. The same 23/23 and 6/6 parity markers and both quarantine mutation rejections are present. ESP32 boot-polarity job `136809273370`: **SUCCESS**.
- **Full BlazePwifi:** [run #44891881763](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44891881763): **FAILURE**, validation job `136809273964`. The failure is the inherited QA-owned `Missing poll signature check` in `experiment/openwrt/BlazePwifi/tests/controllers.sh`. All 14 target/platform build jobs, including ESP8266, ESP32 and Android, completed **SUCCESS**; downstream simulation, update, signing and publication jobs were skipped. No Full validation pass is claimed.

No pre-fix RED commit is claimed for this parity-coverage addition. The two explicit mutation injections are the negative evidence for the new guard.

## Classification and boundaries

- **SIMULATED:** normalized source-helper parity and mutation rejection; host LittleFS/quarantine fixtures.
- **CI VERIFIED:** exact source/test SHA focused Quarantine/readback and Relay/output workflows.
- **Full integration:** FAILED at the independent controller poll-signature contract gate.
- **HARDWARE ACCEPTED:** NO. Real coin selector, relay/electrical behavior, physical flash durability, 150 power cuts and 30-device/24-hour soak remain NOT TESTED.
- **PRODUCTION READY:** NO-GO.

The parity checks do not establish a working positive authenticated poll/receipt path. Current coin/poll admission remains deny-until-CORE-contract; this PR does not invent a signature or weaken the QA failure.

## Next exact actions

1. **PHX-CORE:** publish the canonical authenticated register/poll and event-bound receipt/disposition contract with exact bytes and golden vectors.
2. **PHX-QA:** align the stale positive poll-signature assertion only after CORE approval, retaining negative/default-deny checks.
3. **PHX-MASTER:** refresh canonical Hardware stack pins and active-head assignments; the existing #288 role/matrix rows still lag live #327.
4. **PHX-HARDWARE:** revalidate the entire live stack before the next owned change.

No merge, rebase, retarget, force-push, flash, production migration, signing, release tag, deployment or cutover was performed.


## UTC13 follow-up — preserve C++ literal/comment bytes in board parity

**Date:** 2026-11-21 UTC13  
**Role:** PHX-HARDWARE  
**PR:** #329 OPEN / DRAFT / UNMERGED  
**Parent #327 HEAD:** \`827fa75fa4e56ff3033076cc2f9b7ebb0cddf1a8\`  
**Source/test SHA:** \`79c6f635499ef552a8a93b93a53d1326bb66ba24\`

### Proven test-harness defect

The parity comparator used \`" ".join(body.split())\`. Python \`split()\` collapses whitespace inside C++ string, character and raw-string literals, as well as comments. For helpers that validate quarantine tokens or serialized fields, two behaviorally different board implementations could therefore compare equal when a literal contained different internal spaces.

### Test-first reproduction and correction

- Test-first commit: \`fc97671ace034e88e394eb84f1934a4044f723d4\`.
- Expected RED Quarantine: [run #44910833783](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44910833783), job \`136866089643\`, failed with \`POLL_SAFETY_CPP_PARITY_NORMALIZER_FAIL: string-literal-whitespace\`.
- Expected RED Relay: [run #44910833864](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44910833864), job \`136866089878\`, same intentional failure.
- Fix commit: \`79c6f635499ef552a8a93b93a53d1326bb66ba24\`.

The replacement normalizer collapses formatting whitespace only in C++ code. It preserves standard string/character literal bytes, C++ raw-string contents and comment text; handles escaped quotes/backslashes and raw-string delimiters; and normalizes line endings only inside comments. Seven self-tests cover formatting-only whitespace, string/character/raw-string whitespace, escaped quotes, block-comment content and line-comment content.

### Exact-source GREEN evidence — \`79c6f635499ef552a8a93b93a53d1326bb66ba24\`

- Quarantine [run #44910997142](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44910997142), job \`136866580637\`: **SUCCESS**. Logs: \`POLL_SAFETY_CPP_PARITY_NORMALIZER_PASS 7/7\`, \`POLL_SAFETY_BOARD_PARITY_PASS 23/23\`, \`POLL_QUARANTINE_HELPER_BOARD_PARITY_PASS 6/6\`, source quarantine 36/36 and pending-journal 16/16.
- Relay/output [run #44910997165](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44910997165), job \`136866580683\`: **SUCCESS**. Same normalizer/parity markers; ESP32 boot-polarity job \`136866580774\`: **SUCCESS**.
- Full BlazePwifi push [run #44910991618](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44910991618): **FAILURE** at validation job \`136866637165\`, inherited QA-owned \`Missing poll signature check\` in \`tests/controllers.sh\`. All 14 target/platform jobs completed **SUCCESS** (including ESP8266, ESP32, Android, x86-64, Ruijie and Orange Pi variants). Downstream simulation, signed import, update, signing and publication jobs were skipped. No Full integration pass is claimed.

### Scope and classification

Only this Hardware-owned host-lab comparator and this handover changed. No production \`.ino\`, controller contract, finance, witness, QA-owned test, Release workflow or COE destination changed. Coin/poll admission remains default-deny.

- **SIMULATED:** source-text parity normalization and mutation/self-test coverage.
- **CI VERIFIED:** focused Quarantine and Relay/output workflows on the exact source/test SHA above.
- **Full integration:** FAILED at the separate CORE/QA authenticated poll-contract gate.
- **HARDWARE ACCEPTED:** NO. Physical coin/relay/electrical behavior, LittleFS power-cut durability, 150 power cuts and 30-device/24-hour soak remain NOT TESTED.
- **PRODUCTION READY:** NO-GO.

### Next exact actions

1. PHX-QA independently review this normalizer and retain negative/default-deny assertions.
2. PHX-CORE publish the approved authenticated register/poll and event-bound receipt contract with canonical bytes and golden vectors.
3. PHX-MASTER reconcile the stale #327 pointer in \`ROLE_ASSIGNMENTS.md\` against the current #327/#329 heads and the newer integration matrix.
4. PHX-HARDWARE keep this comparator host-only; no positive admission or quarantine callsite is authorized by this change.
