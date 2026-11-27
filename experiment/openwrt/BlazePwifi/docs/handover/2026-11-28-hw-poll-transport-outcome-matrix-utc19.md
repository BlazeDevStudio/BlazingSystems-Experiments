# PHX-HARDWARE handover — poll transport outcome matrix (UTC19)

- **Repository:** `BlazeDevStudio/BlazingSystems-Experiments`
- **Role:** PHX-HARDWARE
- **PR:** [#365](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/365), OPEN / DRAFT / UNMERGED
- **Branch:** `phoenix/hw-poll-boundary-pulse-matrix-20261128-utc18`
- **Parent:** #364 at `ea765fb822e1c517db4e61c103b86d8eb2c66c92`
- **Source/test SHA:** `fcd5d7df210c8521f9c8fcc1019c8db8bdaf7eb0`
- **Evidence docs head:** `6e5e126199368cbe78f9d46dd6c702c883cfa5cb`

## Completed task

Extended the source-extracted poll-deny harness with five transport outcomes across four independent relay/LED active-level combinations: 20 cases per board, 40 total. Outcomes cover immediate begin failure, empty timeout response, malformed body, server-error body, and a non-empty untrusted `insert=true` body. The harness checks that the pre-poll deny is already effective when `post("poll")` begins, outputs remain OFF throughout the wait and after return, pending pulse/nonce/target evidence is unchanged, and the poll timestamp advances only after return.

Added failure injection that consumes an untrusted positive response and briefly re-enables relay/LED outputs before the final deny. Both ESP8266 and ESP32 reject this transient active-write mutation. Existing six timing windows × four polarity combinations per board remain passing.

## Terminal exact-head evidence

- Focused [#46056036171](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46056036171), job `140698629886`: **PASS**. Logs explicitly show `POLL_TRANSPORT_OUTCOME_PASS outcomes=5 polarity_combinations=4 cases=20` on both boards and transient response-actuation mutation rejection on both.
- Mbed TLS [#46056036039](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46056036039): **3/3 PASS** — source contract `140698947089`, core 3.3.13 `140698947145`, core 4.0.0 `140698946770`.
- Full [#46056036335](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46056036335): controller protocol parity validation job `140698695827` **FAIL**; handover freshness and CI-0701 job `140698630537` PASS; ESP8266 `140698695835`, ESP32 `140698695924`, Android `140698695931`, and all 11 other firmware targets PASS. Downstream simulation/update/signing/publication skipped.
- Earlier docs-head Full #46055555331 also completed with all firmware targets and Android PASS and the same controller parity failure.

## Scope and acceptance boundary

No production sketch, active v0.6 branch, controller API, finance, QA-owned test or COE source changed. Active v0.6 remains `2fbd2475e9f54878c316fa7cea2f228386b0e859`. PR #365 is test-only and does not resolve P0 #177. Host simulation cannot prove physical coin retention when a relay inhibit occurs mid-pulse.

Physical relay polarity, pulse retention, electrical pulse/recovery, 150 power cuts and 30-device/24-hour soak are NOT TESTED. HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO. No coin admission, relay re-enable, finance, replay, witness, downgrade, migration, signer, flash, reset, merge, release or deployment.

## Next exact action

Master register #365 in role/integration matrices; CORE publish the authenticated controller register/poll/receipt/disposition contract; QA independently review the exact source/test SHA and controller parity; Hardware keep intake denied until the approved contract and physical electrical review exist.
