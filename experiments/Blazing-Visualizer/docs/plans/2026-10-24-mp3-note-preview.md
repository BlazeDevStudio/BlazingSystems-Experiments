# MP3 note preview repair

The owner reports that Preview 4 plays music but note-driven visualizers stay idle even after a minute. Three supplied MP3s are for testing only. They remain local; no supplied music, excerpts or decoded PCM may enter GitHub or cloud test jobs.

## Reproduction

- Local signal checks: all three inputs are 44.1 kHz stereo MP3s. Their first ten seconds include detectable harmonic content. The piano track around 5 seconds exceeds the current estimator gate; quiet decay tails do not always exceed it. These checks use FFmpeg and an independent Python detector port, not Android execution.
- Production scheduling was extracted unchanged into `quickPreviewPlayback`. At source `4d8627045c10888e00ea70357941fea49b7d87e7`, run `40044425726` compiled and ran 119 host tests; the new latency regression alone failed. With an explicitly simulated 250 ms startup and 40 ms processing per 46.44 ms source hop, it produced notes but displayed none on 151 checks after startup, restarting the decoder nine times. This demonstrates a scheduling defect; those costs are not a phone measurement.

## Focused correction and checks

1. Stream one quick decoder while the source/profile/playback position version stays unchanged. Bound lookahead through flow backpressure and the existing 96-frame cache. Preserve the 150 ms stale-frame rejection.
2. Restart and invalidate cached preview frames on actual Media3 position discontinuities, including same-second seeks, loops and track changes. Detailed analysis and saved/exported notes stay separate.
3. Test continued visible notes under startup latency, same-second seeks, paused lookahead, source cancellation and EOF.
4. Use an original generated stereo MP3 with a quiet intro and changing chords for Android playback and actual SceneView pixel evidence. No owner-supplied music is embedded in this fixture.
5. Run host/lint/build and API26/API36 checks, inspect the resulting evidence and publish separately as Preview 5 only after success. Keep previous releases and main intact. Do not claim physical-phone success from emulator evidence.

## Remaining acceptance

Actual owner-phone behavior still requires trying the resulting APK. This workstation has no connected adb device and insufficient spare RAM for a usable local emulator. Portable local DSP tooling is being attempted so the exact Kotlin estimator can also be tested with the private MP3s.
