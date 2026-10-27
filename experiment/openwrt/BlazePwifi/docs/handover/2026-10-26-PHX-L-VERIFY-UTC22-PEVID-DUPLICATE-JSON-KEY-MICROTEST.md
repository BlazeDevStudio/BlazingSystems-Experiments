# PHX-L-VERIFY — 2026-10-26 UTC22 — PEVID-0679 duplicate JSON-member preflight

**Scope:** one bounded, source-linked, read-only QA microtest of the physical-evidence structural gate. **NO CODEX. NO PRODUCTION.** No hardware, customer data, firmware, financial transaction, signer, merge or release.

## Exact authority and provenance
- Control plane #172; issues #177/#34/#43 reviewed. Default main `1719b625173ab33cbf90f0729716e43fce8759ed`; development `1890e522843d262c33a5109dcea11768896c2e5f` **comparison only**, not MASTER-approved Phoenix integration.
- QA draft #193 stacked on #179, prior literal HEAD `6eff13c53cdf1ec5bf04b247590da853de109357`. Drafts #179/#193/#150/#183 remain OPEN/UNMERGED. Closed-unmerged #30/#173 not revived.
- Prior literal HEAD `6eff13c53cdf1ec5bf04b247590da853de109357`: Full #40399983796 **COMPLETED FAILURE** (15 success/13 skipped/validate #121842997957 failure: 2 config-auth/cold-reboot RED per ESP board; HND/CI and Arduino compilers PASS); Native #40399983792 **COMPLETED SUCCESS**. Historical docs HEAD `dccfc1a6`: Full #40138138673 SUCCESS and Native #40138138655 SUCCESS; neither overrides latest RED.
- Existing tool: `tools/v060_physical_evidence_contract.py` at development Git blob `1dfa4d8efd17c2a96438da10942d5b8dc96bd412`; existing mock test blob `473cf8a18dece2867f07bacef3739de46592a973`.

## Source-linked executed observation
The structural checker calls `obj = json.loads(raw)` and then validates `set(obj) == REPORT_FIELDS`, schema, fixture flag, claim origin and Git SHA. Python's default `json.loads` silently retains the **last** occurrence of a duplicate JSON member, so the original raw manifest can contain contradictory values not reflected in the resulting object.

Executed disposable Python microtest `physical_manifest_duplicate_keys.py`: **5/5 source-transcribed top-level checks matched**; four deliberately conflicting duplicate-member examples were admitted by the transcribed top-level conditions but rejected by a strict `object_pairs_hook` reference. Cases: `fixture_only`, `claim_origin`, `candidate_git_sha`, and nested `target_arch`. No external packages, private data or network access. Evidence ZIP SHA-256 `d16a543609dd6ee9eb78b9c0211ac585024c61e5fec28afda1e6a9949d9c2c29`.

**Important limit:** The microtest deliberately uses empty `trials`/`soaks`; the **full** 150-trial/3-soak `review()` would reject these fixtures later. We have **not** run the full validator with an otherwise complete duplicate-key manifest, and **have not demonstrated a complete-gate bypass**. This is a parser-level ambiguity and negative-test coverage gap, not evidence that real physical trial data passed, failed or were forged. The structural checker already returns `physical_powercut_verified=false` on a structurally valid fixture.

## Review request / bounded next action
MASTER/QA owner: approve a **test-first** negative fixture for duplicate object members (root and nested) in `tests/v060_physical_evidence_contract.py`, followed by a minimal `json.loads(..., object_pairs_hook=reject_duplicate_keys)` fail-closed correction in `tools/v060_physical_evidence_contract.py` on an isolated branch. Do not change its output to hardware-verified or use it as a release gate substitute. Independently re-run existing PEVID mock cases and exact-head CI after any authorized source change. Preserve prior firmware ACK findings as **already documented** (UTC00/UTC11/UTC13); this run did not rediscover them.

**Production NO-GO:** physical 150 power cuts, 30+ real devices/24h, independent off-device monotonic witness #43, #31/#32 finance durability, reversible migration, permanent signing and #34 electrical coin/relay acceptance remain unverified.
