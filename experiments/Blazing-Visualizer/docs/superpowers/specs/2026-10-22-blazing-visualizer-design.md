# Blazing Visualizer — product and architecture specification

Date: 22 October 2026 (Asia/Manila)  
Owner: Loumer Cabaluna Manreal / Blazing Systems  
Status: written specification for owner review; implementation has not started  
Repository: BlazingSystems/BlazingSystems-Experiments  
Project directory: experiments/Blazing-Visualizer  
Proposed Android application ID: com.blazingsystems.visualizer

## 1. Agreed purpose

Build an Avee-based Android music player and visualizer with an original Blazing Visualizer identity, modern interaction design, editable visual compositions, video export, and visualizer-pack import/export.

Its defining capability is audio-to-note analysis that produces notes musicians can inspect and follow on their own instruments. A decorative frequency spectrum alone does not meet that requirement: the application must represent pitch, octave, note onset, and duration, and provide a synchronized practice view.

The owner chose a source-built Avee-based application rather than modifying the uploaded 1.2.252 APK. The requested modernization covers the complete user experience, not just the displayed name and icon. Existing Avee notices remain in the source and acknowledgements.

### Required outcomes

| Owner requirement | Concrete behavior |
| --- | --- |
| Distinct Blazing Visualizer product | Original navigation, visual language, player, studio, practice view, editor, and export flow. Installable alongside Avee under a separate app ID. |
| Music visualization like the supplied video | Twelve chromatic pitch-class nodes, glowing active notes, chord connections, estimated chord names, and synchronized piano highlights. |
| Notes people can follow | Octave-specific note timeline, readable names, onset/duration, slower practice playback without pitch change, and section looping. |
| Video export | Real MP4 files containing rendered visualizer frames and synchronized audio. |
| Visualizer plugin import/export | Portable, editable visualizer packs with scenes and assets; version-aware Avee preset compatibility with an explicit supported-feature boundary. |
| Modern Avee-like utility | Local music browsing, queue/playlists, background playback, layered visualizer editing, reusable presets, images/text/effects, and output sharing. |

## 2. Selected technical direction

Use a modern Android application around a selectively ported Avee visualizer core. Preserve and adapt useful source-available rendering, spectrum, waveform, scene, and customization components. Add an original application shell, modern media integration, a dedicated note-analysis engine, and a shared preview/export renderer.

The source baseline is Azy-Kun/AveeOpenPlayer_1.0.34 at commit c909d8b50dcabb5d2b54dc1bfd72f9431cdd7af6. The inspected source exposes decoded PCM capture, reusable audio frames, FFT processing, and configurable visualization elements. Its Android SDK 28 application shell and old playback dependencies require replacement or porting. No current video exporter was found in that tree; export is a required new subsystem.

Three approaches were considered:

| Approach | Tradeoff | Decision |
| --- | --- | --- |
| Modern shell and media services around adapted Avee visualizer components | Retains useful Avee foundations while allowing a cohesive new product. Requires clear renderer and scene interfaces. | Selected. |
| Port the entire old application and then redesign every screen | Initially preserves more old structure, but carries older UI and playback dependencies through the migration. | Not selected. |
| Entirely independent application without Avee source reuse | Full implementation control, but discards the source foundation the owner chose. | Not selected. |

The protected/obfuscated uploaded APK is a read-only investigation reference, not the source of the new application. Feature parity is defined by the explicit acceptance requirements below rather than assumed from either Avee version.

## 3. Application experience

The main destinations are Library, Studio, Practice, and Exports. The visual language uses a dark working canvas, strong contrast for notes, clear typography, direct manipulation, and a compact transport bar. Color is accompanied by note labels and shapes so musical information remains readable without color discrimination.

- **Library:** open files or folders through Android's file picker; browse available local audio, search, manage a queue and playlists, and resume the last session.
- **Studio:** choose a track and preset, preview the composition, arrange layers, change their transforms and appearance, and bind supported properties to audio or note activity.
- **Practice:** display the note timeline and keyboard, select a useful register, slow playback while preserving pitch, set A/B loop points, and inspect or correct detected notes.
- **Exports:** select video dimensions, frame rate, clip range and destination; monitor a real export; open or share completed files.

The default workflow is: choose music → analyze once → inspect notes → edit the visualizer → preview → practice or export. Spectrum-only compositions can preview while note analysis is pending. A note-based composition clearly shows analysis progress and does not invent note data.

V1 is offline for playback, analysis, editing, pack exchange, and export after installation. The model is packaged with the application. A remote account, paid API, or cloud processing service is not required.

