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


## PHX-HARDWARE UTC10 follow-up — independent relay/LED polarity matrix

**Updated:** 2026-11-26T10:39:53.455Z
**Task:** #177 / #354 · **Role:** PHX-HARDWARE
**Branch:** `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05`
**Base:** `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`
**Source/test SHA:** `046bced7c8765d5e27daeb2885f0654f9ec62149`
**Scope:** `experiment/openwrt/BlazePwifi/docs/handover/2026-11-26-hw-output-enable-active-write-guards-utc10.md` and `output_enable_sequence_lab.py` only for the new follow-up; production ESP8266/ESP32 sketches are unchanged by this follow-up.

The prior source-extracted lab set relay and LED polarity together. The production function uses independent `runRelayActiveHigh` and `runLedActiveHigh` settings, so the symmetric-only scenarios could not detect a polarity-coupling regression. The lab now exercises all four independent combinations (relay AH/LED AH, relay AH/LED AL, relay AL/LED AH, relay AL/LED AL) on both boards. It also injects incorrect cross-use of the other output's polarity for the old-pin shutdown, pre-output preload, and post-enable OFF confirmation.

**Exact-source focused evidence**
- PR [#45802963675](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45802963675), job `139850670712`: PASS. Logs show all four combinations per board and `14/14 injected regressions rejected` (seven per board), plus existing poll-intake, remote-config-deny and request-auth guards.
- Push [#45802954262](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45802954262), job `139850639639`: PASS with the same exact-source output.
- The first attempt at `2ab43c71ff6397346bfe0948974823a4413f345f` was a test-authoring error: the polarity mutation helper expected two OFF writes but the real function has three (old-pin shutdown, preload, post-enable confirmation). The failed runs [#45802855713](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45802855713) and [#45802846230](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45802846230) are not accepted regression evidence. The count was corrected to three in `046bced7`.

**Independent / integration gates**
- Native synthetic [#45802963561](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45802963561), job `139850670920`: FAIL at QA-owned `tests/v060_vendo_sequence_contract.py` assertion requiring active `clearPending(true/false)` callsites. The deny-only candidate intentionally preserves pending evidence and has no active disposition callsite; Hardware did not edit QA-owned tests.
- Full PR [#45802963678](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45802963678), validation job `139850939852`: FAIL at mandatory handover freshness because this source commit preceded this handover refresh. A new final-docs-head Full run is required; no Full PASS is claimed.
- ESP32 Mbed TLS matrix [#45802963530](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45802963530) was pending when this handover was prepared; no result is claimed here.

**Safety / evidence boundary**
- This is host/source-extracted SIMULATED / CI VERIFIED test tooling. GPIO voltage, relay contact transient, physical coin acceptor, LittleFS power-loss, electrical recovery, 150 controlled power cuts and 30-device/24-hour soak remain NOT TESTED.
- HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO.
- No positive coin/relay admission, response trust, pending disposition, CORE API, finance, signer, witness, COE destination, flash, device reset, payment operation, release tag, merge or deployment changed.

**Next exact action:** inspect the new final-docs-head Full and ESP32 matrix runs; PHX-QA reconciles the deny-only pending-evidence assertion; PHX-CORE publishes the authenticated register/poll and receipt/disposition contract; PHX-MASTER refreshes the #354 head pin in Master-owned coordination files.


## PHX-HARDWARE UTC10 final exact-docs-head validation — 2026-11-26

**Updated:** 2026-11-26T10:45:04.754Z · **PR:** [#354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/354) · **Branch:** `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05`
**Docs HEAD tested:** `45418f9069ba40ad3d2a71930b8469d5d8623de7` · **Source/test:** `046bced7c8765d5e27daeb2885f0654f9ec62149`
**State:** OPEN / DRAFT / UNMERGED; deny-only.

### Final exact-head CI
- Focused Hardware PR [#45803466556](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45803466556), job `139852438950`: PASS.
- ESP32 core matrix PR [#45803466620](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45803466620): PASS — source-contract `139853189956`, core 3.3.13 `139853190096`, core 4.0.0 `139853189558`.
- ESP32 core matrix push [#45803459247](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45803459247): PASS — source-contract `139852414868`, core 3.3.13 `139852415194`, core 4.0.0 `139852415334`.
- Focused push [#45802954262](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45802954262), job `139850639639`: PASS. Exact-source log: 8/8 independent board/polarity scenarios pass; 14/14 injected regressions rejected.
- Full [#45803466880](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45803466880): terminal FAILURE. Mandatory handover freshness, handover fail-closed tests, HND-0700, CI-0701, BusyBox decode, static validation, v0.3, admin security, config and template-gallery checks PASS. QA-owned `tests/controllers.sh` then FAILS because it requires `config_revision` in both sketches. The deny-only candidate intentionally does not consume unsigned remote configuration. All 14 target/Android jobs PASS (ESP8266, ESP32, Android, x86_64, Ruijie and Orange Pi targets); simulations, update bundle, candidate gate, signing and publication are SKIPPED.
- Native [#45803466968](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45803466968), job `139852441371`: FAIL at QA-owned `tests/v060_vendo_sequence_contract.py` requiring active `clearPending(true/false)` callsites. Hardware intentionally preserves pending evidence and has no active disposition callsite.

### Reconciliation
The prior exact-head Full [#45802963678](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45802963678) failed the pre-refresh handover freshness gate. This final-docs-head run [#45803466880](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45803466880) proves the freshness gate now passes; the remaining failure is QA-owned protocol parity. No Hardware change to QA-owned scripts is authorized.

### Next owner actions
- **PHX-QA:** replace legacy `config_revision` and active-clear expectations with deny/no-callsite/pending-evidence-preservation assertions; independently review the polarity matrix.
- **PHX-CORE:** publish the authenticated register/poll and event receipt/disposition contract (canonical serialization, mandatory key provisioning, controller/target binding, freshness and replay).
- **PHX-MASTER:** refresh `ROLE_ASSIGNMENTS.md` and `INTEGRATION_MATRIX.md` from stale #354 `e7f63da2` to current #354 head; branch-protection reads remain false on main and v0.6.
- **PHX-HARDWARE:** keep coin and relay admission denied; rerun Full after QA/CORE owner changes.

Physical GPIO/relay transient, coin acceptor, LittleFS power-loss, electrical recovery, 150 power cuts and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO. No positive coin/relay admission, financial logic, signer/witness, COE destination, flash, reset, live-money operation, migration, release tag, merge or deployment changed.
