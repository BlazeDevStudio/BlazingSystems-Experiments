# PHX-HARDWARE UTC10 — output-enable active-level mutation guards

**Task:** #177 / existing DRAFT PR #354. **Role:** PHX-HARDWARE. **Status:** focused source-lab change CI VERIFIED; Full integration and physical acceptance are not accepted.

## Exact source and branch

- Repository: `BlazeDevStudio/BlazingSystems-Experiments` (repository ID `1389289885`).
- Branch: `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05`.
- Base: `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- Source/test commit: `46a0af372bef5b0e48f538846aa59407227e3a24`.
- Scope: only `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/output_enable_sequence_lab.py` changed in this task. Both production sketches are unchanged by this follow-up.

## Proven test gap and correction

The previous host lab verified an OFF write before OUTPUT and an OFF confirmation after OUTPUT, but did not reject an intervening active-level write. A test-first mutation inserted an active relay write after the preloads and before OUTPUT; the old harness allowed it.

- RED: [#45799017209](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45799017209), job `139837027426`, failed at the expected new mutation: `ESP8266: mutation survived: relay-active-before-output-enable` (the prior harness had no active-level invariant).
- Earlier helper iterations exposed newline/anchor construction mistakes; these were corrected before the valid RED run. They are not counted as acceptance evidence.

The harness now records every `digitalWrite` in the extracted `configureRuntimePins()` and rejects any active-level write to either newly assigned relay or LED pin for both active-high and active-low polarities. It injects four active-level mutations per board: relay/LED before OUTPUT and relay/LED after OUTPUT but before the OFF confirmation.

## Exact-source GREEN evidence

- Push focused: [#45799336363](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45799336363), job `139838136565`, PASS.
- PR focused: [#45799349008](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45799349008), job `139838180750`, PASS.
- Both logs show `12/12 output-enable checks PASS`, with all eight active-level mutations rejected (four per board), plus the existing missing-preload mutation rejected on both boards.
- Existing poll-intake, remote-config deny and request-auth mutation suites also pass in these focused runs.

## Other exact-head gates (not Hardware-owned)

- Native synthetic [#45799349143](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45799349143), job `139838182266`, FAIL at QA-owned `tests/v060_vendo_sequence_contract.py` assertion requiring active `clearPending(true/false)` callsites. This deny-only candidate intentionally preserves pending evidence and has no active disposition callsite; Hardware did not edit QA-owned tests.
- Full build [#45799349134](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45799349134): mandatory handover freshness failed before this handover was committed; target jobs were still running at the initial read. Re-run on a post-handover exact head is required.
- ESP32 Mbed TLS matrix [#45799349049](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45799349049): source-contract passed; target builds were still running at the initial read.

## Safety and limitations

- Candidate remains deny-only. No positive coin admission, relay admission, unsigned response consumption, active pending disposition, CORE API, finance, signer, witness, or COE destination changed.
- This is host/source-extracted SIMULATED / CI VERIFIED test tooling. GPIO voltage, relay contact transient, coin acceptor, LittleFS power-loss, electrical pulse/recovery, 150 controlled power cuts, and 30-device/24-hour soak remain NOT TESTED.
- HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO.

## Next exact action

PHX-QA must reconcile the legacy active-`clearPending` and `config_revision` assertions with the intentionally deny-only / pending-evidence-preservation candidate. PHX-CORE must publish the approved authenticated register/poll and receipt/disposition contract before Hardware implements any positive response consumer. PHX-MASTER must refresh its #354 exact-head pin after this documentation commit.
