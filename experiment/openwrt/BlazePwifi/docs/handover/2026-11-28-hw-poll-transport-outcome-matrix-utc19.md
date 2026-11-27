# PHX-HARDWARE handover — poll transport outcome matrix (UTC19)

- **Repository:** `BlazeDevStudio/BlazingSystems-Experiments`
- **Role:** PHX-HARDWARE
- **PR:** [#365](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/365), OPEN / DRAFT / UNMERGED
- **Branch:** `phoenix/hw-poll-boundary-pulse-matrix-20261128-utc18`
- **Parent:** #364 at `ea765fb822e1c517db4e61c103b86d8eb2c66c92`
- **Documentation-first commit:** `71ea4c332227b58b6bc51a58908bc855bfadc0a8`
- **Source/test SHA:** `fcd5d7df210c8521f9c8fcc1019c8db8bdaf7eb0`
- **Focused exact-SHA evidence:** run #46055268572, job `140696113739`, PASS

## One task completed

Extended the source-extracted poll-deny harness with five transport outcomes across four independent relay/LED active-level combinations: 20 cases per board, 40 total. Outcomes cover immediate begin failure, empty timeout response, malformed response, server-error body, and a non-empty untrusted `insert=true` body. The harness checks that the pre-poll deny is already effective when `post("poll")` begins, outputs remain OFF throughout the wait and after return, pending pulse/nonce/target evidence is unchanged, and the poll timestamp advances only after return.

Added failure injection that consumes an untrusted positive response and briefly re-enables relay/LED outputs before the final deny. Both ESP8266 and ESP32 reject this transient active-write mutation (exit 20). Existing six timing windows × four polarity combinations per board remain passing.

## Exact CI and limitations

- Focused run [#46055268572](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46055268572), job `140696113739`: **PASS** at `fcd5d7df210c8521f9c8fcc1019c8db8bdaf7eb0`.
- Focused log includes `POLL_TRANSPORT_OUTCOME_PASS outcomes=5 polarity_combinations=4 cases=20` for both boards and transient-response mutation rejection for both.
- Mbed TLS run [#46055268521](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46055268521): PENDING; no terminal result claimed.
- Full runs #46055268629 (PR) and #46055260220 (push) failed the mandatory handover-freshness gate because this source/test SHA had not yet been recorded. Rerun after this docs synchronization.
- Last terminal Full integration result #46052478996 failed controller parity at `tests/controllers.sh:21` (`config_revision`); 13/13 firmware targets and Android passed, downstream signing/publication skipped.

## Scope and acceptance boundary

No production sketch, active v0.6 branch, controller API, finance, QA-owned test or COE source changed. The active v0.6 branch remains `2fbd2475e9f54878c316fa7cea2f228386b0e859`. PR #365 is test-only and does not resolve P0 #177's active poll-before-first-sample race. Host simulation cannot prove that a physical acceptor retains a coin when relay inhibit occurs mid-pulse.

Physical relay polarity, pulse retention, electrical pulse/recovery, 150 power cuts and 30-device/24-hour soak are NOT TESTED. HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO. No coin admission, relay re-enable, finance, replay, witness, downgrade, migration, signer, flash, reset, merge, release or deployment.

## Next exact action

Rerun Full on the docs-synchronized head; obtain terminal Mbed result; request independent QA review and Master role/integration matrix registration. Keep PR #365 DRAFT.
