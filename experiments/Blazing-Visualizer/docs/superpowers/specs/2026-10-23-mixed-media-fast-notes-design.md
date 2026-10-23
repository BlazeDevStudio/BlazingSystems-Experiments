# Mixed media and fast note preview

Owner requested continuation of the unfinished mobile roadmap, mixed media selection, automatic deepest-layer video background, faster note identification, and evaluation of instrument separation. Standing instruction approves routine design/implementation and opts out of repeated confirmation questions.

## Decisions and approaches

Keep the current Kotlin/Media3 architecture and existing presets. Select multiple audio/video documents into the same library and queue; inspect media metadata rather than trusting extensions. A video uses the existing Media3 session's audio, timeline, pause/seek/speed and a video TextureView behind a transparent visualizer TextureView. Do not create a second audible player. Audio-only selection removes the video background. Video backgrounds also appear in MP4 exports, using source-time frames with bounded bitmap size. Silent videos remain playable/exportable without fabricated detected notes.

The slow path currently hashes/decodes the whole file, then infers the whole track before publishing notes. Add a bounded, independent quick preview decoder near the current playback position. Publish timestamped spectral/YIN estimates as frames become available, cached by source/time and cancelled on seek/source changes. Continue full Basic Pitch analysis separately for corrections, persistence and final export; temporary estimates never replace the verified analysis cache or saved edits. Playback remains available throughout. Cache misses/pauses must not trigger one full decode per UI tick.

Alternatives considered: Media3 PCM tap avoids duplicate decoding but requires timeline accounting across seeks, buffering and speed processors. Bounded source-time decoding is selected for this increment because its timestamps and cancellation are testable and it can reuse the current decoder. Blocking on whole-file neural inference remains the high-quality background path, not the preview prerequisite.

Instrument separation is a separate refinement stage: evaluate licensed Demucs/source-separation engines and the data contract for per-stem analysis. Do not call frequency bands isolated drums/piano/vocals, do not silently upload songs or add an untested heavy model to startup. A concrete offline stem workflow may be added after measuring a real model; no fake separation switch. Video-to-graph tracing remains deferred.

## Acceptance and constraints

Android26+, SDK36, current Media3 1.8.0; retain queue/Practice/layout/preset/export behavior and original licensing. SourceRef metadata defaults must load old projects. Multiple audio/video selection, video-to-audio transitions, video pause/seek, portrait/landscape framing, silent video handling, stale quick-result rejection and first quick result before full analysis require tests. Native video export must show the input video behind the visualizer and preserve one audio track. Keep memory bounded and release video surfaces/retrievers/decoders on disposal. The model output is an estimate, especially in dense music.

Production signing/physical-phone validation remain unresolved. Publish a separately versioned Preview4 only after clean host/lint/APK and API26/API36 validation, direct-download signing/hash checks and an updated handoff. Existing releases and main remain intact.
