# PHX-MASTER migration hold: duplicate quarantine evidence (2026-11-15 UTC23)

Status: **DRAFT / PRODUCTION NO-GO**. Coordination-only source/tree audit; no runtime migration or acceptance.

## Exact references observed
- Experiments main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; development `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- HARDWARE stacked draft PR #312: `90e94d0323ff35fccdf2f892d543c606ffd45cd9`, based on #311 `e6a25a56e9edb1c39e99ec0f5b1e8854ba350e32`.
- COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243`; integration draft #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- Private v11 registry parsed locally; contents and identifiers intentionally omitted from public record.

## Source/destination blob comparison at exact refs
| Board | PR #312 source blob | COE #26 destination blob | Result |
|---|---|---|---|
| ESP32 `BlazePwifiVendo32.ino` | `6c982bf06f018fa859e88cb31ba19980eaca4e23` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | DIFFERENT; implementation parity not established |
| ESP8266 `BlazePwifiVendo.ino` | `90e5fcfa13e6c955212e3f1a9120aebf94fba2ec` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | DIFFERENT; implementation parity not established |

PR #312 changes both inspectors to reject a second matching complete quarantine record, retaining pending state for reconciliation. Its test harness adds scenario 16 for duplicate records; static firmware hardening test adds a matching guard assertion. Exact-head GitHub software runs #43770532527 and #43770532480 report success. This is NOT native hardware, durable filesystem or power-cut acceptance.

## Migration gate / owner actions
1. PHX-HARDWARE: enumerate all changed source files and direct/transitive dependencies; provide per-file destination mapping, licenses and complete source/destination Git blob comparison; avoid assuming equal behavior from unequal blobs.
2. PHX-QA: independently exercise duplicate complete records, partial/corrupt lines, reboot replay, read/write failure, nonmatching identity and recovery-required latching on both boards. Verify corresponding destination tests at its **own** exact SHA.
3. COE integration owner: inspect draft #26 before proposing any move. Its five previously identified checks (#43096752609, #43096752632, #43096752800, #43096752563, #43096752557) remain queued at the observed candidate SHA. Require completed exact-SHA CI, import completeness, license attribution and reversible rollback proof.
4. PHX-MASTER: run the coordination regression suite on this branch and document its actual execution; source/tree inspection and upstream GitHub CI do not count as Master test execution.

Do not merge, release, flash, provision credentials or admit live payments. Protected signing/independent anti-rollback witness, crash-atomic durable financial state, reversible migration, independent QA, native acceptance, 150 real power cuts and 30-device 24-hour soak remain unverified gates.
