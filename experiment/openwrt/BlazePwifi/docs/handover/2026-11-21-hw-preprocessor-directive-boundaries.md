# PHX-HARDWARE handover — C++ preprocessor directive boundaries in board parity

**Date:** 2026-11-21 UTC15  
**Role:** PHX-HARDWARE  
**Tasks:** #177 hardware safety / #266 cleanup-first  
**PR:** [#334 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/334), child of [#329](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/329)  
**Branch:** \`phoenix/hardware-cpp-preprocessor-boundary-20261121-utc15\`  
**Base #329 HEAD:** \`41efc1ddf4a101d7d1cb4428dcea2662ade6936e\`  
**Test-first RED commit:** \`51b6784eaf1c0dc859e1dd30312b0afeb78c9aa6\`  
**Source/test GREEN commit:** \`aae180c7465266be58716b75d92760392132fb1a\`

## Proven host-lab defect

The C++ parity normalizer collapsed all code whitespace, including physical newlines that terminate preprocessor directives. Two valid function bodies could therefore normalize identically even though one declares a local variable after a macro definition and the other absorbs that declaration into the macro replacement list.

A local C++17 reproduction produced different executable exit codes (1 versus 7) while the original normalizer returned equality. This was a test-harness false-equivalence, not a production sketch defect.

## Test-first RED

The test-only commit added \`preprocessor-directive-newline-boundary\`.

- Quarantine [run #44919138586](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44919138586), job \`136891119378\`: expected failure, \`POLL_SAFETY_CPP_PARITY_NORMALIZER_FAIL: preprocessor-directive-newline-boundary\`.
- Relay/output [run #44919138608](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44919138608), job \`136891119647\`: same expected failure.
- Full build [run #44919138634](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44919138634), validation job \`136891120299\`: inherited QA-owned \`Missing poll signature check\`; this is not a Full integration pass.

## Correction

Only \`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py\` changed.

The normalizer now:

- Tracks beginning-of-logical-line state and recognizes \`#\` after optional horizontal indentation.
- Preserves a directive's full text and its logical line boundary instead of collapsing it into adjacent code.
- Retains backslash-newline directive continuations while canonicalizing CRLF/CR to LF.
- Continues collapsing ordinary code whitespace.
- Preserves string, character, raw-string and comment content.
- Removes ordinary phase-2 backslash-newline splices before code whitespace comparison.

The parity comparator deliberately prefers a false mismatch over a false equivalence when preprocessor directive formatting differs.

## Exact-source GREEN evidence

Source/test SHA: \`aae180c7465266be58716b75d92760392132fb1a\`.

- Quarantine [run #44921028102](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44921028102), job \`136896875917\`: **SUCCESS**.
- Relay/output [run #44921028119](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44921028119), job \`136896875904\`: **SUCCESS**; ESP32 boot-polarity job \`136896876278\`: **SUCCESS**.
- Both focused logs contain \`POLL_SAFETY_CPP_PARITY_NORMALIZER_PASS 14/14\` and \`POLL_SAFETY_CPP_PREPROCESSOR_SEMANTICS_PASS 2/2\`.
- The two compiled C++17 semantic fixtures return the expected distinct exit codes 1 and 7.
- Existing source-extracted board parity and failure-injection labs continue to run on both ESP8266 and ESP32.

Full BlazePwifi push [run #44921024377](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44921024377), same source/test SHA: validation job \`136896865204\` **FAILED** at the inherited QA-owned \`Missing poll signature check\`. All 14 target/platform plus Android build jobs completed **SUCCESS**; downstream simulation, signed import, update, signing, candidate and publication jobs were skipped. This does not clear the Full integration gate.

## Scope and classification

- No ESP8266/ESP32 production sketch, coin admission, GPIO, relay, controller API, finance, signer, witness, QA-owned assertion, Release workflow or COE destination changed.
- Firmware admission remains default-deny.
- **SIMULATED:** host C++17 normalizer and directive-semantic fixtures.
- **CI VERIFIED:** focused Quarantine and Relay/output workflows at the exact source/test SHA above.
- **Full integration:** FAILED at the inherited QA poll-signature assertion.
- **HARDWARE ACCEPTED:** NO; no physical coin/relay/electrical or power-cut testing was performed.
- **PRODUCTION READY:** NO-GO.

## Next exact actions

1. PHX-QA retains independent ownership of the controller poll-signature fixture and replaces the stale positive assertion only after CORE publishes the approved authenticated register/poll and event-bound receipt contract.
2. PHX-MASTER records #334 as a child of #329 and keeps #329 separate from the #330/#331/#332/#333 stack.
3. PHX-HARDWARE preserves the current default-deny behavior and revalidates the live stack before any further source work.

No merge, rebase, retarget, force-push, flash, production migration, signing, release tag, deployment or cutover was performed.