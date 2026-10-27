# PHX-L-VERIFY — 2026-10-27 UTC00 — PEVID storage_source canonical path audit

**Status:** independently reproduced with actual unmodified validator; SOURCE UNCHANGED; MASTER review requested. **Priority P2** conditional evidence-integrity metadata gap, not a hardware/financial defect. Production NO-GO.

## Authority and CI
- Main `1719b625173ab33cbf90f0729716e43fce8759ed`; development `1890e522843d262c33a5109dcea11768896c2e5f` comparison-only, not authorized integration base.
- Draft #193 previous literal HEAD `c5877bc944c07ba432c0806fdb405243ff111918` stacked on #179 `e5a9781ea5234b09501d5356cf966f9237ac8172`. #150/#183 also draft/unmerged.
- Full #40422938067 COMPLETED FAILURE: 15 success/13 skipped/one validate failure job #121921630333 (two existing configuration-auth and cold-reboot REDs per ESP); ESP8266/ESP32 compile success. Native #40422938073 COMPLETED SUCCESS. Docs successor requires separate exact-head classification.
- Actual `tools/v060_physical_evidence_contract.py` Git blob `1dfa4d8efd17c2a96438da10942d5b8dc96bd412` verified by local `git hash-object`.

## Actual execution, full synthetic structural fixture

The `DEVICE` regular expression accepts lexical `/dev/` prefixes but allows dot/dot-dot/empty components. It validates a **claimed manifest metadata field**, never opens a device. Executed the **unmodified source** on a disposable private fixture containing 150 synthetic trial claims, 3 synthetic soak claims and 303 uniquely hashed synthetic capture files.

| Claimed storage_source | Actual validator | Canonical lexical path policy hypothesis |
|---|---|---|
| `/dev/synthetic0` | ACCEPT exit 0 | valid positive control |
| `/dev/../tmp/fake` | ACCEPT exit 0 | invalid parent traversal |
| `/dev/../../etc/passwd` | ACCEPT exit 0 | invalid /dev escape |
| `/dev/./synthetic0` | ACCEPT exit 0 | invalid dot segment |
| `/dev//synthetic0` | ACCEPT exit 0 | invalid empty segment |
| `/tmp/fake` | BLOCK exit 4 | negative control |
| `/dev/not a device` | BLOCK exit 4 | negative control |

**7/7 final expected observations PASS.** An initial **test-harness-only** predicate failed to reject whitespace; it was corrected before the final pass. This was not a source-validator failure or firmware RED. All accepted cases explicitly report `physical_powercut_verified=false` and `production_release_authorized=false`.

## Boundaries and decision

This is a conditional structural metadata/provenance defect **if** a human/downstream process assumes the claimed path is canonical. No real `/dev` path was opened, no actual power cut, payment or coin relay was operated, and no release authorization was bypassed. The earlier duplicate-JSON-member validator finding is separate.

**NEXT:** MASTER review a test-first lexical canonical-path rule rejecting `.`, `..` and empty components, preserving positive/negative controls. Even a canonical path cannot prove device identity, mount isolation, media disposability or physical telemetry. No source fix/merge/flash until review. Physical #34, independent witness #43, paid #31/#32, 150 actual cuts, 30-device 24h soak, reversible migration and permanent signing remain PRODUCTION NO-GO.

**Resume:** read #172 UTC00, all four canonical handovers, draft #193/#179 and latest exact-head CI; verify PEVID blob; seek MASTER decision on canonical metadata path before source correction. NO CODEX.