## 4. Musical analysis and instrument following

### 4.1 Analysis before playback

Analyze selected audio locally in bounded windows and cache timestamped results. This allows upcoming notes to be visible, avoids running heavy transcription on the render thread, and gives preview and export the same musical data.

Spotify Basic Pitch's supplied TensorFlow Lite model is the initial polyphonic-analysis candidate. Its implementation supports multiple pitches and supplies note/onset/contour outputs. The reference preprocessing uses mono audio resampled to 22,050 Hz, and the note representation covers the 88 piano pitches starting at A0. Android inference and postprocessing must be compared with the pinned upstream reference before the detector is considered integrated.

Use the bundled LiteRT Interpreter-compatible CPU runtime first. CPU operation is the required baseline; optional delegates cannot be a condition for basic operation. Model bytes, their SHA-256, source version, notices, and preprocessing/postprocessing versions are recorded with every analysis. Model operator compatibility and native-library alignment are verified in the Android build.

The detector runs separately from the renderer and player. Cancellation, process interruption, source-file changes, and analysis failure are explicit job states. Partial analysis is not marked complete.

### 4.2 Musical data model

A note event contains a stable ID, MIDI pitch, source-audio start/end times in microseconds, amplitude, model activation score, optional pitch-bend information, and provenance. Activation scores are confidence cues, not calibrated probabilities.

Raw estimates are retained. User corrections are stored separately and can change pitch, onset, duration, or inclusion, with undo for an editing session. Preview, practice, video output, and note exports consume the same effective event sequence after applying corrections.

Concert pitch is the default, with A4 = 440 Hz for note naming. The twelve-node wheel folds octaves into pitch classes; the keyboard and piano roll preserve octaves. Sharps/flats and written-instrument transposition affect display separately from sounding pitch. Exported MIDI retains sounding pitches. Practice speed changes time mapping while keeping the original musical pitch.

Derived chord labels start with major/minor triads and require sufficient evidence. Ambiguous frames display no confident chord label. Note activity and chord estimation remain separate so a guessed chord does not manufacture notes.

### 4.3 Practical follow-along tools

V1 includes a scrolling piano roll, current/next-note names and octaves, highlighted keyboard, register filtering, 0.5×–1.5× practice speed, A/B looping, note correction, and MIDI/CSV export.

MIDI exports describe the inferred or corrected performance; they do not claim an original score or instrument arrangement. A register filter is not source separation. Automatic assignment of every note to a particular instrument and automatic guitar fingering are outside the first release.

Basic Pitch's upstream documentation says it works best on one instrument at a time. Dense mixes containing drums, vocals, overlapping instruments, reverb, or distortion are therefore labeled estimated transcriptions. The product must offer correction and uncertainty cues, and must not promise perfect notes from every song. A simple chroma display cannot substitute for this engine.

## 5. Visualizer engine and editor

The public renderer contract is conceptually: render a scene at source-audio time T using the corresponding musical/audio features. It does not depend on wall-clock time, screen refresh count, or an independently advancing particle simulation.

Retain useful Avee scene and rendering concepts behind adapters. The modern scene model owns layer IDs, ordering, transforms, colors, assets, effect settings, and bindings. Adapted upstream files retain their attribution and identify local modifications.

Required built-in visualizer elements are:

- Twelve-note wheel with active-node glow and optional chord links.
- Octave-aware keyboard/piano-roll elements.
- Spectrum bars/lines/circles and waveform displays.
- Image/background, text/track metadata, simple shapes, particles, and glow/blur effects.

The editor supports layer add/delete/reorder, visibility, position/size/rotation, colors, supported audio/note bindings, and saving a composition as a reusable preset. Native Blazing features are represented in the portable scene model.

A single renderer is used for the live GL surface and the offscreen export target. Random effects use a stored seed and timestamp-derived state so seeking and video export reproduce the same scene. Expensive analysis and file decoding run outside the UI/render thread.

## 6. Visualizer packs: what plugin import/export means

In V1, a visualizer plugin means a portable visualizer preset pack: a scene, parameters, assets, metadata, and required renderer features. Importing it adds an editable visualizer. Downloaded Android executable code is not part of this format.

### Native format

Use the extension .blazeviz for a ZIP package containing:

- manifest.json: schema/format version, pack identity, author, title, required features, scene entry point, asset list and checksums.
- scene.json: layer definitions, settings, bindings, and deterministic seeds.
- assets/: the images and other supported visual resources required by the scene.
- Optional thumbnail and attribution files.

