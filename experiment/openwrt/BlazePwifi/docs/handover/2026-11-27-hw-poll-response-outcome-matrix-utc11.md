# PHX-HARDWARE — Poll response outcome matrix (UTC11)

**Date:** 2026-11-27  
**Role:** PHX-HARDWARE  
**Task:** P0 #177 / deny-only poll preflight regression coverage  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-poll-response-outcome-matrix-20261127-utc11`  
**Parent:** DRAFT PR #355 at `9f7a8ecb915cf199a82c0b4d37c56c40d722037b`  
**Parent base:** PR #354 at `fc842342596786e072630179acfbbc4feeb2ba02`  
**Active v0.6 comparison baseline:** `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`

## Scope and reason

The current deny-only candidate explicitly discards `post("poll")` responses and disables coin/relay/LED state before and after the synchronous request. The source-extracted host harness previously returned only an empty string from its `post()` stub. That covered the transport-failure/empty-response path but did not exercise a success-like positive body or detect a transient output enable between response handling and the post-poll deny.

This child adds that missing negative-only outcome coverage. It does not change firmware, shared APIs, coin admission, relay policy, pending disposition, finance, or migration.

## Exact code changes

1. `poll_preflight_inhibit_lab_harness.py`
   - The deterministic `post()` stub returns an injected response body.
   - The host output model records any relay or LED logical ON write after the initial energized precondition is reset.
   - The harness rejects transient ON writes even if a later post-poll deny turns the outputs OFF again.

2. `poll_preflight_inhibit_lab_cases.py`
   - Runs both an empty response (transport/HTTP failure representation) and an untrusted positive response body.
   - Injects a response consumer that briefly enables relay/LED before the post-poll deny; the harness must reject it.

## Commits

- `96b838da3c5ef8b3f43c1dc05988486be4790101` — first response-outcome harness change
- `285d508852bdd806597f8e99b37a566d01641696` — positive-response consumer failure injection
- `5aa139f57538e045d8656530ed4c59abcebbe9cd` — response-body fixture substitution

## Evidence status

- GitHub Actions: **NOT RUN at handover creation**; exact-head PR workflows are required before claiming CI verification.
- Local board hardware: **NOT TESTED**.
- Coin pulse/relay electrical acceptance: **NOT TESTED**.
- Power-cut / LittleFS durability / 150-cycle / 30-device soak: **NOT TESTED**.
- This remains source-extracted host simulation only. No physical test or hardware acceptance is claimed.

## Safety and ownership

- No production sketch changed.
- No positive poll response is accepted.
- No automatic coin POST, retry, or pending clear was added.
- No CORE/QA/Master-owned file or shared contract was changed.
- Parent #355 and its #354 base remain OPEN / DRAFT / UNMERGED; no rebase, retarget, force-push, or merge was performed.
- Keep coin, relay, financial, replay, witness, and downgrade behavior fail-closed.

## Next exact action

Run the focused Active v0.6 Poll Intake Deny workflow on the exact PR head. If it passes, request independent QA review of the new outcome/mutation matrix. Full integration remains subject to CORE's authenticated register/poll and receipt/disposition contract and QA's semantic assertion reconciliation.
