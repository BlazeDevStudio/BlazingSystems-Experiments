# Playback PCM preview and phone diagnostics

The owner explicitly confirmed that Preview 5 is still blank on their phone. Its successful host/API26/API36 checks do not resolve that report. Preview 5 source is `96c5d3d0bec6f5fad20eb753fea9afdca5d3f8ee`; validation `40053385999`, publisher `40053386012`. Keep that release intact.

The supplied music remains local and strictly for testing. The actual production PcmResampler/LiveNoteTracker classes emitted notes for all three first-15-second clips using local FFmpeg input and a verified portable Java 17 runtime. Each produced 319 feature frames; active-note frames were 313 (beats), 180 (piano), and 133 (vocals). This is not Android playback/display evidence and does not establish transcription accuracy. Do not upload supplied audio, excerpts or PCM to GitHub or cloud tests.

## Implementation

1. Observe PCM actually consumed by the existing Media3 audio sink. Preserve the delegate, session, effects, speed, video behavior and timestamps. Copy only consumed bytes; handle partial writes and output stream offsets. Do DSP off the audio thread, with a bounded channel and generation guards.
2. Prefer these playback features for the preview; use the independent file decoder as fallback. Keep detailed note edits/export analysis independent. Source changes, seeks, resets and profile changes invalidate old playback features.
3. Cache the existing resampler's exact phase coefficients to remove repeated trigonometry, retaining the same filter/output clock. Verify against the uncached calculation, chunk/tail behavior and alias rejection, and rerun the private local DSP benchmark with compiled production code.
4. Add a one-tap Check visualizer action. Report PCM reception, estimated notes, evaluated frames and successful canvas presentations. A bounded file check runs locally. Copy only measurements and device/build details, never audio, filenames or file addresses. Surface GL errors rather than swallowing them.
5. Extend the generated stereo-MP3 Android check to require playback PCM features and real canvas pixels before detailed analysis; exercise diagnostic copy. Navigate before starting playback to remove Compose setup timing ambiguity.
6. Full host/lint/build and API26/API36 verification gates a separately tagged Preview 6. Inspect downloaded artifacts and package identity/hash. A successful emulator run is not an owner-phone pass; if still blank, the copied phone report is required to identify the failing boundary.

## Verification investigation

Candidate `59cf2211` passed the host suite but required a scoped Media3 API opt-in correction for lint. Candidate `f16b5486`, with those annotations, then stalled in the host task in both attempts of run `40066386802` and hit the existing 12-minute limit. The last logged test boundary was AveeCompositionTest; no completed XML report was produced. That does not establish which test or runtime operation was stuck. The production changes and assertions remain unchanged while the workflow adds per-test start/end logging and bounded Java thread/SDK-state snapshots before the same timeout. Both incomplete attempt artifacts remain available.

## Execution result

The diagnostic candidate passed the host suite, then lint identified a direct StateFlow read in the new check dialog. Final source `a718e2a45e798038885a9c52f38a89b5a2f623e5` collects that state reactively. Validation `40085323906` passed 129 host tests / 24 suites, lint/APK, and 31 general + 1 fresh-permission native case on each of API26/API36. Both actual MP3 canvas images show active notes; coverage was 1.0 for both chords, including empty-cache fallback and seeking. Exact-source local DSP retained the measured counts/RMS/pitches for all three supplied clips while reducing resampler work. Single-run total elapsed time improved for two clips and was slightly worse for the beats clip; this is not a phone performance claim.

Publisher `40085323837` produced a separate Preview 6 release, and independently downloaded public bytes matched CI exactly. The owner-phone problem remains unconfirmed until a phone test or copied check report. See [Preview 6 evidence](../acceptance/preview-6-evidence.md) for exact hashes, jobs and measurements.
