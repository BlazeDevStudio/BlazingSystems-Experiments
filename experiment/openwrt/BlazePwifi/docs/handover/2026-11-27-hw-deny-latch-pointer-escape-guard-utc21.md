# PHX-HARDWARE UTC21 — deny-latch pointer/reference escape guard

## PHX-HARDWARE UTC21 — deny-latch pointer/reference escape guard

**Recorded:** 2026-11-27T21:33:50Z  
**PR:** [#367 — Prove deny-only latch cannot be re-enabled outside startup](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/367)  
**Branch:** \`phoenix/hw-deny-latch-monotonicity-20261127-utc21\`  
**Source/test head:** \`32644d14ed8c69f682f3f4739880e18f9a4e4495\`  
**Logic/test commit:** \`c97f6460b9340c009ee680e4d42c7103ba05d290\`  
**Parent:** \`3f1f7424efe6285f023aee1e0e0a385e5aec2c4b\`

### Scope and actual change

The existing deny-latch contract scanned direct assignments to controller, coin, relay, LED, insert-mode and active-target fields, but did not reject address/reference escapes that could bypass that direct-assignment scan.

Extended \`poll_preflight_inhibit_lab_contract.py\` to reject:
- direct address-of escapes (for example \`&coinEnabled\`);
- non-const reference aliases;
- \`std::ref\`, \`std::cref\` and \`std::addressof\` wrappers.

Extended the per-board mutation suite with four injected escape cases per board (8 total), plus comment/string decoy checks. No ESP8266/ESP32 production sketch, shared CORE API, QA-owned assertion, finance, signer, witness, migration or release setting changed.

### Validation

- Isolated local regex smoke check: PASS for pointer, reference, \`std::ref\`, \`std::addressof\`, and comment/string decoys.
- Repository Python lab: NOT RUN; the runtime could not resolve github.com for a checkout.
- GitHub Actions at current source/test head \`32644d14...\`: NOT RUN. The GitHub connection updated the ref, but no new workflow run appeared for the new SHA; the available GitHub actions expose run reads/retries but no workflow-dispatch action. Earlier runs at \`3f1f7424...\` are not transferable to this head.
- Previous exact-head evidence remains historical: focused #46069674062 PASS; Mbed TLS #46069674071 PASS 3/3; Full #46069674142 FAIL at QA-owned controller parity. None validates this new source head.

### Status and boundaries

Source-contract change committed; local regex smoke SIMULATED only; CI VERIFIED at this SHA = NO; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

Keep coin and relay admission denied. The source scan is still syntactic and does not prove safety against arbitrary casts, memory corruption or hardware faults. CORE authenticated register/poll and receipt/disposition contract, QA parity, physical acceptance, protected witness, durable accounting/replay and v1-to-v2 migration remain external blockers.

Private \`BLAZE_PROJECT_REGISTRY_v11_20261027.json\` remains NOT RECOVERED; no substitute registry was promoted.
