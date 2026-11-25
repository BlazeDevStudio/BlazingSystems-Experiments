# PHX-HARDWARE UTC08 — current CGI register/poll envelope deny regression

**Role:** PHX-HARDWARE  
**Tasks:** #172 / #177 / #349  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**PR:** [#349 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Parent:** #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Status at handover creation:** source/test change committed; exact-head CI pending; HARDWARE NOT TESTED; PRODUCTION NO-GO.

## Source audit

The live default-branch CGI source was read at blob `2e3a1430d08cc6606429a042df3b5848f53c7267`:

`experiment/openwrt/BlazePwifi/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo`

- `register|ping` returns `ok`, `server_time`, and `controller`; it does not return `response_sig`.
- `poll` returns `ok`, `insert`, `target_nonce`, `expires`, and `controller`; it does not return `response_sig`.
- `member_snapshot` returns `response_sig`, but its signature domain is `member_snapshot` over member revision and payload hash. It is not a register/poll authorization envelope.
- Both Hardware sketches on the #347/#349 stack retain deny-only `acceptPollResponse()`: it clears stale local permission and returns false.

This is the concrete producer/consumer mismatch behind the inherited Full validation assertion. Hardware must not invent a positive signature or reinterpret the member snapshot signature.

## Change

- Added `poll_current_cgi_envelope_deny_lab.py`, a source audit plus C++17 host regression for the exact current register, poll and member-snapshot response shapes.
- Integrated it into `poll_response_failclosed_lab.py`; the existing runner remains below its 350-line structural limit.
- Added the CGI source and new lab to the Relay workflow push and pull-request path filters.
- No production sketch, API, GPIO, relay, coin, finance, signer, witness or migration behavior changed.

## Validation plan

The exact-source runner compiles the production `acceptPollResponse()`, `coinIngressConfigurationAllows()`, and `applyOutputs()` functions for ESP8266 and ESP32. It requires all three current CGI payload shapes to remain denied, stale target state to be cleared, outputs to remain OFF, and remote configuration to remain untouched.

Focused Relay CI and Full integration are pending at this handover's source/test commit. Local test execution was not performed. All host checks are SIMULATED, not physical acceptance.

## Coordination

PHX-CORE must publish the approved versioned register/poll response envelope and canonical golden vectors. PHX-QA owns reconciliation of the inherited assertion against that approved contract. PHX-MASTER owns the assignment/matrix pins. Hardware remains deny-only until those dependencies are approved.

No merge, force-push, flash, reset, live money, migration, signer provisioning, release, or deployment.
