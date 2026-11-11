# v0.1.0 test plan, 2026-10-26

## Controlled fixture
- F01-H1: document observer exposes the two rendered fixture messages
- F01-H2: native command has an action ID and appears exactly once in observed fixture DOM
- F01-N1: repeated action ID rejected
- F01-N2: malformed JSON, unsupported action, invalid UUID, blank text, oversized text rejected
- F01-N3: HTML-looking text is handled as text, never parsed into markup
- F01-E1: two rapid mutations coalesce; both messages preserved

`node tests/fixture.test.cjs` executes the fixture script in Node's VM with a minimal controlled DOM model. This is a synthetic harness: **it does not test Chromium, Android, Meta login, or live messages**.

## Android build
`gradle :app:testDebugUnitTest :app:assembleDebug`, verify APK exists and is nonempty, compare SHA-256 between runner and extracted artifact.

## Android emulator smoke (separate acceptance)
Install uploaded debug APK on Android emulator, start MainActivity, assert running process and extract UI dump. Check no startup crash. No real-device acceptance implied.

## Not run / unsupported
Real Facebook messaging, real-account DOM observation, authenticated downloads, weak-network resumption, camera/microphone/calls, background voicemail, file manager edit/move, SD revocation, 100 kbps simulator, physical Android device launch.

## Android bidirectional UI smoke
Script: `python3 ci/emulator_bidirectional.py` runs on an actual Android emulator after the app is installed and the page-to-Compose observation is verified. It discovers Compose input/button bounds using Android UI hierarchy; sends a unique fixed probe, verifies the action yields a new native message bubble **and** `OBSERVED_IN_FIXTURE` status. Do not claim Meta transport or physical device acceptance.
