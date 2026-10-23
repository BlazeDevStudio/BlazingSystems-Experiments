# Replica Bug Ledger — Blazing Visualizer

Source: GitHub Actions run [39880221516](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39880221516), SHA 3dc037c (2026-10-23).

| ID | Severity | Reproduction evidence | Failure | Remediation / verification |
|---|---|---|---|---|
| B01 | S2 | API26 fresh MusicPermissionTest, artifact 12470841669 | Permission granted through emulator shell fallback after broken system UI; Compose hierarchy absent in PAUSED state, final screen assertion fails | Keep permission and Android content-root assertions for emulator fallback and real Compose UI assertion on working dialog; test-limited API26; rerun needed |
| B02 | S2 | API36 ClickAuditTest exportOrientation..., artifact 12471085943 | Cannot find `export-sheet` immediately after clicking Export video | Explicitly wait for actual ModalBottomSheet semantics; test still fails if panel does not appear; rerun needed |
| B03 | S2 | API36 ClickAuditTest partialImport..., artifact 12471085943 | Cannot find `Playlists` after saving queue and switching Library | Wait for save dialog to close before nav, assert Library visible and eventual Playlists existence; rerun needed |
| B04 | S2 | Owner's Preview 2 feedback | Imported Avee .viz effects and newer animation styles remain approximate | Real user-provided preset corpus + property-by-property independent renderer tests needed |
| B05 | S2 | Owner's Preview 2 feedback | UI too dense for phone; video bottom letterbox | Earlier commits moved playlist up, compacted player, added portrait optimize; physical regression screenshots needed |

Failures B01–B03 are from real test reports, not inferred successful fixes. Last release remains Preview 1 pending full run.