A pack contains no source song by default. Import validates its schema, supported features, archive paths and resource bounds before installing it. Newer incompatible packs produce a useful compatibility message. Export embeds required local assets so sharing does not depend on private file paths. Native import → edit → export → reimport must preserve supported settings and appearance.

### Avee compatibility

Import .viz and legacy .json through a version-aware conversion adapter. The initial supported set covers audio provider settings, standard compositions, image/text, supported spectrum/waveform segment paths, and implemented particle/blur settings. The exact supported property set is documented and tested with versioned fixtures.

Unknown elements or properties are reported before conversion is accepted. The original imported file is preserved. Partial conversion is visibly identified, with unsupported features listed; the app does not advertise universal Avee compatibility.

Native .blazeviz is the full-fidelity export format. An Avee-compatible .viz export is offered only for a scene whose complete feature set can be represented by the verified target Avee format. Blazing note-wheel, piano-roll, or other unsupported bindings produce an explicit explanation instead of a falsely compatible .viz file.

The supplied APK does not grant blanket compatibility knowledge about every existing .viz pack. Compatibility claims require fixture and visual checks against the corresponding Avee version.

## 7. Video export

Video export is required for the first complete release. A working preview or screen recording does not satisfy this requirement.

Use a shared timestamp-driven OpenGL renderer connected to a MediaCodec encoder surface, with an AAC audio path and MP4 muxing. Use Media3 for modern playback and supported media processing where it fits this contract. No second renderer or cloud render service is introduced.

Required output presets are 720p and 1080p, landscape 16:9, portrait 9:16, and square 1:1, at 30 fps. Offer 60 fps only when the selected codec and dimensions pass capability checks and acceptance tests. Unsupported settings produce an actionable choice of supported settings.

Output includes the selected audio clip and the composition at matching source-audio timestamps. Frame presentation times are generated from the requested frame rate. Scene time advances from source media time, not processing speed. Practice speed/loop controls do not silently alter the Studio export; video output uses the explicit clip range at original playback speed.

Exports show progress and cancel controls and use version-appropriate foreground execution. An interrupted job is marked interrupted and can restart; partially written files are never presented as finished exports. Handle unavailable content permissions, missing assets, full storage, encoder errors, and unsupported inputs without losing the saved project.

An export is complete only after the MP4 has finalized successfully. Reported resolution, frame rate, audio presence, duration, and destination must describe the produced file.

## 8. Platform and internal boundaries

Initial platform target: Android 8.0/API 26 and later, with Android 16 behavior support. Ship arm64-v8a; use x86_64 for emulator validation. The build must satisfy Android native-library page-size requirements for supported devices.

Use Kotlin and Jetpack Compose for the new UI, AndroidX Media3 for playback/session integration, local persistence for projects and jobs, and the bundled inference runtime. Freeze compatible stable toolchain/library versions in the implementation plan and lock the build inputs. The official Media3 release page inspected on 22 October 2026 lists 1.11.1 as stable; artifact resolution still has to be verified by a build.

Keep the project a single Android application initially, with clear package boundaries rather than many deployment units:

| Boundary | Owns | Consumes |
| --- | --- | --- |
| Playback | Local playback, media session, queue, practice clock | Source URI and playback settings |
| Analysis | PCM preprocessing, model inference, events, corrections, cache | Source audio and model/parameter version |
| Scene/render | Composition model, layer editor bindings, preview/export frames | Scene, source time and features |
| Packs | Native packaging and explicit Avee conversion | Scene/assets and compatibility definitions |
| Export | Encoder, audio timeline, muxing and job states | Shared renderer and source audio |
| UI/persistence | Navigation, project state, local jobs, user actions | The above operations and their states |

Projects store source references, scene, analysis identity, edits, and export settings. Analysis caches are keyed by source content identity, model hash, parameters, and schema version. Changed or revoked source files cannot silently reuse unrelated cached notes.

## 9. Delivery structure

This product has three connected work packages with shared acceptance evidence:

1. Modern player/studio shell and deterministic scene/render contract.
2. Real note analysis plus musician-facing Practice behavior.
3. Visualizer-pack compatibility and video-export completion.

The first end-to-end proof must take a local track through actual note analysis, render the wheel and keyboard, export a playable MP4, and round-trip a native visualizer pack. It should exercise the product's essential path before broad preset parity work.

This specification defines the complete requested target. Intermediate builds must identify missing requirements and remain labeled preview while any required end-to-end behavior is absent.

## 10. Acceptance and evidence

The following are requirements and design targets, not results already achieved.

