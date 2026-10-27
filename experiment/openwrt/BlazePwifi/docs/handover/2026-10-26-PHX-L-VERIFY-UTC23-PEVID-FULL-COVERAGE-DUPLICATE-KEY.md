# PHX-L-VERIFY UTC23 — Full synthetic PEVID duplicate-key gate audit

**Date:** 2026-10-26 UTC23. **Scope:** QA/build-release evidence validator only; NO CODEX; TEST-ONLY; PRODUCTION NO-GO.

**Source:** `experiment/openwrt/BlazePwifi/tools/v060_physical_evidence_contract.py` at exact Git blob `1dfa4d8efd17c2a96438da10942d5b8dc96bd412` (12,764 bytes; independent local `git hash-object` matched). Literal draft PR #193 parent `fbd59b72608f3bf2393534b24380f7c4b245f43a`, stacked on draft #179; #150/#183 also draft/unmerged. Default main `1719b625173ab33cbf90f0729716e43fce8759ed`; development `1890e522843d262c33a5109dcea11768896c2e5f` comparison-only, not approved Phoenix integration base. Issues #172/#177/#34/#43 reviewed.

**Prior exact-head CI:** Full [#40416636680](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40416636680) **COMPLETED FAILURE**: validate job `121900580341`, two unchanged untrusted-positive-revision and cold-reboot-old-positive-revision REDs on each ESP board. ESP8266/ESP32 compilers and handover PASS. Native [#40416636687](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40416636687) **COMPLETED SUCCESS**. Do not call Full green.

## Actual independent execution

Executed **the unmodified byte-exact Python validator as a subprocess** with 150 disposable **synthetic claimed** power-cut trial records (3 target arches × 5 checkpoint classes × 10), 3 **synthetic claimed** 24h/30-client soak records, 303 unique SHA256-checked **synthetic** capture logs, private /tmp fixture root (0700) and files (0600). No hardware, actual power interruption, payment, or production data. A separate strict JSON parser rejects any repeated member. The fixture generator removes its private directory after the test.

| Case | Exact validator | Strict JSON parser |
| --- | --- | --- |
| Complete synthetic positive | exit 0 STRUCTURE_READY_FOR_INDEPENDENT_REVIEW | ACCEPT |
| Duplicate `fixture_only` false→true | **exit 0** | DUPLICATE_JSON_MEMBER |
| Duplicate trial `receipts_consistent` false→true | **exit 0** | DUPLICATE_JSON_MEMBER |
| Duplicate trial `duplicate_ack_count` 9→0 | **exit 0** | DUPLICATE_JSON_MEMBER |
| Duplicate soak `lost_ack_count` 9→0 | **exit 0** | DUPLICATE_JSON_MEMBER |
| Duplicate `claim_origin` wrong→expected | **exit 0** | DUPLICATE_JSON_MEMBER |
| Reverse `fixture_only` true→false | exit 4 BLOCKED | DUPLICATE_JSON_MEMBER |
| Invalid capture digest | exit 4 BLOCKED | ACCEPT (JSON only) |

**8/8 expectations met, 5/5 contradictory duplicate-member full structural fixtures accepted.** This is stronger than the UTC22 incomplete-manifest microtest: it reproduces acceptance through the actual **full** structural validator. It is NOT evidence that physical power cuts occurred, that the operator's claims are authenticated, or that any production release gate was bypassed. Every accepted result explicitly retains `physical_powercut_verified=false`, `production_release_authorized=false`, and `financial_migration_authorized=false`.

**Reproduction:** run `python test_full_duplicate.py` with the exact source file `v060_physical_evidence_contract.py` beside it. Local evidence ZIP `phx_verify_utc23_full_pevid.zip` SHA256 `34c48a70fd9179c185308df0cebb386e39c93d1be7c220341154917f8664893c`, containing source, generator, log, SHA256SUMS and full report. No fixture/capture files retained.

**Decision/next:** Request MASTER approval for a **test-first** complete-fixture negative suite in `tests/v060_physical_evidence_contract.py`, then a minimal `json.loads(raw, object_pairs_hook=reject_duplicate_members)` correction in `tools/v060_physical_evidence_contract.py` with existing blocked exit 4. Re-run full PEVID suite and exact-head CI; independent source review before guarded integration. No source changes in this docs-only checkpoint. Physical #34, witness #43, paid finance #31/#32, reversible migration, permanent signing and production release remain NO-GO.
