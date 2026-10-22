# Blazing Visualizer click-by-click interaction audit

Source under test: `experiments/Blazing-Visualizer` on `blazing-visualizer`.
The test class `ClickAuditTest.kt` drives actual Compose accessibility semantics through
`performClick`, `performTextInput` and touch injection on the Android emulator.
It does **not** substitute for a physical Android phone or proof of musical accuracy.

| Route | Interaction checkpoints | Evidence |
|---|---|---|
| Library | Open tab; Refresh and Import affordances; search no-match and clear | `navigationPresetPickerEditorAndCanvasArrangement`, `partialImportSearchQueueSortAndPlaylistButtons` |
| Queue | Open tab; sort title A–Z; save playlist; current queue retained | `partialImportSearchQueueSortAndPlaylistButtons` |
| Playlists | Save; test delete confirmation cancellation without losing playlist | `partialImportSearchQueueSortAndPlaylistButtons` |
| Visualizer presets | Open chooser; select Harmonic compass; chooser dismisses | `navigationPresetPickerEditorAndCanvasArrangement` |
| Elements / canvas | Open composition; Arrange preview; tap empty area clears selection; tap active note wheel enables Reset; Done | `navigationPresetPickerEditorAndCanvasArrangement` |
| Practice | Open Practice; set 0.75×; B-flat instrument; Note wheel preset | `practiceSpeedTransposeAndNoteWheelAreClickDriven` |
| Export | Open export; select Portrait; check output dimensions; Separate arrangement; on-canvas editor; Done | `exportOrientationAndSeparateCanvasLayoutAreClickDriven` |
| Import fault isolation | Supply one valid WAV and one inaccessible URI; valid file still enters Library and Queue | `partialImportSearchQueueSortAndPlaylistButtons` |
| Storage permissions | Deny first request; Library remains navigable; refresh/regrant; OS dialog click required on modern Android; API26 CI only uses shell fallback if OS installer is broken | `MusicPermissionTest` |
| Tuner, actual MIDI output, real MP4, model inference, background/resume | Native feature tests + physical follow-up needed; **not** claimed by this click audit | `NativeAcceptanceTest`, `PlayerAndUiTest` |

## Status

**Changes committed; verification is pending at time of writing.** Do not convert the matrix to PASS
until the exact GitHub Actions Android 26 + Android 36 jobs and host build complete. The earlier
Preview 2 CI APK is not a stable release. The owner-requested video tracing renderer remains last,
after the non-video-renderer APK is delivered and accepted.
