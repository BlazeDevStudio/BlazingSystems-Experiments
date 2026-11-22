# PHX-HARDWARE — C++ preprocessor boundary parity normalizer (UTC23)

**Disposition:** PR_READY · focused CI VERIFIED · Full validation blocked by QA-owned controller assertion · SIMULATED ONLY · PRODUCTION NO-GO  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments (repository ID 1389289885)  
**PR:** [#339](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/339) — OPEN / DRAFT / UNMERGED  
**Branch:** \`phoenix/hardware-cpp-preprocessor-boundary-20261121-utc23\`  
**Parent:** PR #338 at \`1a6a7cacf95722a78330d70de057e858143520f2\`  
**Source/test SHA:** \`79b7d10ec646fe91274d22d90a6657e6fbe500a6\`  
**Base:** #338 branch \`phoenix/hardware-poll-normalizer-module-20261121-utc22\`

## One bounded Hardware-owned task

The host-lab C++ normalizer collapsed all whitespace, including newlines that establish whether \`#if\`, \`#define\`, and other preprocessor directives begin a logical line. It could therefore normalize these two different source bodies to the same text:

\`\`\`cpp
void f(){
#if defined(ESP32)
 return true;
#endif
}
\`\`\`

\`\`\`cpp
void f(){ #if defined(ESP32)
 return true;
#endif
}
\`\`\`

The second \`#\` is not at the start of a logical preprocessing line. Treating the bodies as equivalent could conceal a board-specific conditional-compilation difference in the parity lab.

The normalizer now:
- Tracks whether the current logical line already contains a code token.
- Preserves a preprocessor directive as a line-anchored token, while ignoring harmless indentation before \`#\`.
- Preserves directive continuation lines and normalizes CRLF/LF line endings.
- Handles phase-2 backslash-newline splices outside literals/comments/directives.
- Does not reset logical-line state for a block comment whose only newline is spliced; an unspliced newline still starts a new logical line.
- Continues to preserve literal and comment contents while normalizing ordinary code whitespace.

No ESP8266/ESP32 sketch, GPIO/relay behavior, poll/coin admission, controller/API, finance, signer/witness, QA-owned assertion, or Release workflow was changed.

## Test-first and exact-head evidence

The branch retains the test-first sequence, including two independently reproduced false-equivalence cases:

1. Initial test fixture commit \`9d7b815ecf9c208d276f4c72dd9fd832ff107677\` had over-escaped Python newline fixtures; Quarantine run [#44963425677](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44963425677), job \`137027027449\`, failed at the malformed leading-whitespace fixture. The fixture escapes were corrected in \`d10ff94803525134ed431babf8425c6335009558\`.
2. Corrected test-first RED: Quarantine run [#44963539809](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44963539809), job \`137027380451\`, failed as intended at \`preprocessor-directive-line-boundary\`.
3. First source fix: \`44255ecb2d2d82e45561c19320f009146539774b\`; Quarantine run [#44963608711](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44963608711), job \`137027592305\`, PASS at 13/13 normalizer cases.
4. A second test exposed a related block-comment/backslash-newline false equivalence. Test-only commit \`2626cb98bac2151f9960e53f65a6f063346f2d5a\`; Quarantine run [#44963685905](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44963685905), job \`137027837947\`, failed as intended at \`preprocessor-block-comment-splice-boundary\`.
5. Final source/test SHA \`79b7d10ec646fe91274d22d90a6657e6fbe500a6\`; exact-head Quarantine run [#44963705160](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44963705160), job \`137027897513\`, **SUCCESS**.

Final exact-source Quarantine log markers:
- C++ normalizer: **14/14 PASS**.
- ESP32/ESP8266 normalized helper parity: **23/23 PASS**.
- Quarantine helper parity: **6/6 PASS**.
- Drain-abort polarity builder: **2/2 PASS**.
- Source-extracted quarantine scenarios: **36/36 per board; 72/72 combined**.
- Pending attempt marker: **29/29 per board; 58/58 total**.
- Boot recovery: **32/32**; pending clear: **34/34**.
- Pending write/readback/rotation: **22/22 per sketch**.
- Coin POST gate: **24/24**; disposition dispatch: **14/14**.
- Poll-window drain: **11/11 per board**; original #177 1501/1600/1680 ms timing case PASS.
- Existing mutation probes rejected fail-open, missing-inhibit, missing-edge, wrong-polarity, stale-target, and journal/quarantine bypass variants.

The workflow explicitly reports \`SIMULATED_ONLY=1\`, \`PHYSICAL_RELAY_ACCEPTANCE=0\`, \`PHYSICAL_COIN_PULSE_ACCEPTANCE=0\`, and \`PHYSICAL_POWER_CUT_ACCEPTANCE=0\`. These are source-extracted host simulations, not hardware acceptance.

## Full integration disposition

Exact final source/test SHA Full PR run [#44963705158](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44963705158):
- Validation job \`137027907250\`: **FAILURE** at inherited QA-owned \`tests/controllers.sh\` assertion \`Missing poll signature check\`.
- All **14/14** ESP8266, ESP32, Android, OpenWrt target and optional target jobs completed SUCCESS.
- Browser/platform simulations, candidate gates, update bundle, signing and publication were skipped after validation failure.

The failure is outside this normalizer change. Current main register/poll producers still do not emit the canonical \`response_sig\` contract. PHX-CORE owns the authenticated receipt/response contract; PHX-QA owns the positive assertion/extractor. Do not invent a signature or weaken firmware default-deny behavior to make Full green.

## Live coordination and parallel candidates

At this activation:
- Experiments main: \`f4e8a891aed8af86d5fd315d28750a0ac3a7372b\`.
- Master PR #288 live head: \`0fdb43c20fc6b68699e229b5cdc8a7e7a4efbe93\`; its current role/integration documents still omit #338/#339 and pin older #327 metadata. Master was asked to refresh its own inventory; Hardware did not edit Master-owned files.
- Parent #338 remains OPEN/DRAFT at \`1a6a7cacf95722a78330d70de057e858143520f2\`.
- #239 remains OPEN/DRAFT Phase-A deny at \`d83b715b116185107737fef721c2eece8feebf39\`.
- #254 remains OPEN/DRAFT ControllerAuthV1Lab at \`84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9\`.
- Parallel #283 remains OPEN/DRAFT, main-based, at \`88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d\`; its append failure guard is present, but \`quarantinePending()\` has no active callsite and the shared response-signature contract remains unresolved.
- COE integration PR #26 remains OPEN/DRAFT/FROZEN at \`b382d233ff06c8791b1028bed3c617cc7b670d12\`; no source migration or promotion occurred.

## Remaining gates

- Physical coin/relay/electrical pulse recovery: NOT TESTED.
- 150 controlled power cuts: NOT TESTED.
- 30-device / 24-hour soak: NOT TESTED.
- Protected anti-rollback signer/witness: NOT ESTABLISHED.
- v1→v2 financial migration, durable accounting and replay: NOT TESTED / NOT ESTABLISHED.
- Independent QA and Release acceptance: PENDING.
- Private \`BLAZE_PROJECT_REGISTRY_v11_20261027.json\`: not accessible through the available Google Drive connector surface; exhaustive Library listing found only v3–v7 snapshots. No older registry was substituted.

No physical flash/reset, live coin or money operation, production migration, signing, merge, release tag or deployment occurred. **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**


## UTC00 follow-up — phase-2 spliced comment delimiters

**Source/test commit:** \`e570d74848e80f06986b37b90dc439e1ed67a2dd\`  
**PR branch:** \`phoenix/hardware-cpp-preprocessor-boundary-20261121-utc23\`  
**Parent #338:** \`1a6a7cacf95722a78330d70de057e858143520f2\`

### Additional defect reproduced

C++ translation phase 2 removes backslash-newline pairs before comment token recognition. The prior normalizer did not recognize comment openers/terminators when a splice occurred between delimiter characters. This caused a split block-comment opener to be tokenized as ordinary code, collapsing meaningful double spaces inside a comment and producing a false-equivalence. A split terminator could be reported as an unterminated block comment.

The test-only commit \`1f73829347860367739bde3090f5957309682730\` added three regressions:
- block-comment opener split by a splice;
- block-comment terminator split by a splice;
- line-comment opener split by a splice.

The corrected test-only exact-head Quarantine run [#44968171894](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44968171894), job \`137041798295\`, failed at \`block-comment-opener-splice-preserves-content\` as expected. An earlier malformed fixture-placement commit \`109ae4b1b0d204a76faff8e8bdc4a4c15af34db7\` produced a Python \`IndentationError\` in run [#44968099982](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44968099982), job \`137041589116\`; that was corrected in \`1f738293...\` before the valid RED run and was not a source failure.

### Source correction

The normalizer now has shared \`splice_end()\` / \`skip_splices()\` helpers. It recognizes \`//\` and \`/*\` delimiters across phase-2 splices, scans block-comment terminators across splices, and preserves the original comment bytes for parity comparison. The same splice helper is used for ordinary code outside literals/comments/directives.

### Exact-source verification

Focused Quarantine [#44968280056](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44968280056), job \`137042139146\`, **SUCCESS** on source/test SHA \`e570d74848e80f06986b37b90dc439e1ed67a2dd\`:
- C++ normalizer: **17/17 PASS**.
- Existing ESP32/ESP8266 parity, quarantine, poll, pending journal, coin-gate and failure-injection suites completed successfully.
- Workflow output explicitly retains \`SIMULATED_ONLY=1\` and physical coin/relay/power-cut acceptance flags = 0.

Full BlazePwifi build [#44968280055](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44968280055) validation job \`137042209695\` **FAILED** at inherited QA-owned \`Missing poll signature check\` in the ESP8266 controller sketch. Target jobs were still running at the time of this handover update; no aggregate target-build conclusion is made here. Downstream simulation/signing/publication remain gated. Do not add a guessed \`response_sig\` or weaken default-deny.

### Live coordination

- #339 remains OPEN / DRAFT / UNMERGED; no firmware sketch/runtime or controller/financial API changed.
- #239 remains OPEN/DRAFT Phase-A deny; #254 remains OPEN/DRAFT ControllerAuthV1Lab; #283 remains OPEN/DRAFT main-based. At the current #283 head, append failure returns before \`clearPending()\`, but \`quarantinePending()\` has no active callsite and register/poll still lack an approved \`response_sig\`.
- Master PR #288 remains OPEN/DRAFT at \`0fdb43c20fc6b68699e229b5cdc8a7e7a4efbe93\`. Its latest UTC23 role table includes #338 but not this #339 follow-up; Master must refresh its own exact-head inventory. Hardware did not edit Master-owned coordination files.
- Private \`BLAZE_PROJECT_REGISTRY_v11_20261027.json\` remains inaccessible through the available Google Drive/Library surface; no older registry was substituted.

**Disposition:** host-lab correction CI VERIFIED; SIMULATED ONLY; physical acceptance NOT TESTED; HARDWARE ACCEPTED NO; PRODUCTION NO-GO.
