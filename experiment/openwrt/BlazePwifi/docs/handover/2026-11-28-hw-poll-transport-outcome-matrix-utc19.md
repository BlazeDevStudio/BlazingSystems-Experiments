# PHX-HARDWARE handover — poll transport outcome matrix (UTC19)

- **Repository:** `BlazeDevStudio/BlazingSystems-Experiments`
- **Role:** PHX-HARDWARE
- **PR:** [#365](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/365), OPEN / DRAFT / UNMERGED
- **Branch:** `phoenix/hw-poll-boundary-pulse-matrix-20261128-utc18`
- **Parent:** #364 at `ea765fb822e1c517db4e61c103b86d8eb2c66c92`
- **Source/test SHA:** `fcd5d7df210c8521f9c8fcc1019c8db8bdaf7eb0`
- **Final docs/CI head:** `0e5b838cfc7db86c2ce9aaf25b1cabe9e5b2ad73`
- **Docs-first commit:** `71ea4c332227b58b6bc51a58908bc855bfadc0a8`

## Completed task

Extended the source-extracted poll-deny harness with five transport outcomes across four independent relay/LED active-level combinations: 20 cases per board, 40 total. Outcomes cover immediate begin failure, empty timeout response, malformed body, server-error body, and a non-empty untrusted `insert=true` body. The harness checks that the pre-poll deny is already effective when `post("poll")` begins, outputs remain OFF throughout the wait and after return, pending pulse/nonce/target evidence is unchanged, and the poll timestamp advances only after return.

Added failure injection that consumes an untrusted positive response and briefly re-enables relay/LED outputs before the final deny. Both ESP8266 and ESP32 reject this transient active-write mutation. Existing six timing windows × four polarity combinations per board remain passing.

## Exact CI evidence

- Focused source/test run [#46055268572](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46055268572), job `140696113739`: PASS at source/test SHA `fcd5d7df210c8521f9c8fcc1019c8db8bdaf7eb0`.
- Focused docs-head run [#46055555335](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46055555335), job `140697053907`: PASS at docs head `0e5b838cfc7db86c2ce9aaf25b1cabe9e5b2ad73`.
- Mbed TLS run [#46055268521](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46055268521): 3/3 PASS — source contract `140696739516`, core 3.3.13 `140696740005`, core 4.0.0 `140696740049`.
- Docs-head Mbed [#46055555322](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46055555322) was still running; no result claimed.
- Full docs-head [#46055555331](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46055555331): controller protocol parity FAIL at validation job `140697234100`; handover freshness and CI-0701 job `140697154250` PASS; ESP8266 `140697234058`, ESP32 `140697233967`, Android `140697234021`, and all 11 other firmware targets PASS. Downstream simulation, update, signing and publication skipped.
- Earlier Full runs #46055268629/#46055260220 failed handover freshness before this docs sync and are superseded. Prior exact-stack Full #46052478996 identified `tests/controllers.sh:21` / `config_revision` as the controller parity mismatch.

## Scope and acceptance boundary

No production sketch, active v0.6 branch, controller API, finance, QA-owned test, or COE source changed. Active v0.6 remains `2fbd2475e9f54878c316fa7cea2f228386b0e859`. PR #365 is test-only and does not resolve P0 #177. Host simulation cannot prove physical coin retention when a relay inhibit occurs mid-pulse.

Physical relay polarity, pulse retention, electrical pulse/recovery, 150 power cuts and 30-device/24-hour soak are NOT TESTED. HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO. No coin admission, relay re-enable, finance, replay, witness, downgrade, migration, signer, flash, reset, merge, release or deployment.

## Next exact action

Master register #365 in the role/integration matrix; CORE publish the authenticated controller register/poll/receipt/disposition contract; QA independently review the exact source/test SHA and controller parity; Hardware keep intake denied until the approved contract and physical electrical review exist.
