# Avee workflow, preset interoperability, and reference motion

Status: implementation authorized by the owner's request to continue and standing approval. Reconciled against d45ddeee; build on the existing application, preserve existing native presets, and leave video-to-graph tracing deferred.

## Outcomes

- A narrow phone has a compact player, direct Library/Visualizer/Queue access, a visible playlist browser, a preset thumbnail grid, and reachable preset/edit/export controls. Fullscreen visualization is optional. Canvas arrangement survives viewport changes and never progressively shrinks saved geometry.
- Selecting a library song constructs the library queue. Actual Media3 end-of-track transitions advance and repeat the queue; repeat/shuffle persist. Do not replace existing passing transition/restore behavior.
- Inspect the provided modern APK read-only for data formats and engine behavior. Preserve the original imported Avee document and assets, render supported nested segment/path/color/measure properties, and retain composition references rather than flattening every pass. Report remaining approximations precisely. Do not redistribute the APK, proprietary code, or artwork.
- Export offers portrait, landscape, and square, plus optimized arrangement, contain, crop, and stretch. Optimized native note compositions place their keyboard near the bottom and allocate the upper area to the main visualization. Separate arrangements remain independent; the exact resolved scene feeds preview and encoder.
- Add source-clock-driven moving traces, fading tails, attack/release envelopes, true projected chord trajectories, and independent motion speed/trail/depth controls. Existing static/full-outline choices remain. Equations remain off by default. Musical ratios use measured/detected equal-tempered pitches and must not falsely claim that music was tuned to a just ratio.
- Responsive frequency visualization, offline polyphonic note transcription, and monophonic microphone tuning remain separate capabilities. Improve the audio response using verified spectrum configuration, without claiming that FFT bars alone identify notes.

## Validation

Add behavioral regressions for editing across viewport changes, repeated edit sessions, bottom occupancy, nested modern preset fields and retained source data, trace age/seek determinism, all chord voices contributing to spatial paths, and zero effects intensity. Exercise real narrow-phone navigation, playlists, arrangement, export orientation and Media3 transitions on API26 and API36. Run host tests, lint and clean APK builds; publish only from a passing same-source matrix. Update the handoff with exact evidence and any compatibility limits.
