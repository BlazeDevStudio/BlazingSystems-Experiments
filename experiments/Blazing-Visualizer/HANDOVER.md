# Blazing Visualizer preview

The Android preview is built, signed, persisted and available in draft PR #133. Source is under `experiments/Blazing-Visualizer` on `blazing-visualizer` in `BlazingSystems/BlazingSystems-Experiments`.

Verified: 45 host tests; all 11 latest native/UI checks; full CI on API26 and API36 at source revision `d87730e552fa2f55727d3b0ac4e47addc89463c8`. The final package adds licenses without changing any of the 17 DEX/native/model entries tested on the device. The corrected UI import-wait test was also rerun separately (4/4). Results, exact raw runs, preview MP4 and the release audit are in `docs/acceptance`.

The AAC regression is fixed using measured encoder priming and explicit tail flushing. Decoded MP4/source correlation: 0.9999358, measured lag: 0 us. All six required 720p/1080p landscape/portrait/square presets and a four-second clip passed. Raw onset F1 was 0.909 on synthetic notes/chord and 1.0 on three recorded-flute attacks; these small fixtures do not establish arbitrary-song transcription quality.

Read `docs/acceptance/review.md` for the exhaustive decisions, costs and three deferred minor issues. Physical arm64 performance, production signing/store publication, and the owner's acceptance of Avee familiarity remain future release checks. This is a debug-signed preview; main has not been merged.

Build: JDK17, SDK36/build-tools36.0.0, `./gradlew :app:testDebugUnitTest :app:lintDebug :app:assembleDebug`. Native validation: `./gradlew :app:connectedDebugAndroidTest`. Test fixtures use bundled fixed references from original Spotify Python processing with LiteRT1.4. Offline APK has no Internet permission.
