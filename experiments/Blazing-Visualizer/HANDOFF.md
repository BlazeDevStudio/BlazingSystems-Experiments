# Blazing Visualizer handoff

## 2026-10-22 Avee preset import compatibility increment (COMMITTED_UNVERIFIED)

- Existing modern-Avee phone/navigation/player/crop work is at commit 863d91d; DO NOT duplicate its Media3/layout changes. This pass changes only .viz importer, its regression tests and this handoff.
- Plain JSON and ZIP archives with exactly one JSON-formatted .viz/.json/.txt entry can be recognized using the existing bounded extraction/path rules. Importer understands direct element-array and composition-wrapped JSON, nested v wrappers, float pair arrays or x/y objects, boolean visibility, rotation in degrees, Spectrum and Waveform type aliases. It still reports approximation and explicitly refuses opaque binary .viz and ambiguous multi-preset archives. This is NOT a claim that all modern Avee .viz presets work; a real legally obtained sample corpus is necessary.
- Test state: 3 new host fixture tests added, exact-head GitHub Actions pending. No customer APK, no new release. Same existing API26 ActivityScenario failure may persist.
- Next action: inspect exact-head Gradle host/Android26/36 run, fix compile/test findings, then independently compare modern Avee preset samples and real-device rendering. Preserve existing Basic Pitch and licensed FFT source.

## 2026-10-22 modern-Avee player and portrait export correction

- Owner's refreshed priority: **preserve current visualizer presets**; fix music player continuous queue playback, modern phone UI, Avee .viz interoperability, and lower blank export framing. Audio-reactive visual response must not be confused with polyphonic Basic Pitch note transcription. Uploaded Avee 1.2.252 Premium APK is an unofficially modified build (contains E_l_a_Mods.xml and libpairipcore); use only for reference, do not embed or redistribute any protected source/assets.
- Implemented in this commit: Media3 repeat ALL by default and saved OFF / ONE / ALL plus shuffle toggles; Library selection constructs ordered library listening queue rather than playing only a single file; compact phone-first header and bottom Library / Visualizer / Queue navigation with mini-player; hide navigation while arranging scene; export COVER default to fill portrait video without lower letterbox, explicit CONTAIN and STRETCH choices, matching saved frame layout for preview and MP4. Added shape regression and menu/export click tests.
- **Not a complete Avee 1.2.252 clone or .viz import implementation.** Existing AveePresetAdapter still supports only Text, Image, Bars and Particles from Avee JSON. Modern .viz should be independently researched from a legally obtained template sample before claiming broad compatibility. The modern APK is not a preset sample.
- Pending: same-SHA GitHub Actions JDK17/SDK36 host/lint/APK and API26/API36 interaction tests, plus real phone UI/playback/export inspection. Current published GitHub release is still Preview 1; do not mislabel a CI build as a validated new release. Owner's hourly preview notification remains configured.
- Previous baseline before these changes: source 31a6f7c passed build and API36 device tests but API26 failed permission-related lifecycle RESUMED transition (run 39764907346). This remains open; Android8 launch resilience needs attention. Video-to-graph stays last.


## 2026-10-22 click-by-click audit pass (in progress)

- Owner reports Preview 2 buggy. Source inspection and CI confirmed: API26 permission-smoke cannot see OS permission buttons (run 39756912938), while API36 and the clean host build passed on source d31a43b; release remains blocked. Do not present the old downloadable CI APK as accepted/released.
- This pass adds direct Compose click tests for Library/Visualizer/Queue, preset selection and dismissal, editor/arrangement controls, search/no-results feedback, queue sorting and playlist save; routes multi-file import around bad files rather than failing the entire selection; makes the export affordance unavailable before loading a song. The arrangement canvas gains tap-to-select, in addition to drag/resize. Android 8 test retains denied/granted permission UI assertions but documents a fallback if the emulator's system installer never exposes its permission buttons; on modern Android a missing dialog remains a hard test failure.
- Verification of *this* change: pending GitHub Actions.
- Actions run 39764223851 failed before executing tests: missing `com.blazingsystems.visualizer.playback.Playlist` import in the playlist-delete UI added by this pass. The missing import is corrected here. Do not treat this build as validated; recheck next same-SHA host and device jobs.
 Until same-commit host/lint/API26/API36 pass, do not publish it as validated. Physical device coverage, tuner and actual export reliability still need acceptance.