| Area | Acceptance evidence |
| --- | --- |
| Build/install | Reproducible CI debug/preview APK; successful install and launch on supported Android versions, including Android 16. |
| Actual Avee basis | Pinned upstream provenance, attribution, and identifiable adapted source components; new UI and modern media path documented. |
| Playback | Local supported-format files, queue, background controls, pause, seek, track changes and revoked permission handling. |
| Note semantics | Fixture checks for pitch/octave labels, onsets/durations, correction precedence, display transposition, and MIDI/CSV round-trip semantics. |
| Inference parity | Android model/postprocessing compared against saved outputs from the pinned upstream reference, including overlap boundaries and end-of-file padding. |
| Detection quality | Frozen, annotated isolated-instrument fixture set with exact pitch and ±50 ms onset matching; raw, uncorrected note-onset F1 target of at least 0.80. Manual correction cannot be used to meet this detector target. Hold-out mixed-track results reported separately, with uncertainty visible. |
| Silence and percussion | Silence produces no sustained note/chord output; percussion-only false positives are measured and reported against fixed fixtures. |
| Follow-along | Future/current notes visible; 0.5×/1×/1.5× playback and A/B loops preserve pitch and align the displayed note time within 50 ms of the chosen playback clock. |
| Preview/export | Same scene and timestamp produce visually matching frames within documented GPU tolerance, including seeded effects and seeking. |
| MP4 output | 720p/1080p and required aspect ratios pass metadata inspection and playback; audio/video alignment within 50 ms and duration difference within one video frame or one encoded audio frame, whichever is larger. |
| Native packs | Import/export/reimport of the full required layer set preserves settings/assets and passes visual comparisons. Malformed or unsupported packages fail clearly. |
| Avee packs | Versioned conversion fixtures and explicit per-property compatibility records; unsupported effects are reported rather than silently omitted. |
| Runtime | On a documented arm64 test device, a five-minute 1080p/30 preview and full-track export complete without crash or out-of-memory failure. Analysis speed, peak memory and thermal behavior are measured. |
| Release contents | APK, source revision/archive, SHA256SUMS, model/runtime versions, notices, tested-device list, quality results and known limitations. |

If a detector fails the isolated-instrument quality target, changing a label or substituting spectrum bars does not close the requirement. Review model choice/preprocessing or the product quality target explicitly. Fixture thresholds cannot be tuned only against the reported acceptance set.

A successful build alone does not establish note accuracy, export correctness, preset compatibility, or device performance. Physical-device evidence and automated results must be distinguished.

## 11. First-release scope boundary

Required in the first complete release: original modern Android experience; local player; editable core visualizers; real note analysis; practice view; note correction and MIDI/CSV output; native pack import/export; the tested Avee compatibility subset; and actual video export.

Microphone/live-instrument transcription, instrument stem separation, sheet-music engraving, guitar fingering generation, executable third-party plugins, a plugin marketplace, cloud accounts, desktop editions, and automatic support for every proprietary Avee effect are separate extensions. The pendulum grid in the second reference reel is a future preset, not a prerequisite for the requested note-following path.

## 12. Primary references and evidence boundary

- Avee source baseline: https://github.com/Azy-Kun/AveeOpenPlayer_1.0.34/tree/c909d8b50dcabb5d2b54dc1bfd72f9431cdd7af6
- Avee source license: https://github.com/Azy-Kun/AveeOpenPlayer_1.0.34/blob/c909d8b50dcabb5d2b54dc1bfd72f9431cdd7af6/LICENSE
- Basic Pitch source snapshot: https://github.com/spotify/basic-pitch/tree/fa5997af0a8210982619003269994a1be25eddf3
- Basic Pitch constants: https://github.com/spotify/basic-pitch/blob/fa5997af0a8210982619003269994a1be25eddf3/basic_pitch/constants.py
- Basic Pitch inference: https://github.com/spotify/basic-pitch/blob/fa5997af0a8210982619003269994a1be25eddf3/basic_pitch/inference.py
- Basic Pitch note postprocessing: https://github.com/spotify/basic-pitch/blob/fa5997af0a8210982619003269994a1be25eddf3/basic_pitch/note_creation.py
- Android media transformations: https://developer.android.com/media/media3/transformer/transformations
- Media3 release notes: https://developer.android.com/jetpack/androidx/releases/media3
- Android model runtime: https://ai.google.dev/edge/litert/android
- Android 16 behavior changes: https://developer.android.com/about/versions/16/behavior-changes-16

The earlier APK/video investigation established a plausible audio-provider integration seam and the desired graphic appearance. It did not produce a runnable modified application. This document establishes a source-built product design for review; no implementation, detector benchmark, export test, or release artifact is claimed by this commit.
