# Blazing Visualizer handoff

Updated 23 October 2026 (Asia/Manila). Continue this existing Android app; do not restart or overwrite concurrent work.

## Published APK

**Preview 2 is now published and verified.**

- Direct download: https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/blazing-visualizer-v1.0.0-preview.2/Blazing-Visualizer-preview-2.apk
- Source: `48c229e607e7fdcab2f71c915c7f75102a1e9304` on `blazing-visualizer`.
- Full validation: https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39889541772 . Clean host tests/lint/APK, API26, and API36 all succeeded.
- Publisher: https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39889541799 . It verified package/version, retained signer, both ABIs and re-downloaded identical release bytes.
- Size: 31,769,164 bytes. SHA256: `e12079aecc762a08e7bb15b19f79358ef11e9a7f402e4a35d975a386f8fae3d5`.
- The retained public debug-only certificate SHA256 is `64f9fbd13d72bb5ef88bccdc4602a487fea21fb73a13298b93a0f2b1f6c2109c`.
- Preview 1 used a different signing key. Export wanted presets before uninstalling Preview 1, then install Preview 2. Later previews keep the retained identity and can update Preview 2.

ChatGPT file download URLs fail on the owner's phone. Deliver direct GitHub Releases APK URLs.

## Repository and scope

Repo: BlazingSystems/BlazingSystems-Experiments. Project: experiments/Blazing-Visualizer. Draft PR133: https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/133 . Main remains untouched.

The owner wants the familiar current Avee player/editor workflow and useful preset interoperability, phone-sized controls, continuous playback, note following, MP4 export, and much closer reference motion. Existing liked native presets must stay available. Routine implementation, feature-branch updates, testing and preview publication are authorized; do not repeatedly request approval or launch paid Codex tasks.

Portable non-Codex continuation prompt: [CONTINUE_WITH_CHATGPT.md](CONTINUE_WITH_CHATGPT.md).

## Implemented and reconciled

- MediaStore permission/discovery, manual import, separate reorderable/sortable queue and playlists; library selection builds a listening queue. Media3 repeat-all default and repeat/shuffle settings persist.
- Preview 2 fixes the narrow-phone toolbar overflowing offscreen and exposes Playlists as a browser tab. Requested playback takes priority over stale old-item updates; a race had cancelled newly imported/selected tracks. Exact-source device tests now pass, including natural next-track and last-to-first repeat-all transitions.
- Per-track Practice speed, transposition, spelling/register, section loops, note edits and MIDI/CSV export persist. Basic Pitch analysis is cached and queued with current-track priority; decoded-audio ownership and startup persistence regressions were fixed.
- Lo/Lo2/Mid/Mid2/Hi/Hi2 MIDI routing, independent piano/global animation intensity and part colors; only active keys light. Long-press move/resize, preview or separate export layout, portrait/landscape/square MP4 and optimized note-keyboard bottom occupancy exist.
- Editable note-wheel idle text and simultaneous note labels when no chord is recognized; an expanded exact-set chord dictionary avoids guessing from incomplete notes.
- Preview 2 mic toggle feeds the main visualizer with FFT and a monophonic YIN reading. It does not open a separate tuning window. Live polyphonic estimates and an independent capture animation clock are the next increment.
- Three original math presets and optional equations are included. Equations default OFF. [Reference math fact check](docs/acceptance/reference-video-math.md) remains authoritative.
- Avee plain JSON and JSON-in-ZIP .viz subset supports wrapped vectors, colors, nested polygon/segment settings and safe assets. In Preview 2, compatibility is partial and the importer flattens multiple compositions; the Preview 3 candidate replaces this with referenced passes and still approximates modern effects. Never claim all Avee presets or pixel-identical rendering work.

## Current continuation: Preview 3 candidate

The `blazing-visualizer-notes-motion` integration branch preserves the next increment. Primary branch updates use an expected-head lease; reconcile both heads before editing so concurrent work survives. Published Preview 2 remains intact. Preview 3 (versionCode 3) must pass its own exact-source matrix before its separately tagged APK is published. The publisher verifies the retained signer and refuses to overwrite any existing release.

Implemented candidate, not yet verified: thumbnail preset grid and fullscreen control; note-aware optimized export reflow with custom separate layouts preserved; all unknown note classes displayed in fitted rows; conservative live spectral polyphony plus precise single-note YIN with an independent capture clock; five optional outline/trail/reveal, projected chord, shared-cursor wave, rhythm gate and stable radial motion presets. Equations stay off. Existing native presets remain.

Avee candidate retains original JSON and per-layer raw metadata through native packs, renders referenced compositions instead of flattening them, adds paired segments with independent colors/signed heights, procedural internal images, image aspect/circle/tint/blend and bounded current-frame effects. Spectrum2 uses configured arbitrary-frequency correlations with bounded, seek-independent recorded response. Imported contain/cover frames the entire composite once. Unknown expressions/shaders, exact temporal blur/beat gain and arbitrary presets remain partial. No source APK/code/artwork is redistributed.

Focused tracker, geometry, native-pixel, composition, segment and frequency-bank tests accompany this increment. These are verification targets, not passing evidence until Actions runs. Continue clean host/lint/APK and API26/API36, resolve failures, review pixels and verify the direct Preview 3 asset before reporting completion. See [mobile/motion evidence](docs/acceptance/2026-10-23-mobile-and-motion.md).

## Reference and acceptance limits

The uploaded Avee 1.2.252 APK is unofficially modified (contains E_l_a_Mods and pairip). Use read-only functional/schema observations, source-licensed components and original implementations. Do not distribute its code, APK or artwork. A prior narrow DEX/JADX audit found Spectrum2's arbitrary-frequency correlation bank and response controls; its strongest-bar index is not a MIDI note detector. The engine tool was not connected; temporary local tooling supplied static evidence, not official runtime parity.

Reference recording observations distinguish full interval outlines plus bright travelers, progressive shared-cursor reveal with hard loop resets, 3D chord projections, fixed polygon impacts, and settled radial contours. Implementations are original interpretations, not recovery of the author's production project or stem separation.

The published matrix proves emulator behavior, not physical ARM64 audio focus, microphone latency, arbitrary-song transcription accuracy or full modern Avee parity. Live harmonic/octave ambiguity remains. More details: [mobile/motion evidence](docs/acceptance/2026-10-23-mobile-and-motion.md), [Replica audit](docs/acceptance/replica-rea-audit.md), [older execution record](docs/acceptance/execution-record.md).

**Video-to-graph tracing/Bezier rendering stays LAST and is explicitly excluded from these APKs.** Deliver the improved player first.
