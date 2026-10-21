# Blazing Visualizer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver an installable Avee-based Android player with familiar Avee interactions, Blazing branding, real note-following, visualizer-pack exchange, and synchronized MP4 export.

**Architecture:** One Android application shares a source-audio timeline between playback, cached analysis, the element editor, the GL renderer, and export. Adapt attributed Avee DSP/path/spectrum components; use a modern player/UI, bundled polyphonic inference, and portable scene data. Work is sequenced as integrated, independently testable slices.

**Tech Stack:** Kotlin 2.3.20, Compose BOM 2025.09.01, AGP 8.13.2, Gradle 8.13, JDK 17, compile/target SDK 36, minimum SDK 26; Media3 1.8.0; LiteRT 1.4.0 Interpreter baseline; kotlinx-serialization-json 1.9.0. Use Kotlin's matching Compose/serialization compiler plugins. These conservative artifact versions were verified at Google Maven/Maven Central on 22 October 2026; a successful dependency resolution/build is still required.

**Spec:** ../specs/2026-10-22-blazing-visualizer-design.md, including the owner's clarification that Avee look, feel, and workflow take priority over the earlier distinct-navigation proposal.

## Global Constraints

- Repository/project root: experiments/Blazing-Visualizer; application ID: com.blazingsystems.visualizer.
- Initial platform target: Android 8.0/API 26 and later, with Android 16 behavior support. Ship arm64-v8a; use x86_64 for emulator validation.
- Preserve recognizable Library/Queue → Visualizer → preset chooser → element/property editor → export interactions.
- V1 is offline for playback, analysis, editing, pack exchange, and export after installation. The model is packaged with the application.
- Avee baseline: c909d8b50dcabb5d2b54dc1bfd72f9431cdd7af6; Basic Pitch baseline: fa5997af0a8210982619003269994a1be25eddf3.
- Preserve upstream notices and file-specific licenses. The NAudio-derived FFT file has an Ms-PL header and must retain its separate license.
- A4 = 440 Hz; MIDI events retain sounding pitch; written-instrument transposition affects display separately.
- Practice speed: 0.5×–1.5×; user corrections remain separate from raw estimated events.
- Required MP4 presets: 720p/1080p, 16:9/9:16/1:1, 30 fps; 60 fps only after capability and acceptance checks.
- Raw isolated-instrument note-onset F1 target: at least 0.80 at exact MIDI pitch and ±50 ms onset; corrections cannot satisfy the raw detector target.
- Preview/guide clock alignment and exported A/V alignment: within 50 ms.
- No finished-release claim from scaffolding, mock data, a successful build, or an untested APK.

## Review Focus

1. Rotation/background transitions while editing or exporting must retain track/composition and cannot lose completed edits. Pin in tasks 1, 6, 7.
2. A source URI may lose permission or refer to changed content; surface a relink/reanalysis state and do not reuse unrelated cached notes. Pin in tasks 1 and 3.
3. A supported-looking imported preset may contain one unknown element or an external asset path; report partial conversion before acceptance. Pin in task 5.
4. Very short audio, tail padding, stereo downmixing, and notes spanning analysis-window boundaries must not shift or duplicate events. Pin in task 3.
5. Seeking backward into particles or a loop must reproduce the same visual and note state instead of retaining future state. Pin in tasks 2, 4, 6.

---

## File map and common contracts

All project-relative paths below start at experiments/Blazing-Visualizer. P means app/src/main/java/com/blazingsystems/visualizer; U means app/src/test/java/com/blazingsystems/visualizer; I means app/src/androidTest/java/com/blazingsystems/visualizer. These aliases are path prefixes only.

