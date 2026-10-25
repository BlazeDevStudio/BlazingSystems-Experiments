# PHX-L-VERIFY UTC07 — ESP build toolchain provenance audit (2026-10-25 UTC)

**Classification:** VERIFIED BUILD REPRODUCIBILITY GAP / FIRMWARE SECURITY RED / PRODUCTION NO-GO. **Scope:** read-only, source-and-log-linked QA; no firmware change, flash, signing, keys, payments, merge or release. NO CODEX.

## Exact provenance

- Repo: `BlazingSystems/BlazingSystems-Experiments`; `main@9596fc6a9f8a6a42bc252019c24ca1f38d96dd7a`; comparison-only development `blazepwifi-v0.6.0-audit-foundation@ad662ddfffd483864daaf5bca3f16368877a2113`. Neither is an authorized integration destination.
- QA stacked draft PR #193 literal source/docs pre-audit HEAD `07d6c4a8cb2e0aacc869cf365d52aa6f8d36d866`, parent unmerged draft PR #179 `e5a9781ea5234b09501d5356cf966f9237ac8172`. PRs #150/#183 separate draft unmerged.
- Actual workflow `.github/workflows/blazepwifi-build.yml` Git blob `47d91f60469e512940a8d0f438718c9f5c7ac097`, inspected ESP8266 lines 396–417 and ESP32 lines 442–463.
- Full #40170853939, synthetic PR checkout `c1eb77ae190f3804280d006403433fca6ea03650`: **COMPLETED FAILURE, 15 successful / 1 validation failure / 13 skipped**. Validate job `121102109187`: real-source C++ GPIO/config regression **13 PASS + 2 security RED per board** (`untrusted_positive_revision_cannot_enable_coin`, `cold_reboot_older_positive_revision_cannot_enable_coin`). Both ESP Arduino compiler jobs **SUCCESS**. Native #40170853896 synthetic-native **SUCCESS**.
- ESP8266 compiler job `121102109261` installed `esp8266:esp8266@3.1.2` according to log, FQBN `esp8266:esp8266:nodemcuv2`.
- ESP32 compiler job `121102109190` installed `esp32:esp32@3.3.12` according to log, FQBN `esp32:esp32:esp32`.
- The logs record `arduino/setup-arduino-cli@v2` resolved to action SHA `81d310742121c928ea9c8bbd407b4217b432ae02` **for this run only**, with setup version selector `1.x`. Do not assume the same action/tool binary in a future run.

## Executed audit and observed gaps

A deterministic source/log audit inspected both real workflow job blocks and both exact-run compiler logs. **14/14 asserted evidence matches** (six workflow/log invariants plus observed core-version match per board). This is an *audit execution*, not 14 passing firmware functional tests.

| Check | ESP8266 | ESP32 | Consequence |
|---|---|---|---|
| `runs-on: ubuntu-latest` | Present | Present | Moving runner image |
| `arduino/setup-arduino-cli@v2` | Present | Present | Moving action tag; exact resolved SHA known only for this run |
| `arduino-cli core update-index` | Present | Present | Fetches mutable board index |
| `arduino-cli core install esp8266:esp8266` / `esp32:esp32` **without `@version`** | Present | Present | Future run may install different core |
| Build-generated `SHA256SUMS` from local `dist` tree | Present | Present | Verifies packaged outputs, **not** external toolchain identity |
| Exact job logs and PR synthetic checkout cross-checked | PASS | PASS | Audit is linked to observed build |
| Observed core version | 3.1.2 | 3.3.12 | Observations, **not source pins** |
| Explicit `arduino-cli version` / `arduino-cli core list` inventory in ESP jobs | Absent | Absent | Exact CLI version and full dependency graph not recorded as release evidence |

Both FQBNs are explicit and both builds succeeded; this does **not** prove byte-for-byte reproducibility. The prior independently downloaded ZIP audit **62/62 PASS** proves those archive bytes, SHA256SUMS entries and bundled Git-source matches for that run, not a deterministic rebuild or a trusted production signature.

## Recommended bounded MASTER review (no source changes authorized by this report)

1. Decide whether to pin runner image, action SHA, exact Arduino CLI version and checksum, ESP8266 core 3.1.2 and ESP32 core 3.3.12 **after compatibility review**, and board package-index snapshots or resolved tool digests. These observed versions are candidate pins, not a safety endorsement.
2. Add read-only build-provenance inventory: literal PR head, synthetic checkout SHA, action/runner identity, `arduino-cli version`, `core list`, FQBN, compiler/linker versions and hashes, flags, board-index/tool digests, sketch/library Git blobs, and output hashes.
3. Test two isolated clean builds with identical pinned inputs, compare binaries byte-for-byte, and explicitly document any nondeterministic fields. Retain ZIP CRC/manifest/tamper checks as independent package integrity tests.
4. Keep firmware configuration-authentication/reboot-highwater source RED unresolved pending MASTER/CORE signed receipt and independent witness contract. Do not turn this provenance report into permission to merge, flash or release.

**Unverified hard gates:** physical coin acceptor/relay electrical behavior and edge sampling; 150 power cuts; 30-device 24-hour soak; independent monotonic witness #43; reversible migration; paid-finance #31/#32; hardware #34; permanent signing; production approval. **PRODUCTION NO-GO.**
