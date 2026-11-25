# PHX-HARDWARE handover — isolate UTF-16 surrogate mutation cases

**Updated:** 2026-11-25T08:16:00Z  
**Role:** PHX-HARDWARE  
**Repository:** \`BlazeDevStudio/BlazingSystems-Experiments\`  
**Control plane:** [#172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)  
**Hardware task:** [#177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Cleanup gate:** [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
**PR:** [#349](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349) — OPEN / DRAFT / UNMERGED  
**Branch:** \`phoenix/hw-json-array-primitive-guard-20261124-utc00\`  
**Base:** PR #347 at \`960184670379f01e20f0e7e8bc23b3e5eedacd3f\`

## Scoped task

Correct the UTF-16 surrogate mutation harness failure in the strict poll-JSON parser lab. This is a test-fixture isolation correction, not a production parser change.

**Starting branch head:** \`84607f15a0b5df6125a0211a7df6efc522bff112\`  
**Source/test head:** \`059e3bbde935a86de0fa0e31e06d1ebb36755c4f\`

## Observed RED and root cause

At the starting head, the exact-source Quarantine and Relay workflows failed inside \`verify_utf8_contracts()\`:

- Quarantine [#45572069779](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45572069779), job \`139060882998\`.
- Relay [#45572069774](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45572069774), job \`139060883498\`.

The high-surrogate mutation expected exit 151 but got 134. The mutation intentionally bypassed the high-surrogate branch, but its fixture reused the full UTF-8 baseline. That baseline checks a valid high/low surrogate pair first; after the mutation, the parser left the low surrogate unconsumed and rejected the valid pair at exit 134 before reaching the intended isolated-high-surrogate case. This was a test-harness ordering/fixture-isolation defect, not evidence that the production parser accepted an invalid surrogate.

## Changes

1. Commit [\`85751fde\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/85751fdec2dcb7823410d98b4dd63c29475ec5d4) adds dedicated \`UNPAIRED_HIGH_SURROGATE_MAIN\` and \`ISOLATED_LOW_SURROGATE_MAIN\` fixtures.
2. Commit [\`059e3bbd\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/059e3bbde935a86de0fa0e31e06d1ebb36755c4f) changes the UTF-8 mutation contracts to run each mutation against only its targeted invalid surrogate.
3. The full UTF-8 baseline remains intact and continues to test valid scalar pairs plus malformed raw UTF-8 and invalid escaped surrogates.

Only these two host-lab files changed in this increment:

- \`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_json_array_primitive_lab_fixtures.py\`
- \`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_json_array_primitive_lab_utf8_contracts.py\`

No production \`.ino\`, parser function, GPIO/ISR, relay behavior, CGI producer, shared API, financial state, signer, witness or migration changed.

## Exact-source CI evidence

- Quarantine [#45574159279](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45574159279), job \`139067820225\`: **PASS**.
  - ESP8266 and ESP32 UTF-8 baseline: valid 5/5, invalid 13/13.
  - Both boards reject the targeted unpaired-high mutation at expected exit 151.
  - Both boards reject the isolated-low mutation at expected exit 152.
  - UTF-8 mutation set: 6/6 rejected per board.
  - Quarantine source-extracted scenarios: 72/72 PASS.
- Relay [#45574159323](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45574159323): **PASS**.
  - Jobs \`139067820615\` and \`139067820793\`.
  - Both boards pass the same targeted surrogate mutation checks and bounded HTTP response guards.
- Full BlazePwifi [#45574159334](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45574159334): **FAILED at inherited integration gate**.
  - Thirteen firmware/platform build jobs plus Android: 14/14 PASS.
  - Validation job \`139067864908\` fails at Controller protocol parity: \`Missing poll signature check\` in the ESP8266 sketch.
  - Downstream simulations, update, signing and publication stages skipped. This is not a Hardware-owned signature contract and was not weakened.

## Evidence classification and safety

- **Test-fixture correction:** CI VERIFIED at exact source/test SHA \`059e3bbde935a86de0fa0e31e06d1ebb36755c4f\`.
- **Parser behavior:** source-extracted host simulation only.
- **Physical coin acceptor / relay / power-cut acceptance:** NOT TESTED.
- **HARDWARE ACCEPTED:** NO.
- **PRODUCTION READY:** NO.

The workflows explicitly retain \`SIMULATED_ONLY=1\`, \`PHYSICAL_COIN_PULSE_ACCEPTANCE=0\`, \`PHYSICAL_RELAY_ACCEPTANCE=0\`, and \`PHYSICAL_POWER_CUT_ACCEPTANCE=0\`.

## Blockers and next action

- PHX-CORE must publish the approved authenticated register/poll producer contract and canonical vectors.
- PHX-QA must independently reconcile the Full validation assertion without relaxing deny-default.
- PHX-MASTER must refresh the current #349 owner/source pins and maintain the stacked-PR ancestry.
- PHX-HARDWARE's next activation must revalidate all live heads and choose one new unblocked Hardware-owned task. Do not repeat this fixture correction.

No merge, rebase, force-push, physical flashing, device reset, production migration, live-money test, signer provisioning, release tag or deployment occurred.
