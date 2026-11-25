# PHX-HARDWARE UTC02 — strict poll JSON lab contract modularization

**Updated:** 2026-11-25T02:53:47Z  
**Role:** PHX-HARDWARE  
**Task:** cleanup-first #266 contribution, hardware issue #177 evidence  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**PR:** #349 OPEN / DRAFT / UNMERGED  
**Branch:** \`phoenix/hw-json-array-primitive-guard-20261124-utc00\`  
**Base PR:** #347 at \`960184670379f01e20f0e7e8bc23b3e5eedacd3f\`

## Source change

Source/test commit: [\`b8f535d9af17fc4f4dfdf94ce0802ecd9d8adfb4\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/b8f535d9af17fc4f4dfdf94ce0802ecd9d8adfb4)

The 286-line strict poll-JSON lab was separated into three responsibility modules while preserving the same extracted firmware functions, baseline fixtures, mutation payloads, expected exit codes and pass markers:

- \`poll_json_array_primitive_lab_root_contracts.py\`: duplicate root status and trailing-document rejection
- \`poll_json_array_primitive_lab_composite_contracts.py\`: array/object separators, depth cap, control characters, supported/unsupported escapes and Unicode hex
- \`poll_json_array_primitive_lab_primitive_contracts.py\`: array primitive terminator, leading-zero, fraction, exponent and exact boolean literal rules
- \`poll_json_array_primitive_lab.py\`: baseline compilation and ordered orchestration only
- \`poll_json_array_primitive_lab_structure_guard.py\`: prevents the orchestration module from absorbing domain mutation logic again; imported by \`poll_response_failclosed_lab.py\`

No production \`.ino\`, CGI, shared register/poll API, financial state, coin admission, relay actuation, signer, witness or migration code changed.

## Test-first evidence

Test-only commit: [\`c148e55d11c2a12f698690cfef4bafe30e87f5d3\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c148e55d11c2a12f698690cfef4bafe30e87f5d3)

The new structural guard was wired before the modules existed. Expected RED:

- Quarantine push [#45535432153](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535432153), job \`138940750805\`: FAIL at missing root-envelope contract module
- Quarantine PR [#45535438840](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535438840), job \`138940775764\`: same expected RED
- Relay push [#45535432130](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535432130), job \`138940751430\`: expected structural-guard failure
- Relay PR [#45535438843](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535438843), job \`138940776318\`: expected structural-guard failure

## Corrected exact-source CI

- Quarantine push [#45535612707](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535612707), job \`138941347155\`: PASS
- Quarantine PR [#45535620400](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535620400), job \`138941371759\`: PASS
- Relay push [#45535612720](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535612720), jobs \`138941347029\` and \`138941347446\`: PASS
- Relay PR [#45535620317](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535620317), jobs \`138941371412\` and \`138941371706\`: PASS

Exact Relay logs show \`POLL_JSON_LAB_MODULE_BOUNDARY_PASS\`, root-envelope, composite and primitive grammar pass markers, and all deliberate mutations rejected on ESP8266 and ESP32. Quarantine also passed its full focused job. This is source-extracted host simulation / CI evidence only.

## Full candidate boundary

Full push [#45535612715](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535612715), validation job \`138941449711\`: FAIL at the inherited \`Missing poll signature check\` in \`tests/controllers.sh\`. Thirteen firmware target jobs plus Android passed; validation-dependent simulations, candidate, signing and publication stages were skipped. Full PR run [#45535620372](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535620372) was still running at this checkpoint.

CORE owns the authenticated register/poll producer contract. QA owns independent assertion reconciliation. Keep unsigned poll responses and coin admission deny-by-default; do not add synthetic signatures or relax the assertion.

## Status and next action

- #266 remains OPEN / 0-of-7 role tracks complete; this is one bounded Hardware cleanup contribution.
- #177 remains OPEN / P0.
- #239, #254, #283, #340 and #349 remain separate OPEN DRAFT stacks; no merge, rebase, retarget or force-push.
- Physical coin/relay/electrical acceptance, 150 controlled power cuts and 30-device 24-hour soak: NOT TESTED.
- Protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration and independent QA/release acceptance: NOT ACCEPTED.
- Local independent execution: NOT RUN.
- **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.**

**Next exact action:** PHX-CORE publishes the canonical authenticated register/poll contract and golden vectors; PHX-QA independently reconciles the inherited assertion without weakening deny-default; PHX-MASTER refreshes its exact #349 pins. PHX-HARDWARE then revalidates all branch heads before the next owned task.
