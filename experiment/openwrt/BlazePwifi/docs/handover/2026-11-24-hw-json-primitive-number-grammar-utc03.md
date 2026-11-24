# PHX-HARDWARE UTC03 — JSON primitive number/literal grammar coverage

**Observed:** 2026-11-24 UTC03  
**Role:** PHX-HARDWARE  
**Task:** #177 / #266 / #349  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** phoenix/hw-json-array-primitive-guard-20261124-utc00  
**Parent #347 exact base:** 960184670379f01e20f0e7e8bc23b3e5eedacd3f  
**Exact source/test SHA:** 40b80bb075c008f3251c31f09a4dc9eb9e6c17e5  
**PR:** [#349 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)

## Work completed

Expanded the existing source-extracted parser lab used by both ESP8266 and ESP32 firmware. This is test coverage only; neither production .ino sketch changed.

The parser already implements strict JSON primitive grammar. The gap was that the previous suite tested only a small subset of numeric/literal boundaries. The new lab now exercises:

- **9 valid JSON numbers:** zero, negative zero, positive/negative integers, positive/negative fractions, and exponent forms with lower/upper-case exponent markers and optional signs.
- **16 malformed primitive values:** leading-zero integers (01, -01), leading plus, missing integer/fraction/exponent digits, doubled minus, non-JSON NaN/Infinity, upper-case/truncated literals, literal suffixes, malformed exponents and hexadecimal-looking numbers.
- **4 source-derived fail-open mutations:** accept leading-zero integers, accept an empty fraction, accept an empty exponent, and accept a truncated true literal.

Each malformed primitive is placed before the root ok:true member so the source-extracted parser must validate it before the status can be observed.

## Test-first history and harness correction

- Test expansion commit: [0cefcfe](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/0cefcfe4c2d362790579879b6b3f9cdb895b1a43).
- Initial Quarantine [run #45321792211](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45321792211), job 138201820092, **FAILED in the test harness**, not in the production parser. The empty-fraction mutation removed the only use of fractionStart, and the host compile correctly stopped under -Werror for an unused variable.
- Harness correction: [40b80bb](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/40b80bb075c008f3251c31f09a4dc9eb9e6c17e5). The fraction/exponent mutants now retain the comparison variable but bypass the rejection branch, allowing the mutation to compile and then demonstrate the expected fail-open behavior. No firmware source or runtime behavior changed.

The failed harness run is preserved as a failed run; it is not relabeled as firmware RED evidence.

## Exact-head focused CI

All results below check out exact source/test SHA 40b80bb075c008f3251c31f09a4dc9eb9e6c17e5.

### Quarantine Byte Readback

[Run #45321927194](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45321927194), job 138202267188: **SUCCESS**.

Both ESP8266 and ESP32 logs show:

- Primitive grammar: **9/9 valid accepted, 16/16 malformed rejected**.
- Primitive fail-open mutations: **4/4 rejected** on each board.
- Existing composite/string grammar: **6/6 valid and 12/12 malformed** on each board.
- Existing source quarantine scenarios: **36/36 per board**.
- The job retained SIMULATED_ONLY=1; physical coin acceptor and power-cut flags remain zero.

### Relay Output Polarity

[Run #45321927191](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45321927191):

- Source/output job 138202267005: **SUCCESS**.
- ESP32 boot-polarity job 138202267615: **SUCCESS**.
- Both boards report the same primitive and composite grammar counts and mutation rejection.
- Coin pulse capture remains **17/17 per board** in the source-extracted host lab.
- Physical relay/coin/power-cut acceptance flags remain zero.

### Full BlazePwifi

Push-triggered [run #45321921703](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45321921703) at the same SHA is terminal **FAILURE**:

- All **13/13 firmware target/platform jobs** succeeded.
- Android job succeeded.
- Validation job 138202355678 failed at the inherited **Missing poll signature check** in tests/controllers.sh.
- The 12 dependent simulation/update/signing/candidate/publication stages were skipped.

The PR-triggered Full run [#45321927236](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45321927236) also failed its validation job 138202367440 at the same assertion; its remaining target jobs were still completing when this handover was written. No Full integration PASS is claimed.

## Contract, ownership and safety

- Current main CGI producer blob 2e3a1430d08cc6606429a042df3b5848f53c7267 still does not emit the approved authenticated response_sig envelope for register|ping or poll.
- PHX-CORE owns the producer contract, canonical response bytes and golden vectors. PHX-QA owns the inherited parity assertion. PHX-HARDWARE will not invent a positive signature or weaken default-deny.
- PR #239 (Phase-A deny), #254 (ControllerAuthV1Lab) and #283 (parallel sketches) remain OPEN / DRAFT / UNMERGED at their independently revalidated heads. #348 remains a separate child of #254. No stack was merged, rebased or retargeted.
- #266 remains OPEN with 0/7 cleanup tracks complete.
- COE #26 remains FROZEN / DRAFT / UNMERGED; no source was copied or promoted.
- BLAZE_PROJECT_REGISTRY_v11_20261027.json was not available through the authorized Library search/list surface, and no Google Drive connector is exposed in this runtime. No older registry was substituted.
- No finance, ledger, signer, witness, migration, relay authority, production GPIO, physical device, customer state, release or deployment behavior changed.

## Evidence classification and next action

- Strict JSON primitive/composite parser regressions: **SIMULATED / CI VERIFIED**.
- Firmware target build matrix: **CI VERIFIED** for the 13/13 target jobs in the terminal push run; Full integration still **FAILED** at controller protocol parity.
- Physical coin acceptor, electrical pulse/relay recovery, LittleFS power-loss, 150 controlled power cuts and 30-device 24-hour soak: **NOT TESTED**.
- **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

**Next exact action:** PHX-CORE publishes the approved authenticated register/poll response envelope and canonical golden vectors; PHX-QA reconciles Missing poll signature check against that contract; PHX-MASTER refreshes #349 source/test/docs pins in the role assignment and integration matrix. PHX-HARDWARE then reruns Full integration on the approved exact stack without relaxing default-deny.
