# PHX-MASTER — pending-clear preflight migration gate (2026-11-16 UTC00)

**Status:** DRAFT / PRODUCTION NO-GO. Coordination only; no source migration or release approval.

## Reproducible exact-ref evidence

- Experiments main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; development `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` (main is 293 commits ahead in Git ancestry, not functional parity).
- Master draft #288 prior HEAD: `ce7f4ac89aaf85aae528e826afec69b2184f92a1`; ownership routes inspected, including non-copyable broad `Rental/` destination.
- HARDWARE stacked draft #313: `phoenix/hardware-clear-preflight-20261115@6b8583b7b0b39314bce39666d1cdd0b8f84afe48`, stacked after #312. Exact-head software CI: [43776173534](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43776173534) and [43776173574](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43776173574) completed success. These are not physical tests.
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243` (structure-only). COE draft #26: `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12`; its five PR workflows are queued, not passing.

## Firmware blob identity comparison (GitHub contents API)

| Target | HARDWARE #313 source blob | COE #26 staged destination blob | Result |
|---|---|---|---|
| ESP32 `BlazePwifiVendo32.ino` | `b494056c64ef527ac15c8bea5f31ceabda6dc322` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | DIFFERENT |
| ESP8266 `BlazePwifiVendo.ino` | `02e8cef30d80c55d23f24b6c7be98645411e4739` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | DIFFERENT |

These identities prove blob divergence, **not** whether the destination behavior is missing or equivalent. No license, full import completeness, dependency, file-mode, or test identity parity is asserted.

## Specific pending-clear safety review

HARDWARE #313 describes a preflight check before `clearPending()` deletes any of `pending.dat`, `pending.new`, or `pending.bak`. The reported repair counts durable candidates first; multiple candidates must latch recovery and leave all evidence intact. Independent QA must confirm this on **both** exact-source implementations and the proposed destination with negative cases: every pairwise ambiguity, triple ambiguity, failed remove, missing filesystem, existing recovery latch, simulated reboot, and retained RAM/durable evidence. Verify test harness actually compiles/executes the real implementation; do not treat test names or a successful workflow as sufficient evidence.

## Owner-routed next actions

1. **PHX-HARDWARE:** provide per-file source/destination semantic diff, dependencies, licensing, file mode, test identities, and reversible patch plan; preserve stacked PR order (#312 then #313).
2. **PHX-QA:** independently rerun exact-SHA negative recovery tests and review source/destination parity; record actual commands and results.
3. **COE integration owner:** resolve five queued exact-head workflows, do not overwrite staged firmware or merge until evidence reviewed.
4. **PHX-MASTER:** execute `coordination/phoenix/verify_coordination.py` and companion tests against this exact head in a suitable checkout; this run performed GitHub source/tree and CI metadata inspection only, not a local test run.

Private Drive v11 registry JSON was parsed in restricted workspace for recovery context; contents/identifiers must remain private. No automatic merge, flash, signing, financial operation, or release. Independent protected signing/anti-rollback witness, crash-atomic financial state, reversible migration, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner release authorization remain required.
