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


## UTC22 — fixed-span comparator null/empty fail-closed guard (2026-11-26)

**Current source/test commit:** [`659b1e646ba6d3efdbe6e03df4ab4f170a89f0e1`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/659b1e646ba6d3efdbe6e03df4ab4f170a89f0e1)  
**Test commit:** [`2147c9ae46ae862cb355d2da3b4df1787180689e`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/2147c9ae46ae862cb355d2da3b4df1787180689e)  
**PR:** [#348 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/348)

### Defect and bounded correction

The public inline `equal_fixed()` helper dereferenced both input pointers for `n > 0` without validating them, and returned true for a zero-length comparison (including two null pointers). Existing `verify_mac()` and `matches_policy_digest()` call sites validate their own spans, but the helper itself had no safe standalone contract.

- Test commit adds null-left, null-right, both-null, zero-length, equal-byte and unequal-byte assertions.
- Source correction rejects null pointers and `n == 0` before entering the fixed-length XOR-accumulation loop.
- The nonzero-length comparison retains a complete fixed-length pass; no early-exit byte comparison was introduced.
- The synthetic JSON fixture was corrected in commit `2147c9ae` after an initial over-escaped edit; that intermediate fixture was not counted as test evidence.

### Exact local sanitizer evidence

A focused local C++17 micro-harness copied the pre-change helper body and compiled with `g++ 14.2.0 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined`.

- **RED:** pre-change null-left call exited 1 with UBSan “load of null pointer” and ASan SEGV at address 0.
- **GREEN:** post-change helper passed null-left, null-right, both-null, zero-length, equal-byte and unequal-byte checks under ASan/UBSan.

This is a local helper-level reproduction, **not** the complete native header test. The container has the Mbed TLS runtime library but not the development headers, so the full `v060_controller_auth_header_native.cpp` compile was NOT RUN.

### GitHub Actions status and limits

Exact-SHA workflow lookup and combined commit status for `659b1e646ba6d3efdbe6e03df4ab4f170a89f0e1` returned no workflow runs and no status checks. The connected GitHub actions available in this session do not expose workflow dispatch. Therefore no GitHub CI PASS/FAIL is claimed for this increment; the focused workflow remains pending independent execution.

### Safety boundary

This remains an ESP32 lab-only primitive, not application intake. No sketch, CORE response schema, key material, GPIO, relay, coin admission, financial state, signer/witness, migration, release workflow or COE destination changed. PR #348 remains stacked on #254 at `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`, which remains stacked on Phase-A deny #239 at `d83b715b116185107737fef721c2eece8feebf39`. Parallel #283 remains unchanged. Phase-A coin/relay admission remains DENY; physical hardware acceptance remains NOT TESTED.


## UTC22 exact docs-head CI correction

The focused native workflow subsequently ran against the exact final handover head `8bdddfb88630c0c9675f7e4a47ab640f5d17f699` (which contains source/test commit `659b1e646ba6d3efdbe6e03df4ab4f170a89f0e1`).

- Focused [run #45715616078](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45715616078), job `139560779561`: **SUCCESS**.
- Exact-source checkout step verified `git rev-parse HEAD == 8bdddfb88630c0c9675f7e4a47ab640f5d17f699`.
- Runner installed Ubuntu `libmbedtls-dev 2.28.8`, compiled the actual `ControllerAuthV1Lab.h` test with C++17, `-Wall -Wextra -Werror`, ASan and UBSan, and executed the full native header test.
- Output confirms fixed-span null/empty checks, digest rendering, empty-policy denial, empty canonical/signature denial, null parser-span denial, synthetic HMAC tamper/device/nonce rejection, and coin/relay admission remaining DENY; all five existing synthetic auth cases passed.
- Phase-A admission guard step passed.

The separate [Full BlazePwifi run #45715616079](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45715616079) was still pending with no jobs returned at the last observation; no Full aggregate result is claimed. The focused helper is **CI VERIFIED / SIMULATED**, not hardware accepted or production-authoritative.


<!-- PHX-HW-20261126-UTC00-348-TERMINAL:START -->

## 2026-11-26 UTC00 — terminal exact-head CI reconciliation

The exact-head Full workflow has now completed; the earlier “IN PROGRESS” wording above is superseded by the terminal result below.

- PR/docs head before this docs-only reconciliation: `ed17201687d9308de0e0bc4dd10d6da33d4a4733`.
- Source/test: `659b1e646ba6d3efdbe68b71ff0f54edbc09ba9`; native test commit `2147c9ae46ae862cb355d2da3b4df1787180689e`.
- Focused [#45716221522](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45716221522), job `139562835485`: **PASS** at the exact parent/docs head. The actual native header test passed null/empty-span and synthetic authentication checks under C++17, warnings-as-errors, ASan/UBSan; Phase-A admission remained DENY.
- Full [#45716221609](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45716221609): terminal **FAILURE**. The validation job `139563017167` passed; ESP32 job `139563017235` failed at Arduino core 4.0.0 because `mbedtls/sha256.h` is absent for the application sketch. All other 12 firmware target jobs and Android passed; 23 total jobs succeeded, one failed, six production/release-related jobs were skipped.
- The ESP32 provider/PSA decision belongs to MASTER/CORE/RELEASE; this Hardware lab branch did not substitute a different core or add an unapproved provider. Focused status is CI VERIFIED / SIMULATED only; Full status is FAILED; hardware NOT TESTED; production NO-GO.
- No production sketch, CGI producer, shared API, key, relay, coin admission, financial state, signer/witness, migration or COE destination changed. No physical test, flash, reset, signing, merge or deployment occurred.
- Next: obtain the approved ESP32 Mbed TLS 4 provider decision, QA review, then rerun Full at the approved exact head.

<!-- PHX-HW-20261126-UTC00-348-TERMINAL:END -->
