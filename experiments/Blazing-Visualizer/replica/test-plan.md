# Replica Test — Blazing Visualizer, 2026-10-23

Only the owner's app is automated. No testing or private data extraction from Avee. Statuses are from existing CI run 39880221516 at SHA 3dc037c; fixes in this later commit require fresh runs.

| Case | Setup → interaction → assertion | Before-fix evidence | State |
|---|---|---|---|
| F01-H1 | Import 2 WAV files; seek near end, assert Media3 automatically advances | QueueRegressionTest exists; API36 full suite reported 17/19 | Passed on API36 existing run |
| F02-H1 | Presets → select → editor → tap/drag canvas → Done | ClickAuditTest nav route | Passed on API36 existing run |
| F03-H1 | Import audio → Export → select portrait and fit → separate canvas edit | Export node absent in immediate Compose assertion; test now waits for actual entry, not skipping it | Rerun pending |
| F03-E1 | Export 9:16 and ensure piano bottom occupies expected region | Host layout regression tests | Host passed; actual MP4 on phone not run |
| F04-H1 | Save queue playlist, close dialog, enter Library, assert saved playlist and cancel delete | A premature navigation click could race dialog dismissal; test now waits for closure | Rerun pending |
| F05-N1 | Fresh install → Deny → Library → Refresh → Allow | API26 installer crash; final Compose hierarchy absent despite permission change | Partial fallback only on API26, not a complete foreground UI check |
| F05-H1 | Same on Android 16 with actual Allow and return to Library | Android 16 permission test 1/1 passed | Passed on API36 previous run |
| F06-H1 | Mic Live on physical ARM64 → note wheel updates → app background → mic off | Source reviewed, no hardware session | Not run |
| F07-E1 | Import modern .viz with nested segments and missing image | Unit and parser source, no representative external preset corpus | Partial; externally unverified |

Severity definition follows Replica: S1 data loss/security, S2 broken core feature, S3 workaround, S4 cosmetic. Never call a previously failed test passed merely because a patch was committed.