- Detailed interaction routes and unverified checkpoints: [docs/acceptance/click-audit.md](docs/acceptance/click-audit.md).
- Playlist deletion now asks for confirmation; search uses a stable semantic tag for UI automation.

## 2026-10-22 late owner APK delivery checkpoint

- Owner explicitly requested new Preview 2 APK as soon as compiled, without waiting for Codex to submit it. A compiled but *not yet device-verified* APK is available from CI artifact https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39754432234/artifacts/12415611017 (ZIP containing app-debug.apk). This is not a published GitHub Releases APK; no direct Preview 2 Releases URL is established yet.
- Validation run 39754432234: clean Android host build, 76 host tests, lint and APK packaging passed. API26 failed on the fresh-runtime-permission smoke (Android 8 SystemUI also crashed on keyguard occlusion; package installer opened, but the test could not find deny button). API36 failed in PlayerRestoreTest.kt:53 because the pending A/B loop initial position was not observable at READY. These are actual failures; do not label full CI a success.
- d3f50a4f79a4ce87bace0e1a8df4ca46589f59d3 adjusts Media3 restore to apply pending A/B loop seeks after playback READY and searches all accessibility windows/text alternatives for OS permission buttons. Full native validation is pending, and hardware behavior is not yet proven.
- The Preview 2 GitHub Release publisher is installed at .github/workflows/blazing-visualizer-publish-preview2.yml. It is gated on a *same source commit* clean build plus passing API26/API36 jobs; it verifies application ID/version, APK signing certificate, archive ABIs, downloads the release asset again and compares bytes. The first update had invalid YAML indentation and a within-step environment oversight; the following fix addresses both. Publication is intentionally blocked until the device matrix passes. The owner has a one-hourly notification watch for a published direct APK URL.
- Do not replace Preview 1. It uses an incompatible signing identity: export desired presets, uninstall Preview 1, then install Preview 2 once available. Keep video-to-graph deferred until after this first upgraded APK.
- Priority: examine latest Android CI failures, fix test or runtime code without weakening meaningful assertions, and verify release workflow actually publishes and byte-checks the APK on a passing candidate; edit this handoff with exact run and release proof.


Updated 2026-10-22. Resume this existing application; do not restart it.

- Repository: https://github.com/BlazingSystems/BlazingSystems-Experiments
- Feature branch: `blazing-visualizer`; project: `experiments/Blazing-Visualizer`.
- Draft PR: https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/133 . Main is untouched.
- Portable non-Codex prompt: [CONTINUE_WITH_CHATGPT.md](CONTINUE_WITH_CHATGPT.md).
- Current iteration spec, ordered plan, rulings and evidence: [docs/plans/2026-10-22-preview-2.md](docs/plans/2026-10-22-preview-2.md).
- Reference-video fact check: [docs/acceptance/reference-video-math.md](docs/acceptance/reference-video-math.md). Equations must be optional and OFF by default. Video-to-graph tracing is LAST, explicitly excluded from the first improved APK.

## Reconciled development

ChatGPT changes already on the branch before this pass included persisted per-track Practice (47635172), independent Library/Queue with MediaStore permission and discovery (f1fbaf41), serial preanalysis (1b9428f2), note bands/piano effects/palette (8775af84), and the YIN microphone tuner (6a87eb30 plus lint correction 84148e2a). Preserve these implementations.

This integration adds preview/export decoded-audio leases across repository instances; joins cancelled background preparation before foreground decoding; checks the content/model/parameter note cache before decoding library tracks; displays preparation status; restores the actual paused Media3 queue without interrupting a running session; retains pending Practice speed/loop across connection; guards microphone callbacks on stop/background; strengthens harmonic rejection/smoothing.

It also adds original note-derived Harmonic flow, Orbital voices and Wave garden presets; an equations checkbox; independent piano-part/background colors; pitch-routed scale bindings and spectrum bins; zero-intensity decorative-motion fixes; clipped per-key glow; long-press move/resize handles; separately persisted export transforms or auto-fit-follow mode; persisted portrait/landscape/square output settings and an accurately fitted composition preview.

## Verification state — release candidate awaiting device acceptance

