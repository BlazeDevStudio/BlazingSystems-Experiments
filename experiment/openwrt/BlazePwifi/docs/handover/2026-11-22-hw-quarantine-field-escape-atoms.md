# PHX-HARDWARE handover — quarantine log escape-atom truncation

**Date:** 2026-11-21 UTC17  
**Role:** PHX-HARDWARE  
**Tasks:** #177 hardware safety / #266 cleanup-first  
**PR:** [#335 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/335), child of [#329](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/329)  
**Branch:** \`phoenix/hardware-quarantine-field-escape-boundary-20261122-utc16\`  
**Base #329 HEAD:** \`41efc1ddf4a101d7d1cb4428dcea2662ade6936e\`  
**Source/test SHA:** \`8ed751bf3371337fbd774b69ba61ddb820933be6\`  
**ESP32 sketch blob:** \`a2c767be512ebb47ae93190ab045c2659c3426b3\`  
**ESP8266 sketch blob:** \`098a46f698fd672595a9c0cc62b640ac41d84959\`  
**Lab blob:** \`f011522386a5692c689623d7fc898dc5d49cb1af\`

## Proven defect

Both sketches previously built a bounded quarantine field by appending encoded atoms up to \`maxLen\`, then removing three trailing bytes to make room for \`...\`. When the final encoded atom was longer than one byte, this trim could split the atom and leave a dangling backslash. The exact prior helper is present at the PR base #329 HEAD; the legacy negative-control implementation in the lab reproduces the same trimming behavior.

Affected atoms:
- escaped backslash: \`\\\\\`
- carriage return: \`\\r\`
- line feed: \`\\n\`
- tab: \`\\t\`
- reason/target delimiter space: \`\\x20\`

A dangling escape makes the quarantine record ambiguous and can corrupt the intended field boundary. This is a source-formatting/persistence-record integrity defect, not a positive coin-admission defect.

## Correction

Both ESP32 and ESP8266 \`quarantineLogField()\` helpers now use the same two-pass algorithm:

1. Measure complete encoded atom lengths without splitting an escape.
2. Detect whether the encoded value exceeds the field limit.
3. Reserve three bytes for \`...\` when truncation is required and the limit permits a suffix.
4. Append only complete encoded atoms up to the reserved content limit.
5. Append the suffix only after the complete-atom boundary is reached.

The helper bodies are byte-identical at the current source/test SHA. Existing escaping semantics for backslash, CR, LF, TAB, and the \` REASON=\` / \` TARGET=\` delimiter spaces are preserved.

No journal schema, record version, controller API, finance path, signer/witness, relay output, GPIO, or coin-admission behavior changed.

## Regression and failure-injection evidence

The Hardware-owned \`quarantine_readback_lab.py\` now checks:

- 4/4 truncation-boundary cases for backslash, CR, LF and TAB.
- 161/161 output-limit sweeps across a mixed value containing all escape forms and both reason/target delimiters.
- 5/5 legacy negative controls: the exact pre-fix trimming algorithm reproduces a dangling backslash at the boundary.
- Existing quarantine scenarios: 36/36 per board.
- Total source-extracted host scenarios: 72/72 across ESP32 and ESP8266.

The legacy control is a deliberate test fixture, not production code. It verifies that the regression would reject the old algorithm. No separate historical CI RED run is claimed for this task.

## Exact-source CI

All results below are tied to source/test SHA \`8ed751bf3371337fbd774b69ba61ddb820933be6\`.

- **Quarantine byte-readback:** [run #44928481634](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44928481634), job \`136919704475\`: **SUCCESS**. Logs assert the literal SHA, 4/4 escape atoms, 161/161 limit sweep, 5/5 legacy dangling-escape reproductions, 36/36 quarantine scenarios per board and 72/72 combined host scenarios.
- **Relay/output:** [run #44928481496](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44928481496), job \`136919704091\`: **SUCCESS**. ESP32 boot-polarity job \`136919704457\`: **SUCCESS**. Logs assert the same literal SHA.
- **Full BlazePwifi:** [run #44928481524](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44928481524), validation job \`136919781347\`: **FAILURE** at the inherited QA-owned \`Missing poll signature check\` in the ESP8266 sketch. The run completed with all 14 firmware target jobs **SUCCESS**; Android job `136919781226` was **CANCELLED**. Update bundle and several simulations were skipped; publish prerelease/release, production sign handoff, Android emulator and candidate gate were cancelled. No Full integration PASS is claimed.

The Full failure is not fixed by adding an invented signature. Main register/ping and poll replies still do not emit the required controller \`response_sig\`; member endpoints do emit their own signatures, which are a different contract. PHX-CORE must publish the canonical authenticated register/poll and event-bound receipt contract, and PHX-QA owns the independent fixture/assertion change.

## Scope and classification

- **SIMULATED:** source-extracted host tests and legacy mutation control.
- **CI VERIFIED:** exact-source focused Quarantine and Relay/output workflows.
- **Full integration:** FAILED at the inherited poll-signature validation gate; target matrix was complete except Android at the time of handover.
- **HARDWARE ACCEPTED:** NO. Physical LittleFS behavior, coin acceptor, relay/electrical pulse, power-loss recovery and controlled power cuts remain NOT TESTED.
- **PRODUCTION READY:** NO-GO.

The CI explicitly reports \`SIMULATED_ONLY=1\` and \`PHYSICAL_POWER_CUT_VERIFIED=0\`.

## Branch and ownership boundaries

- #335 is a separate child of #329 at \`41efc1d...\`.
- #334 is a sibling child of #329; it is not part of #335.
- #329 is a child of #327.
- #327 → #330 → (#331, #332) → #333 remains a separate branch lineage.
- #239 and #254 remain separate stacked drafts; #283 remains a separate main-based draft.
- No rebase, retarget, merge, force-push or source migration was performed.

## Next exact actions

1. **PHX-QA:** independently review the escape-boundary and legacy negative-control tests; retain fail-closed checks.
2. **PHX-CORE:** publish canonical register/poll and event-bound receipt bytes, signature scope and golden vectors.
3. **PHX-MASTER:** refresh \`ROLE_ASSIGNMENTS.md\`, \`INTEGRATION_MATRIX.md\` and #172 to include #334/#335 and the exact current #239/#254/#283/#327–#335 refs.
4. **PHX-RELEASE:** continue the ESP32 Mbed TLS/toolchain compatibility investigation and shared validation freshness work.
5. **PHX-HARDWARE:** keep coin admission default-deny; do not wire quarantine lifecycle or positive poll handling without approved cross-role contracts.

No physical flashing, device reset, live money, production migration, signing, release tagging, deployment or cutover was performed.


## UTC17 follow-up — centralize quarantine escape-atom classification

A cleanup audit found the backslash, CR, LF, TAB, and REASON=/TARGET= delimiter escape classifier duplicated in both passes of quarantineLogField(): one copy measured encoded length and another emitted the bytes. A future edit to only one copy could make the size calculation disagree with output and reintroduce a split or malformed quarantine field.

The behavior-preserving cleanup:

- Adds static const char* quarantineLogFieldEscapeAt(const String&, size_t) to both ESP32 and ESP8266 sketches.
- Routes both the measurement pass and output pass through the same helper.
- Keeps the helper byte-identical across boards.
- Adds the extracted helper to the board-parity lab and raises the checked shared-helper count to 23/23.
- Adds failure injection that changes only ESP8266's \x20 delimiter mapping to \x21; the parity guard rejects that drift.

No encoded output, truncation limit, suffix policy, journal schema, controller contract, finance path, GPIO/relay behavior, or coin admission changed.

### Exact-source verification

Source/test SHA: 182d6393dbeeb342395f06477b54ff30dada2f1b

- Quarantine [#44932261678](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44932261678), job 136931241526: SUCCESS. Exact extracted C++ compile passed; 23/23 shared helper parity; escape-mapping drift mutation rejected; 4/4 boundary cases, 161/161 length sweep, 5/5 legacy dangling-escape controls, 36/36 quarantine scenarios per board, 72/72 combined scenarios.
- Relay/output [#44932261680](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44932261680), job 136931241682: SUCCESS. ESP32 boot-polarity job 136931241425: SUCCESS.
- Full [#44932261738](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44932261738), validation job 136931318092: FAILURE at the inherited QA-owned Missing poll signature check. All 13 firmware target jobs passed; Android was still running at the last read. Downstream update/simulation/signing/release steps were skipped. No Full integration PASS is claimed.

Classification remains SIMULATED / focused CI VERIFIED; HARDWARE ACCEPTED NO; PRODUCTION NO-GO. The source cleanup does not resolve #177 physical pulse/relay acceptance or the CORE-owned authenticated register/poll contract.


## Final exact-head completion — Full matrix readback

A later job read completed both Full runs. The earlier "Android still running" note above is superseded by this final readback:

- Source/test Full [#44932261738](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44932261738): **14/14 firmware-target + Android jobs SUCCESS**; validation job 136931318092 **FAILED** at the inherited QA-owned Missing poll signature check. All downstream update-bundle, simulation, signing, candidate and publication jobs were skipped.
- Final docs-head Full [#44932620569](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44932620569): **14/14 firmware-target + Android jobs SUCCESS**; validation job 136932344293 **FAILED** at the same inherited Missing poll signature check. All downstream release/signing/candidate jobs were skipped.

Thus the target build matrix is CI VERIFIED at both heads, but Full integration remains FAILED. No controller signature was invented and no QA-owned assertion was weakened.
