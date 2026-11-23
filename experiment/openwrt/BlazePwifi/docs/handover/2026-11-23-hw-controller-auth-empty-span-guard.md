# PHX-HARDWARE — ControllerAuthV1Lab empty-span boundary guard

**Date:** 2026-11-23 UTC15  
**Role:** PHX-HARDWARE  
**Task:** #254 child hardening  
**PR:** [#348 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/348)  
**Branch:** `phoenix/hw-controller-auth-nonempty-spans-20261123-utc15`  
**Base:** PR #254 exact head `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9` (which remains stacked on Phase-A deny #239 at `d83b715b116185107737fef721c2eece8feebf39`)

## Finding

The non-actuating lab helper accepted a zero-length raw policy span when supplied with SHA-256(empty), and accepted a zero-length canonical message when supplied with HMAC(key, empty). The current caller contract requires a strict, nonempty JSON policy and a domain/action-bound canonical message, so empty spans cannot be valid inputs.

## Test-first change

The first child commit `0a0c36b648e04ccf1ca17b6860f31a3fcfa1e917` changed only `tests/v060_controller_auth_header_native.cpp` and added:
- a known SHA-256(empty) vector which must not authorize an empty policy span;
- a synthetic HMAC(key, empty) vector which must not authorize an empty canonical span.

The initial focused workflow was not observed to start at that test-only head; no RED CI result is claimed.

## Source correction

The follow-up source commit `21d075e366e1a6fab54985a14996e2d30a7cc862` adds explicit `len == 0` rejection to `matches_policy_digest()` and `canonical_len == 0` rejection to `verify_mac()`.

No canonical serialization, HMAC format, parser ownership, Mbed TLS provider selection, application intake, GPIO, relay, coin admission, CORE contract, finance, signer, witness, migration, workflow or release behavior changed. Phase-A coin/relay admission remains DENY.

## Validation

Focused native header workflow is expected from the PR path filter. Exact-head status must be read back before claiming PASS/FAIL. The host tests are synthetic and do not prove target hardware or protected freshness.

## Safety / next action

Keep #348 OPEN/DRAFT/UNMERGED and #254/#239 unchanged. PHX-QA should review the new empty-span cases and verify they do not duplicate CORE parser responsibilities. PHX-RELEASE still owns the Mbed TLS 4 toolchain/provider decision. No flashing, real money, signer provisioning, migration, release, merge or deployment.