- c85247b is the regression-test baseline. Actions run 39747267719/build119718745948 executed 51 host tests with three intentional behavioral failures: piano glow spilling to an unpressed key, explicit layer color overridden by palette, and motion at zero intensity.
- e921558's initial pixel-test attempt failed Robolectric SDK setup; c85247b pins supported API33 and produced the meaningful failures above.
- General Compose tests now grant music access before creating the Activity. Previous API26/API36 failures were a visible GrantPermissionsActivity covering the Compose hierarchy; do not count the older matrix as passing.
- Integrated source c84a4d1e19daf0be695a4e9dba6e191032a86e44 passed all 76 host tests (0 failures/errors), lint, APK and instrumentation-APK compilation in run 39753520154/build119739674443. Downloaded host XML was inspected: leases7, rendering6, layout/math5, startup/persistence3, YIN7 all passed. Its emulator jobs were superseded by the corrected runner configuration; do not call that device matrix a pass.
- Current candidate: 4f697965ba3b0e0b90779584cc4200deac260528, validation run https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39754432234 . It adds clean-build signing retention plus correct emulator working directory and a standalone fresh-install permission smoke test. Host clean build and API26/API36 jobs are pending at this checkpoint.
- New native checks isolate queue/loop restoration from any Activity/ViewModel owner; preserve a live session against stale saved-track loops; cover graph preset PNG rendering, pack round-trip and MP4. General Compose checks also cover Practice and independent export layout through configuration recreation; the new host tests separately verify disk writes across tracks.
- Local Gradle bootstrap is blocked by Java networking in this environment; use GitHub Actions. Numerical Python tuner checks are supplementary and are not JVM/device or real-microphone proof.

## Release baseline

ONLY preview 1 is currently published; it does not contain these October 22 improvements.
Direct APK: https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/blazing-visualizer-v1.0.0-preview.1/Blazing-Visualizer-preview-1.apk
SHA256: ba86f7b48b9b751d3d1399611dc1cd8e2d20cfdc26ce92cb14322ec4d9e5ffb3 ; 31,605,136 bytes.
Validated source: 590150cc672007a3951b7d6f5366a532297be5ae ; full successful run 39717064004.
ChatGPT file URLs fail on the owner's phone; publish and verify a GitHub Releases direct APK URL. Do not replace preview 1. Preview 2 now uses a retained public debug-only identity, documented in config/README.md; expected certificate SHA256 64f9fbd13d72bb5ef88bccdc4602a487fea21fb73a13298b93a0f2b1f6c2109c. Preview 1 used an ephemeral CI key: export wanted BlazeViz presets before its one-time uninstall/reinstall. Future previews can update preview 2 with the retained identity. The publication workflow must verify both actual certificates.

## Next actions

1. Finish candidate run 39754432234 and inspect the clean host build plus API26/API36 permission and native acceptance reports. Source host regressions already passed at c84a4d1; do not redo implemented features.
2. One fresh whole-change review is complete. Six material findings were fixed: startup writes before load, per-track changes lost through conflation, stale preview aspect on scene replacement, missing low/high piano keys, fitted text shrinking, and stale-loop seeking during live-session adoption. Five host reproductions were watched fail in run39752269344 then pass at c84a4d1; live MediaSession behavior is covered by isolated native tests. Review record/rulings are in docs/plans/2026-10-22-preview-2.md. Do not commission duplicate whole-change reviews.
- The editor states the graph cap of 12 pitches; equations label ratio truncation beyond six. Practice retains full detection. Tuner generation checks/publication now run on Main. Physical microphone behavior is still unverified.
- A normal preview renders a fitted COPY of canonical scene geometry using ephemeral StudioState.previewAspect. Entering arrangement captures that visible geometry as the new design canvas. Export fitting and its preview resolve from the same canonical scene or the saved independent transforms.
3. Publish preview 2 from the exact validated CI artifact via the preview publication workflow, then verify its release asset, hash and direct link. Record exact source/build/release/signing evidence here.
4. Physical arm64 playback/export/microphone and longer mixed-music note accuracy remain device acceptance checks. Do not claim perfect transcription or a calibrated physical tuner from synthetic tests.
5. Deliver the non-video-renderer APK first. Only then consider the deferred video tracing/Bezier renderer.

Routine implementation, testing, feature-branch updates and preview publication are already authorized. Do not ask repeatedly to continue or launch paid Codex/cloud-agent tasks. Keep source and this handoff pushed after each material checkpoint.
