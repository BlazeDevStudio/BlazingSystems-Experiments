# Blazing Visualizer handoff

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

## Verification state — integration not yet approved as a release

- c85247b is the regression-test baseline. Actions run 39747267719/build119718745948 executed 51 host tests with three intentional behavioral failures: piano glow spilling to an unpressed key, explicit layer color overridden by palette, and motion at zero intensity.
- e921558's initial pixel-test attempt failed Robolectric SDK setup; c85247b pins supported API33 and produced the meaningful failures above.
- General Compose tests now grant music access before creating the Activity. Previous API26/API36 failures were a visible GrantPermissionsActivity covering the Compose hierarchy; do not count the older matrix as passing.
- Integrated host/lint/assemble/API26/API36 verification is pending. New math/layout/cache/YIN and queue/Practice/export-layout regressions are included but must actually run.
- Local Gradle bootstrap is blocked by Java networking in this environment; use GitHub Actions. Numerical Python tuner checks are supplementary and are not JVM/device or real-microphone proof.

## Release baseline

ONLY preview 1 is currently published; it does not contain these October 22 improvements.
Direct APK: https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/blazing-visualizer-v1.0.0-preview.1/Blazing-Visualizer-preview-1.apk
SHA256: ba86f7b48b9b751d3d1399611dc1cd8e2d20cfdc26ce92cb14322ec4d9e5ffb3 ; 31,605,136 bytes.
Validated source: 590150cc672007a3951b7d6f5366a532297be5ae ; full successful run 39717064004.
ChatGPT file URLs fail on the owner's phone; publish and verify a GitHub Releases direct APK URL. Do not replace preview 1. Check signing continuity before promising an in-place upgrade.

## Next actions

1. Run the integrated source through host tests/lint/assemble and API26/API36 device matrix; inspect every failure and fix its cause.
2. Exercise permission denial/manual import, layout gestures, actual queue ordering, Practice persistence, export aspect/fitting and audio cache ownership. Obtain a fresh whole-change review and fix material findings.
3. Publish preview 2 from the exact validated CI artifact via the preview publication workflow, then verify its release asset, hash and direct link. Record exact source/build/release/signing evidence here.
4. Physical arm64 playback/export/microphone and longer mixed-music note accuracy remain device acceptance checks. Do not claim perfect transcription or a calibrated physical tuner from synthetic tests.
5. Deliver the non-video-renderer APK first. Only then consider the deferred video tracing/Bezier renderer.

Routine implementation, testing, feature-branch updates and preview publication are already authorized. Do not ask repeatedly to continue or launch paid Codex/cloud-agent tasks. Keep source and this handoff pushed after each material checkpoint.
