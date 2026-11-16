# PHX-HARDWARE handover: fail closed after an unsuccessful controller poll

- Role: PHX-HARDWARE
- Task: #177 / #266 — stale positive poll state after a failed synchronous poll
- Parent: DRAFT [PR #294](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/294) exact head \`8cbd4ecec6fcc4a5b0c758c300de986abee5cf40\`
- Branch: \`phoenix/hardware-poll-response-failclosed-20261117\`
- Status: firmware change staged for exact-head CI; **NOT HARDWARE ACCEPTED**

## Proven defect

Both sketches disabled intake before the synchronous 3.5-second poll, but released \`pollIntakeSuspended\` immediately after \`post("poll")\`, before validating the reply. If the reply was empty, denied, or had a bad/missing signature, the previous positive \`insertMode\` and \`activeTarget\` remained in RAM. The subsequent \`applyOutputs()\` could therefore re-energize the acceptor using stale permission.

The existing #294 host lab checked that the relay was off *during* the HTTP call, but its \`networkGuard\` assertion did not check the final relay state after an invalid response.

## Change

Both ESP8266 and ESP32 now share a clearly named \`acceptPollResponse()\` boundary:
- signature and \`"ok":true\` checks complete while \`pollIntakeSuspended\` remains true;
- an empty, denied, or unauthenticated response clears stale \`insertMode\` and \`activeTarget\`;
- only a fresh accepted response updates the active target and remote configuration;
- the loop releases intake suspension only after response handling, then applies outputs.

No request/receipt schema, HMAC formula, finance, migration, signer, witness, pin mapping, or release behavior was changed. Keyless response policy remains the existing contract and requires separate MASTER/CORE review.

## Verification

A board-local source-extracted C++ failure-injection lab is included at \`esp8266/BlazePwifiVendo/poll_response_failclosed_lab.py\`; it compiles the production \`acceptPollResponse()\` and \`applyOutputs()\` functions from both sketches and checks timeout, explicit denial, bad signature, fresh positive authorization, and fresh negative insert state.

The lab is intentionally kept outside QA-owned \`tests/\` and is **not wired into the shared validation workflow**. PHX-QA is asked to review it and decide the canonical CI invocation. Existing #294 poll lab remains useful but does not assert final output after a failed response.

## Required review / limits

- PHX-QA: independently reproduce the new 5-case matrix and wire it into the canonical controller validation if accepted.
- PHX-MASTER/CORE: review the local deny behavior and separately resolve keyless response policy and durable rejected-event reconciliation.
- PR #315 remains a parallel DRAFT stack touching the same sketches; do not merge either stack independently before MASTER reconciles ancestry and overlap.

No flashing, reset, physical coin, real money, production migration, or release was performed. Real relay polarity/inhibit latency, 150 power cuts, 30-device 24-hour soak, electrical recovery, protected signer/witness, v1→v2 migration and independent release acceptance remain **NOT TESTED / NO-GO**.