- Build/entry: settings.gradle.kts, build.gradle.kts, gradle.properties, gradle/libs.versions.toml, gradle/wrapper/*, gradlew, gradlew.bat, app/build.gradle.kts, app/src/main/AndroidManifest.xml, P/MainActivity.kt, P/ui/BlazingTheme.kt.
- Domain/storage: P/project/Models.kt, P/project/ProjectStore.kt.
- Player/UI: P/playback/PlayerController.kt, PlaybackService.kt, LibraryRepository.kt; P/ui/AveeShell.kt, LibraryScreen.kt, VisualizerScreen.kt, PresetChooserSheet.kt, ElementEditorSheet.kt, PracticeSheet.kt, ExportSheet.kt.
- Source-derived engine: app/src/main/java/com/NAudio/FastFourierTransform.java; app/src/main/java/com/aveeopen/comp/Visualizer/Dsp/DspWindows.java and DspCurves.java; P/avee/AveeCirclePath.kt and AveeSpectrumAnalyzer.kt.
- Rendering: P/render/SceneEvaluator.kt, GlSceneRenderer.kt, GlTarget.kt, GlPrimitives.kt, GlPreviewView.kt, BuiltinScenes.kt, LayerEditor.kt.
- Analysis: P/audio/PcmDecoder.kt, PcmResampler.kt; P/analysis/ModelRunner.kt, BasicPitchAnalyzer.kt, NotePostprocessor.kt, NoteEdits.kt, ChordEstimator.kt, AnalysisRepository.kt; app/src/main/assets/models/nmp.tflite.
- Practice/exported notes: P/practice/NoteNames.kt, PracticeClock.kt, NoteExport.kt.
- Packs: P/packs/VisualizerPack.kt, NativePackCodec.kt, AveePresetAdapter.kt, CompatibilityReport.kt.
- Video: P/export/ExportRequest.kt, VideoExporter.kt, AudioEncoder.kt, Mp4Writer.kt, ExportService.kt, ExportJobStore.kt.
- Evidence/release: tools/reference_analyze.py, tools/build_acceptance_fixtures.py, tools/verify_release.py, tools/requirements-reference.txt, fixtures/*, docs/acceptance/*, THIRD_PARTY_NOTICES.md, licenses/*, README.md, HANDOVER.md.
- CI: repository-root .github/workflows/blazing-visualizer.yml.

Task 1 defines these serializable domain types in Models.kt:
- SourceRef(uri: String, contentSha256: String?, durationUs: Long).
- NoteEvent(id: String, pitch: Int, startUs: Long, endUs: Long, amplitude: Float, activation: Float, provenance: NoteProvenance, bendCents: List<Float>).
- NoteEdit as a sealed Insert/Replace/Delete event operation; replacements carry a complete NoteEvent and preserve the event ID.
- Scene(id: String, layers: List<Layer>, seed: Long); Layer carries ID, element type, visibility, transform, JSON properties, and explicit bindings.
- ElementType: IMAGE, TEXT, SHAPE, SPECTRUM, WAVEFORM, PARTICLES, BLUR, NOTE_WHEEL, PIANO_ROLL.
- FeatureFrame(sourceTimeUs: Long, rms: Float, spectrum: List<Float>, waveform: List<Float>, notes: List<NoteEvent>, chord: String?).
- ExportSettings(width: Int, height: Int, fps: Int, videoBitrate: Int, audioBitrate: Int).
- Project(id: String, source: SourceRef, scene: Scene, analysisKey: String?, edits: List<NoteEdit>, export: ExportSettings).

All times refer to original source audio. Active note intervals are start-inclusive/end-exclusive. Validate MIDI pitch 21..108 for detector events, nonnegative start time, end > start, finite activation/amplitude, unique IDs, and finite scene numeric values. MIDI export may encode manually corrected pitches 0..127; detector-model range remains distinct.

### Task 1: Familiar player shell, persistent project, and a reproducible build

**Files:** Build/entry, domain/storage, player/UI files above through VisualizerScreen; create U/project/ProjectStoreTest.kt, I/ui/AveeWorkflowTest.kt, I/playback/PlaybackTest.kt, and CI workflow. Create README.md and HANDOVER.md within this deliverable.

**Interfaces:**
- PlayerController exposes StateFlow<PlaybackState>, open(uri: Uri), play(), pause(), seekTo(sourceTimeUs: Long), setPracticeSpeed(speed: Float), setLoop(startUs: Long?, endUs: Long?).
- PlaybackState contains sourceTimeUs, durationUs, isPlaying, speed, and an explicit failure state. Media3 speed changes preserve pitch.
- ProjectStore exposes load(id: String): Project?, save(project: Project), list(): List<Project>, using atomic file replacement and content URI references.
- LibraryRepository exposes open(uri: Uri): SourceRef and queue/playlist persistence. Missing/revoked permissions produce a recoverable relink state.

- [ ] **Step 0: Prepare the pinned Android test harness.** Locate/install JDK 17 and SDK 36, add the pinned Gradle wrapper/build/test configuration, and verify ./gradlew --version plus SDK availability. Keep feature behavior absent until the following failing tests are written.
- [ ] **Step 1: Write failing tests** for an atomic project round-trip, a simulated interrupted write retaining the previous project, a revoked URI producing relink, and the user path through Library/Visualizer/preset/editor/export actions.
~~~kotlin
assertEquals(project, store.load(project.id))
onNodeWithContentDescription("Choose visualizer").performClick()
onNodeWithText("Presets").assertIsDisplayed()
onNodeWithContentDescription("Edit visualizer").assertExists()
onNodeWithContentDescription("Export video").assertExists()
~~~
The test supplies a generated local WAV URI, plays actual audio, seeks, and verifies player state. Intercept the system picker only to provide this fixture.
- [ ] **Step 2: Run** ./gradlew :app:testDebugUnitTest :app:connectedDebugAndroidTest; confirm new behavior fails before implementing it, not because an unrelated SDK is missing.
- [ ] **Step 3: Implement** the declared models, player/service, persisted URI handling and familiar shell; add notification/media-session controls. Configure the pinned build, debug APK, instrumented tests, and project-specific CI paths. Obtain wrapper binaries/checksums from the official Gradle distribution. Preserve project state across recreation.
- [ ] **Step 4: Verify** ./gradlew :app:testDebugUnitTest :app:lintDebug :app:assembleDebug and the three new instrumented test classes on API 26 and 36. An actual player works even before later visual elements arrive.
- [ ] **Step 5: Commit** feat(blazing-visualizer): add familiar player shell and project persistence.

### Task 2: Attributed Avee DSP and shared deterministic visualization

**Files:** Source-derived engine/rendering paths above; modify VisualizerScreen.kt and Models.kt only if an explicitly documented missing field is needed. Create U/render/SceneEvaluatorTest.kt, U/avee/AveeSpectrumAnalyzerTest.kt, I/render/RenderParityTest.kt and required license files.

**Interfaces:**
- AveeCirclePath.points(count: Int, radius: Float): List<Vec2>; C/the first point is at the top.
- AveeSpectrumAnalyzer.analyze(pcm: FloatArray, sampleRate: Int): SpectrumFrame, with RMS, spectrum and waveform output.
- SceneEvaluator.evaluate(scene: Scene, features: FeatureFrame, sourceTimeUs: Long): EvaluatedScene.
- GlTarget.pbuffer(width: Int, height: Int) and GlTarget.encoder(surface: Surface, width: Int, height: Int); targets own their EGL lifecycle and expose readPixels(): ByteArray for tests.
- GlSceneRenderer.render(scene: EvaluatedScene, target: GlTarget); same implementation serves preview and export.
- BuiltinScenes.defaultSpectrum(): Scene and noteWheel(): Scene; LayerEditor.apply(scene: Scene, command: LayerCommand): Scene.

- [ ] **Step 1: Write failing tests** for a known tone's spectral peak within one FFT bin, 12 distinct circle points, start/end note boundaries, and same-timestamp seek/replay equivalence.
~~~kotlin
assertEquals(12, AveeCirclePath.points(12, 1f).distinct().size)
assertEquals(frameAtOneSecond, evaluatorAfterBackwardSeek)
~~~
Render parity compares the same scene/time in independent pbuffer targets on one device with a documented pixel tolerance, not cross-device byte identity.
- [ ] **Step 2: Run** ./gradlew :app:testDebugUnitTest --tests '*SceneEvaluatorTest' --tests '*AveeSpectrumAnalyzerTest'; confirm the new assertions fail.
- [ ] **Step 3: Implement** the pinned source ports, preserving headers and original FFT file/license. Adapt spectrum/path algorithms to the new typed interfaces. Implement images/text/shapes, bars/lines/circles, waveform, deterministic particles, blur/glow, note wheel and piano roll. Time/seed derive effects without mutable future state. Record each imported source path and upstream blob identity in THIRD_PARTY_NOTICES.md.
- [ ] **Step 4: Verify** unit tests and RenderParityTest, including landscape/portrait/square, zero-size surface recovery, layer visibility/order, and backward seeking. Full preview uses actual decoded audio features.
- [ ] **Step 5: Commit** feat(blazing-visualizer): port Avee visualization primitives and shared renderer.

### Task 3: Real polyphonic inference, event timing, and cache correctness

**Files:** Audio/analysis paths above; tools/reference_analyze.py, tools/requirements-reference.txt, app model asset and notices, fixtures/model-parity/*; create U/analysis/NotePostprocessorTest.kt, U/analysis/AnalysisRepositoryTest.kt, U/audio/PcmResamplerTest.kt, I/analysis/ModelParityTest.kt.

**Interfaces:**
- PcmDecoder.decode(uri: Uri): Flow<PcmChunk>; PcmChunk carries interleaved samples, source sample rate/channels and timestamp.
- PcmResampler.toMono22050(chunks: Flow<PcmChunk>): Flow<FloatArray> implements bounded, stateful reference-compatible preprocessing.
- ModelRunner.run(window: FloatArray): ModelOutputs; expose onset/note/contour tensors by signature, never guessed tensor order.
- suspend BasicPitchAnalyzer.analyze(source: SourceRef, progress: (Float) -> Unit): AnalysisResult.
- NotePostprocessor.decode(outputs: List<TimedModelOutputs>, durationUs: Long, parameters: AnalysisParameters): List<NoteEvent>.
- applyNoteEdits(raw: List<NoteEvent>, edits: List<NoteEdit>): List<NoteEvent>; ChordEstimator.estimate(notes: List<NoteEvent>, sourceTimeUs: Long): String?.
- suspend AnalysisRepository.getOrAnalyze(source: SourceRef, parameters: AnalysisParameters): AnalysisResult. Cache key includes full source hash, model hash, parameters and schema version.

- [ ] **Step 1: Write failing tests** for 22.05 kHz mono preprocessing, sub-window input/tail padding, window-boundary events without duplication, no notes from silence, corrections preserving raw events, cancellation, and changed-source invalidation.
~~~kotlin
assertEquals(1, events.count { it.pitch == 60 && it.startUs == expectedOnsetUs })
assertTrue(silentEvents.isEmpty())
assertNotEquals(keyForOriginal, keyForChangedSource)
~~~
Generate reference tensors/events with the pinned upstream Python implementation on Python 3.11; do not create expected values with the Android algorithm being tested.
- [ ] **Step 2: Run** the analysis/resampler test classes and ModelParityTest; confirm the actual model/event interfaces are absent or incorrect before implementation.
- [ ] **Step 3: Implement** streaming decode/resample, bundled nmp.tflite from the pinned upstream path, verified model SHA-256, reference overlap/padding/time conversion, onset/frame postprocessing, separate raw/edit persistence, chord confidence and job states. Port the reference alignment correction explicitly. Use CPU inference first and keep disk/audio/ML off the UI/render threads.
- [ ] **Step 4: Verify** Python/Android tensor tolerance of maximum absolute difference 1e-3 on fixed windows; compare final event pitch and timing within one reference output frame. Check all native PT_LOAD alignments are at least 16 KiB and verify packaged native library alignment. A compatibility failure blocks this task and requires an explicit runtime correction, not dummy note output.
- [ ] **Step 5: Commit** feat(blazing-visualizer): add cached on-device polyphonic note analysis.

### Task 4: Musician-facing Practice, corrections, and note export

**Files:** Practice paths, PracticeSheet.kt; modify VisualizerScreen.kt and player clock integration. Create U/practice/NoteNamesTest.kt, PracticeClockTest.kt, NoteExportTest.kt and I/ui/PracticeFlowTest.kt.

**Interfaces:**
- NoteNames.name(midiPitch: Int, preferFlats: Boolean, displayTranspose: Int): String.
- PracticeClock.sourceTimeUs(playerState: PlaybackState): Long; display follows the player's source clock, including looping and seeking.
- NoteExport.writeMidi(events: List<NoteEvent>, output: OutputStream) and writeCsv(events: List<NoteEvent>, output: OutputStream).
- PracticeSheet receives the active Project, AnalysisResult and PlayerController; uses applyNoteEdits from task 3 rather than maintaining a second transcription.

- [ ] **Step 1: Write failing tests** for A4/C5 naming, B-flat instrument display versus unchanged sounding-pitch MIDI, interval ends, backward seek and loop reset, and correction/export consistency.
~~~kotlin
assertEquals("A4", NoteNames.name(69, false, 0))
assertEquals("B4", NoteNames.name(69, false, 2))
assertEquals(69, independentlyParsedMidiPitch)
~~~
Parse exported MIDI independently with the Python mido library in a fixture check. Verify CSV quotes/newlines and microsecond timing.
- [ ] **Step 2: Run** the three unit classes and PracticeFlowTest; confirm the new behavior fails.
- [ ] **Step 3: Implement** scrolling upcoming/current notes, octave keyboard/piano roll, register filter, 0.5×–1.5× controls, A/B loop points, edit/add/remove note operations and session undo. Show activation/estimated status without treating it as a calibrated probability. MIDI remains concert pitch.
- [ ] **Step 4: Verify** a known progression at 0.5×/1×/1.5×, seeking backward and looping; note clock must match source playback within 50 ms. The user can play along and can export the corrected sequence.
- [ ] **Step 5: Commit** feat(blazing-visualizer): add instrument practice and MIDI CSV output.

### Task 5: Visualizer packs, compatible Avee import, and element editing

**Files:** Pack paths, PresetChooserSheet.kt and ElementEditorSheet.kt; fixtures/packs/* and docs/acceptance/avee-compatibility.md. Create U/packs/NativePackCodecTest.kt, AveePresetAdapterTest.kt, I/ui/PresetEditingTest.kt.

**Interfaces:**
- NativePackCodec.read(input: InputStream, destination: File): ImportResult and write(pack: VisualizerPack, assets: AssetResolver, output: OutputStream).
- AssetResolver.open(relativePath: String): InputStream; pack files stream to bounded staging storage instead of loading every asset into memory.
- AveePresetAdapter.import(input: InputStream, filename: String, destination: File): ImportResult.
- CompatibilityReport contains supported/unsupported elements/properties, missing assets, target format version and whether explicit partial-conversion acceptance is required.
- AveePresetAdapter.export(scene: Scene, assets: AssetResolver, output: OutputStream): CompatibilityReport; emits .viz only if the complete scene is representable.
- LayerCommand supports add/remove/reorder/visibility/transform/property/binding changes through task 2's LayerEditor.

- [ ] **Step 1: Write failing tests** for full native round-trip, relative embedded assets after moving the pack, unknown schema versions, archive traversal/oversize limits, and a single unsupported Avee element.
~~~kotlin
assertEquals(originalScene, reimportedScene)
assertTrue(report.requiresPartialAcceptance)
assertFalse(report.unsupportedProperties.isEmpty())
~~~
Use original synthetic scene fixtures; establish .viz container/scene names through documented format observations before claiming interoperability. Preserve each fixture's provenance.
- [ ] **Step 2: Run** NativePackCodecTest and AveePresetAdapterTest; confirm all new behaviors fail.
- [ ] **Step 3: Implement** schema-1 .blazeviz manifests/scenes/assets/checksums, transactional imports, preserved original Avee files, explicit conversion warnings, and the editor/chooser actions. Bound archives to 64 MiB input, 128 MiB expanded, 1,024 entries, and 4,096-pixel image edges; explain these limits in the import error. Record every supported Avee property and target version. Notes/unsupported bindings block misleading Avee export.
- [ ] **Step 4: Verify** import → choose → edit → export → reimport in PresetEditingTest, including image/text, bar/line/circle, waveform, particles, blur, note wheel and piano roll. Run visual comparisons for each supported Avee fixture and report unsupported features before applying conversion.
- [ ] **Step 5: Commit** feat(blazing-visualizer): add portable packs and verified Avee conversion.

### Task 6: Actual synchronized MP4 export

**Files:** Video paths and ExportSheet.kt; modify manifest for version-appropriate foreground execution; create U/export/ExportTimelineTest.kt, I/export/Mp4ExportTest.kt, ExportFailureTest.kt; fixtures/video/*.

**Interfaces:**
- ExportRequest(project: Project, clipStartUs: Long, clipEndUs: Long, outputUri: String, settings: ExportSettings).
- VideoExporter.export(request: ExportRequest, onProgress: (Float) -> Unit): ExportResult, plus cancel(jobId: String).
- Frame source time = clipStartUs + floor(frameIndex * 1_000_000 / fps); encoder PTS starts at zero.
- AudioEncoder uses original source-audio range at original speed. Mp4Writer owns finalized muxing and codec-delay/timestamp handling.
- ExportJobStore persists QUEUED/RUNNING/COMPLETED/CANCELLED/INTERRUPTED/FAILED; a partial MP4 cannot enter COMPLETED.

- [ ] **Step 1: Write failing tests** for exact rational frame timestamps, final frame/clip boundaries, codec capability rejection, cancellation/storage failure, process restart state, and generated MP4 stream inspection.
~~~kotlin
assertEquals(1_000_000L, sourceTimes[30] - sourceTimes[0])
assertFalse(interruptedJob.isCompleted)
assertEquals(2, inspectedStreams.size)
~~~
Use a known note/chirp fixture and cached real analysis. Extract MP4 frames/audio for independent FFprobe/FFmpeg checks.
- [ ] **Step 2: Run** ExportTimelineTest, Mp4ExportTest and ExportFailureTest; require actual missing export to fail, not a mocked success callback.
- [ ] **Step 3: Implement** the MediaCodec encoder surface through GlTarget.encoder and task 2's renderer; add AAC encoding and MP4 muxing, progress, cancel, foreground notification, capability checks and interrupted-job recovery. Practice controls do not silently change output rate. Finalize the destination only on muxer success.
- [ ] **Step 4: Verify** every 720p/1080p × 16:9/9:16/1:1 preset at 30 fps. Measure A/V offset ≤50 ms and stream duration difference ≤max(one video frame, one encoded audio frame). Compare exported frames to preview at the same timestamps, including backward-seek seeded effects. Verify a full track and open/share the actual MP4.
- [ ] **Step 5: Commit** feat(blazing-visualizer): add synchronized MP4 video export.

### Task 7: Accuracy, runtime, and familiar-workflow acceptance

**Files:** tools/build_acceptance_fixtures.py, fixtures/notes/manifest.json, docs/acceptance/note-quality.md, runtime.md, avee-workflow.md; create I/acceptance/EndToEndTest.kt and I/acceptance/NoteQualityTest.kt. Fix owning feature files only for demonstrated failures.

**Interfaces:** Frozen fixture manifest identifies source hash/license, expected note events, instrument/mix category, split and matcher parameters; evaluator reports precision, recall, onset F1, timing error and false positives. EndToEndTest uses public interfaces from tasks 1–6.

- [ ] **Step 1: Write failing acceptance checks** for raw isolated-instrument F1 ≥0.80 at exact pitch/±50 ms; separate synthetic, isolated real-instrument, percussion and mixed-track scores. Freeze/version fixtures before tuning; record original generated-signal fixtures separately from licensed recordings. Test cache invalidation and a five-minute scene session with orientation/background changes.
~~~kotlin
assertTrue(rawIsolatedInstrumentOnsetF1 >= 0.80)
assertTrue(avOffsetUs <= 50_000L)
assertTrue(allRequiredNativeElementsRoundTrip)
~~~
No score is reported for a fixture category that was not actually evaluated.
- [ ] **Step 2: Run** the acceptance suite; retain the failing baseline and reproduce actual defects with the systematic-debugging skill before changes.
- [ ] **Step 3: Implement fixes** to inference/clock/render/import/export behavior identified by evidence. Exercise the familiar Avee path on API 26 and 36; preserve track/composition when switching preset/editor/Practice/export. Do not lower the detector target or hide unsupported effects without owner-visible scope review.
- [ ] **Step 4: Verify** the complete suite and a documented arm64 device: five-minute 1080p/30 preview, full-track MP4 export, peak memory, analysis speed and thermal behavior. Record emulator evidence separately; owner acceptance of Avee look/feel remains a device review item.
- [ ] **Step 5: Commit** test(blazing-visualizer): record end-to-end quality and runtime acceptance.

### Task 8: Installable preview artifacts and maintainable handover

**Files:** CI workflow, tools/verify_release.py, README.md, HANDOVER.md, docs/acceptance/release-matrix.md, THIRD_PARTY_NOTICES.md.

**Interfaces:** verify_release.py accepts APK, source revision, test-result directory and output directory; exits nonzero for missing required evidence/checksum mismatch. Emits a manifest recording source/model/runtime identities, APK package/version/signing-certificate digest, test categories and outstanding device checks.

- [ ] **Step 1: Write failing release checks** for a missing APK, stale source SHA, checksum mismatch, absent note/export/pack evidence, and inaccurate completed/preview status.
- [ ] **Step 2: Run** python tools/verify_release.py against deliberately incomplete input and confirm a nonzero exit.
- [ ] **Step 3: Implement** project-scoped CI that runs JVM/lint/build and emulator acceptance, then uploads the installable debug preview APK, source archive, test reports, notices, manifest and SHA256SUMS. Record debug signing honestly; production signing is a separate release operation. No placeholder binary or renamed unrelated APK is allowed.
- [ ] **Step 4: Verify** downloaded artifacts/checksums, install the generated APK, run the local-track → detected notes → pack round-trip → MP4 path, and check package/version/source identities. README has concise setup/use steps; HANDOVER has exact continuation commands and remaining evidence.
- [ ] **Step 5: Commit** build(blazing-visualizer): package verified preview artifacts and handover.

## Plan self-review and execution handoff

Coverage: spec sections 1–3 map to tasks 1/2/5/7; note engine and Practice to 3/4/7; rendering to 2/6; packs to 5; video to 6; platform/persistence to 1/3/6; acceptance/delivery to 7/8. Every Review Focus condition has an owning test. Interface names and source-time units are shared, and all files are assigned above.

Run every task's failing/passing cycle, update checkboxes and HANDOVER.md at each completed task, and preserve actual failure evidence. Implementation runs only after this written plan is reviewed and an execution method is chosen.

Recommended execution method: Native, with this agent implementing sequentially in the current session, followed by the fresh whole-branch review required by the execution workflow. The player, scene, analysis and export tasks share interfaces and a single media clock. A delegated execution method remains available if the owner chooses it; no subagents have been started.

Current status: plan prepared for review; no application code, APK, or measured quality/export result exists yet.
