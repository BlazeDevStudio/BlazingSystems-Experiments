# Replica — Blaze Systems / REA: Blazing Visualizer acceptance evidence

Date: 2026-10-23 (Asia/Manila). Branch: `blazing-visualizer`. Owner-authorized project only. **No competitor binary analysis was executed through REA's stdio runtime.** REA plugin v0.1.2 is installed but its REA MCP/JADX engine is not connected in the ChatGPT cloud runtime. Replica's recon/test/diff methodology is applied to first-party implementation and test evidence; this is not a license to copy proprietary code.

## Observed platform routes and acceptance

| Flow | User-visible goal | 2026-10-22 source/CI evidence | Status |
|---|---|---|---|
| F01 | Library songs flow continuously to next | Media3 playlist and Repeat All; QueueRegressionTest native transition exists | Tested on API36 matrix, not separately certified physical playback |
| F02 | View presets and edit arrangement on phone | ClickAuditTest navigation/editor coverage | API36 navigation case passed; physical phones not run |
| F03 | Export preview and MP4 agree, no bottom letterbox | Export OPTIMIZE / COVER, same SceneLayouts.forExport | Host test passed; API36 offscreen preview-label assertion failed before this UI correction |
| F04 | Save playlist and browse playlists | ClickAuditTest partial import, queue sort and playlist save | API36 `Playlists` absent in composed viewport because section was below songs; moved before songs |
| F05 | Deny / regrant media permission | MusicPermissionTest on fresh API26 | Denial and denied-Library tests passed, API26 system UI crashes, scenario.recreate after shell grant hung PAUSED; removed only second recreate |
| F06 | Live mic listens without separate tuner | Mic chip invokes audio capture and onSamples FFT feeds same renderer | Source present, real hardware/audio focus not certified |
| F07 | Modern Avee custom preset import | AveePresetAdapter JSON subset and explicit unsupported reports | Partial approximation only, binary/full FX parity not established |

Source CI `39862655659`, source `607ed4fd6646139640ad2a331f451a708d7ed362`: host build/tests/lint/APK PASS, API26 fresh permission FAILED, API36 instrumented suite **17 passed, 2 failed**. Report archive API36 artifact #12462544721 / API26 #12463506039. API36 XML identified failures at `ClickAuditTest.kt:139` (offscreen export-preview semantics) and line 98 (Playlists not composed yet). API26 XML identified `MusicPermissionTest.kt:103`: `scenario.recreate()` following emulator `pm grant`; prior denied scenario recreate passed. API26 logcat also shows `com.android.systemui` NullPointerException in NavigationBarFragment, not app code.

## Next evidence and release gate

- Re-run **same-source** clean host build, Android 8/API26 and Android 16/API36 device tests. Confirm CI passes; never mark a planned fix as PASS.
- Inspect actual Android emulator UI hierarchy/screenshots and real phone touch/scroll interactions (not executed in this chat).
- Verify AAC/MP4 export, background playback and microphone capture on physical ARM64 before claiming modern Avee parity.
- Only published, hash-verified GitHub Releases APK is eligible as the new release link. As of this report only `blazing-visualizer-v1.0.0-preview.1` is published.

Intentional limitations: no proprietary Avee code or assets incorporated; title/brand is Blaze. Confidence: high in XML failure stacks; medium in UI failure hypotheses until rerun; none for unexecuted device recordings.

## 2026-10-23 Replica + REA continuation, CI report–grounded

- Public reference: https://aveeplayer.com/ confirms music player, folder navigation, radio, equalizer, playlist/queue, advanced elements, 4K export, 1.2.83+ `.viz` format. `replica/recon.md`, `replica/features.csv`, `replica/test-plan.md`, `replica/bugs.md`, and `replica/parity.md` now hold the app audit, gaps, evidence and reproduction paths.
- GitHub Actions run `39880221516` exact XML: build SUCCESS, API26 1/1 FAILED after Android PackageInstaller fallback because no Compose hierarchy after permission grant; API36 ClickAuditTest 2/4 FAILED (`export-sheet` absent immediately after tap and `Playlists` not found after Save). Other API36 instrumentation: 17 of 19 passed.
- Changed instrumentation to wait for Save dialog closure and real ModalBottomSheet semantics without bypassing the controls. The API26 emulator-specific broken-installer fallback checks real permission and Android content hierarchy; **does not claim** post-grant foreground Compose UI was exercised. A functioning OS button path still requires Compose Library visible. Exact-head rerun pending.
- REA analysis engine unavailable because the installed plugin wraps a local stdio MCP server; no APK/JADX tooling was executed.
