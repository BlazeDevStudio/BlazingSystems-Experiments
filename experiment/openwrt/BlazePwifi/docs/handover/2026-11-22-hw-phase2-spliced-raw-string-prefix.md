# PHX-HARDWARE — phase-2-spliced C++ raw-string prefix correction (UTC13)

**Disposition:** exact-source focused Quarantine and Relay CI VERIFIED · Full controller validation BLOCKED by inherited CORE/QA contract mismatch · SIMULATED ONLY · HARDWARE ACCEPTED NO · PRODUCTION NO-GO.

- Role: PHX-HARDWARE
- Repository: `BlazeDevStudio/BlazingSystems-Experiments` (repository ID `1389289885`)
- PR: [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327), OPEN / DRAFT / UNMERGED
- Branch: `phoenix/hardware-prepoll-edge-abort-20261119`
- Parent/base: #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`
- Source/test commit: `e560dd0d2c54a4471561b33189614e64578a9de0`
- Final documentation head: recorded in the PR after this handover commit

## Proven defect

The shared Hardware host-lab C/C++ lexer did not recognize a raw-string prefix when C++ translation phase 2 joined physical lines inside that prefix. Examples:

- `R\\` followed by a physical newline and then `"PHX(`
- `u8\\` followed by a physical newline and then `R"PHX(`

The old scanner treated the quote as an ordinary string opener. Quotes inside the raw body then ended the mask early; a brace in raw-string content could be mistaken for a function-closing brace. The source-exact extractor could consequently truncate a function or fail with `unterminated C/C++ string or character literal`.

## Test-first RED

- Test-only commit: `fcfc9a0a1fc23d54d53b6f9e8b145a7ac9be4cc6`.
- Quarantine push [#45029135144](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029135144), job `137228604607`: expected FAILURE at `extract(fixture, "splicedRawStringFixture")`, `AssertionError: unterminated C/C++ string or character literal`.
- This is the intended test-first defect reproduction, not an infrastructure failure.

## Source correction and exact-head GREEN

Changed only these Hardware-owned host-lab files:

- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/firmware_lab_source.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_response_failclosed_lab.py`

The shared lexer now:

- Matches raw-string prefixes across phase-2 line splices, including `R`, `u8R`, `uR`, `UR` and `LR`.
- Checks the preceding token character after undoing adjacent phase-2 splices, avoiding a false raw-prefix start after an identifier joined across lines.
- Preserves original physical offsets and newline positions for the existing mask contract.
- Adds exact-source fixtures for a splice between `R` and the quote and between `u8` and `R`; each raw body contains embedded quotes and braces that previously broke extraction.

Exact-source evidence at `e560dd0d2c54a4471561b33189614e64578a9de0`:

- Quarantine push [#45029446607](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029446607), job `137229561148`: **SUCCESS**.
- Quarantine PR [#45029451026](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029451026), job `137229575286`: **SUCCESS**.
- Both emit `FIRMWARE_LAB_PHASE2_SPLICED_RAW_PREFIX_PASS 2/2`; complete Hardware source-extracted host suite reports **72/72 PASS**.
- Relay/output PR [#45029450997](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029450997), jobs `137229575293` (ESP32 boot polarity) and `137229575435` (source/output polarity): **SUCCESS**.

## Full integration remains blocked

- Full push [#45029446601](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029446601), validation job `137229561243`: **FAILURE** at inherited `Missing poll signature check` in `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`.
- All 14/14 target/platform + Android jobs completed **SUCCESS** on the push run.
- Full PR [#45029450993](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029450993), validation job `137229643781`: **FAILURE** at the same inherited assertion. At this handover, 13 target/platform jobs had completed SUCCESS and Android was still in progress; no overall Full PASS is claimed.
- The failure is the pre-existing positive poll-signature assertion against the current deny-only firmware/producer boundary. PHX-HARDWARE did not edit `tests/controllers.sh`, invent `response_sig`, or weaken default-deny. CORE owns the authenticated response contract; QA owns its independent assertions.

## Ownership and safety boundary

- No production `.ino` sketch/runtime, GPIO, relay, coin admission, server/API, financial ledger, migration, replay, signer/witness, QA-owned test, Release workflow or COE destination changed.
- No branch rebase, retarget, merge, force-push, physical flash, reset, signing, release tag, deployment, live-money test or customer operation occurred.
- Logs explicitly retain `SIMULATED_ONLY=1`, `PHYSICAL_COIN_PULSE_ACCEPTANCE=0`, `PHYSICAL_RELAY_ACCEPTANCE=0` and `PHYSICAL_POWER_CUT_ACCEPTANCE=0`.

## Next exact action

PHX-CORE and PHX-QA must resolve the authenticated register/poll and event-bound receipt contract without weakening deny behavior. PHX-MASTER must refresh the #327 exact-head pin after this change. PHX-HARDWARE will revalidate the live stack before the next owned task; physical coin/electrical tests, 150 power cuts, 30-device/24-hour soak, protected anti-rollback witness and independent release signoff remain open.
