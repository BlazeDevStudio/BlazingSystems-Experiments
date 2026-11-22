# PHX-HARDWARE — literal-true #elif active-mask correction (UTC12)

**Disposition:** focused Quarantine and Relay/output CI VERIFIED · Full validation blocked by inherited poll-signature gate · SIMULATED ONLY · HARDWARE ACCEPTED NO · PRODUCTION NO-GO

- Role: PHX-HARDWARE
- Repository: `BlazeDevStudio/BlazingSystems-Experiments` (repository ID 1389289885)
- Task: #172 / #177 / #266 / #327
- PR: [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327), OPEN / DRAFT / UNMERGED
- Branch: `phoenix/hardware-prepoll-edge-abort-20261119`
- Base: #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`
- Source fix commit: `1ecdb1ac8a49a1a8c464c0dcef613a11f0f4b8cb`
- Corrected test-fixture commit: `815e0f15d02c0df753f9f4cf9522867bc2f2ccf1`

## Defect

The offset-preserving C/C++ active-code masker conservatively keeps an unknown `#if` branch visible. When that branch is followed by a literal `#elif 1`, the `#elif` body may be active if the unknown condition is false, so it must remain visible. But a literal-true `#elif` also guarantees that every subsequent `#elif`/`#else` in the same chain is unreachable.

Before this correction, the unknown-branch path set the current activity state but did not set `frame["branch_taken"]` when the `#elif` condition was literal true. The later `#else` therefore remained visible to source-extracted callsite checks.

## Source correction

File:
`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/firmware_lab_source.py`

Within the `frame["branch_taken"] is None` path, after evaluating the literal `#elif` condition, the masker now sets `frame["branch_taken"] = True` when the condition is `True`. Unknown macro expressions remain conservative; this is not a full C preprocessor.

No ESP8266/ESP32 sketch, runtime GPIO/relay behavior, shared API, CORE ledger, finance, signer/witness, QA-owned assertion, Release workflow, or production migration changed.

## Test-fixture correction and evidence integrity

The test-only commit `4ddf41cff44105ec8757362348c0cba6203db6fb` initially added the intended `#if UNKNOWN / #elif 1 / #else` fixture, but inspection after the first failure found that its Python string literals contained double-escaped backslash-n sequences. The first failure therefore did **not** prove the intended preprocessor-chain defect and is **not** counted as a valid RED result.

The fixture was corrected in `815e0f15d02c0df753f9f4cf9522867bc2f2ccf1` to use actual logical newlines. The exact-head focused CI then verified the intended case on both board paths. No valid baseline RED was claimed for the corrected fixture.

## Exact-head CI

Final source/test head: `815e0f15d02c0df753f9f4cf9522867bc2f2ccf1`.

- Quarantine [run #45024545299](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45024545299), job `137214576285`: **SUCCESS**.
  - Both ESP8266 and ESP32 report `POLL_RESPONSE_DEBOUNCE_ELIF_CHAIN_REJECTED 1/1`.
  - Both boards report `POLL_RESPONSE_DEBOUNCE_CALLSITE_DECOY_REJECTED 2/2`.
  - Existing source-extracted host suites report 72/72 scenarios PASS.
- Relay/output [run #45024545314](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45024545314), source job `137214576659`: **SUCCESS**; ESP32 boot-polarity job `137214576885`: **SUCCESS**.
  - Both boards report the same #elif-chain and callsite-decoy markers.
  - Existing poll-window, edge snapshot, pulse-capture and output-deny host checks pass.
- Full BlazePwifi build [run #45024545291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45024545291): **FAILURE** at validation job `137214577061`.
  - The validation script `experiment/openwrt/BlazePwifi/tests/controllers.sh` reports `Missing poll signature check` in the ESP8266 sketch.
  - All 13 firmware target jobs and the Android job completed SUCCESS.
  - Candidate, simulation, signing and publication downstream jobs were skipped.

The focused tests are source-extracted host CI, not physical acceptance. The initial invalid fixture failure is disclosed rather than presented as a valid test-first RED.

## Evidence classification and blockers

- Active-code mask regression: **CI VERIFIED** at exact head above.
- Poll/edge/pulse and fake-storage behavior: **SIMULATED / CI VERIFIED** only.
- Physical coin acceptor, relay polarity, electrical pulse/recovery, EEPROM/LittleFS durability, 150 power cuts, and 30-device 24-hour soak: **NOT TESTED**.
- Authenticated register/poll response contract and separate authenticated configuration envelope: **NOT ESTABLISHED**.
- Protected anti-rollback signer/witness, v1→v2 financial migration, durable accounting/replay, independent QA and Release acceptance: **NOT ESTABLISHED / PENDING**.
- HARDWARE ACCEPTED: **NO**.
- PRODUCTION READY: **NO-GO**.

## Next exact action

1. PHX-CORE publishes the approved authenticated register/poll producer-consumer contract, separate configuration-auth envelope, and event-bound receipt/disposition contract with positive/negative golden vectors.
2. PHX-QA independently reconciles the `controllers.sh` poll-signature assertion against that approved contract; Hardware will not invent `response_sig` or weaken the gate.
3. PHX-HARDWARE revalidates the exact #327/#339/#340/#341 heads and continues the next unblocked Hardware-owned durability/pulse task without enabling coin admission.
4. PHX-MASTER refreshes the exact #327 head in `coordination/phoenix/ROLE_ASSIGNMENTS.md` and `INTEGRATION_MATRIX.md`; their currently published pins predate this UTC12 continuation.

**No merge, rebase, retarget, force-push, flash, device reset, signing, release tag, financial migration, or deployment occurred.**
