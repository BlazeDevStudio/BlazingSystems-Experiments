# PHX-L-VERIFY UTC08 — ESP SHA256SUMS co-tamper authority boundary (test-only)

- **UTC:** 2026-10-25T08Z; **role:** PHX-L-VERIFY; **protocol:** BLAZE-COMMS/1; **status:** EXECUTED / REVIEW_REQUIRED / PRODUCTION NO-GO.
- **Repository:** BlazingSystems/BlazingSystems-Experiments; QA child DRAFT PR #193 stacked on unmerged #179; #150/#183 separate unmerged. Before audit, literal QA HEAD `344aa907c6dffe0f559d28d288619fbf2e1578cf`. Default `main@9596fc6a9f8a6a42bc252019c24ca1f38d96dd7a`, comparison-only development `blazepwifi-v0.6.0-audit-foundation@ad662ddfffd483864daaf5bca3f16368877a2113`; neither is an authorized merge destination.
- **Source basis:** `.github/workflows/blazepwifi-build.yml` Git blob `47d91f60469e512940a8d0f438718c9f5c7ac097`; ESP8266 and ESP32 jobs both generate their own `SHA256SUMS` using the literal GNU command below, in the same output tree as the binaries. Unlike independent signed provenance, this is a self-generated checksum list.
```sh
find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
```

## New independent executed fault-injection fixture

Used disposable `tempfile.TemporaryDirectory` toy bytes, **not real firmware**. Ran the literal GNU manifest generation command and `sha256sum -c SHA256SUMS` for each board-labelled fixture. **18/18 assertions PASS** (9 each): initial manifest creation and verification; single payload modification detected against old manifest; regenerate checksum after modification; co-modified payload+manifest passes `sha256sum -c`; an independent original SHA256 still detects modification; newly added unapproved member can be included in regenerated manifest and passes verification. No hardware, network adversary, actual ESP binary tampering or signing occurred.

**Evidence files (local conversation artifacts, not committed source):** `phx_verify_utc08_manifest_authority.py` SHA256 `73a6315116f808ff5d480d6b94f2bc172071933eb94bf1ce19a754a33efbe47f`; `phx_verify_utc08_manifest_authority.json` SHA256 `2141cde81dc1baa25999ced5c7d116c285ca93b1f4e38554f9e0b882960e5a37`. The previous independent actual-archive 62/62 audit remains valid for byte integrity of that archive; it does **not** confer trusted build authority. This new experiment tests the trust boundary, not an actual malicious GitHub run.

## Exact-head CI reconciliation

At prior documentation HEAD `344aa907c6dffe0f559d28d288619fbf2e1578cf`, [Full #40174476237](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40174476237) **COMPLETED FAILURE** (15 success, 1 validation failure, 13 skipped); validate job `121112255700` completed handover and actual-source C++ test, preserving **13 PASS / 2 config-auth and cold-reboot RED per ESP board**. ESP8266 job `121112255689` SUCCESS and ESP32 `121112255742` SUCCESS; [Native #40174476223](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40174476223) SUCCESS. Source-security REDs remain unresolved; a compiled binary and matching self-checksums cannot override validation failure.

## MASTER review request / next exact action

Require a separately trusted, immutable or signed provenance statement binding **literal source Git SHA, PR synthetic-merge SHA, exact toolchain/board packages, expected artifact filenames, artifact SHA256 and job/run identity**. Then verify full artifact bytes against that independently controlled statement and compare at least two isolated clean builds after pinning toolchain inputs. A signature is useful only if its key and provenance issuance are independently controlled. Do **not** silently revive owner-closed PR #173, weaken handover gates, change ESP source/financial authority, or publish a release. This is a proposal, not a deployed control.

**Hard gates:** #43 independent off-device monotonic witness; #34 real relay/coin pulse and 150 abrupt physical power cuts plus 30-device 24h soak; #31/#32 paid finance, reversible migration, permanent signing, signed config receipts and ACKP1. All remain NOT VERIFIED / PRODUCTION NO-GO. No Codex, customer data, firmware flashing, payment, merge or release.

**Next:** MASTER review this provenance contract; if authorized, add *test-first* negative CI policy checks on isolated draft PR #193, pin toolchain inputs and independently verify two clean-build artifacts without altering production release logic.
