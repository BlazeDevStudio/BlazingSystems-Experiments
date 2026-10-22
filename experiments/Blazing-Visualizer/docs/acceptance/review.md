# Review and decisions

A fresh whole-branch review of `bb86af8…532ec1b` found no Critical issues, six Important issues and three Minor issues. The Important fixes are in one implementation pass; all related host and native UI/queue regressions pass. Final audio-export revalidation is running.

| Finding | Fix and regression |
|---|---|
| Skipped tracks during analysis retain old notes | TrackCoordinator follows the actual playback URI while analysis is running; host regression observed RED→GREEN. |
| Removed queue items still play | PlayerController removes the Media3 item as well as the stored/UI queue. The device regression first played the removed B item instead of C, reproducing the finding. Device queue regression now passes, as do the three UI/player checks. |
| Concurrent library saves share a temporary file and finish out of order | Unique atomic temporary files; one ordered snapshot channel for project, scene, presets, queue and playlists; surfaced write failures. Concurrent-write host regression observed RED→GREEN. |
| An old correction dialog mutates a new track | Dialog drafts carry project/source identity; the edit reducer rejects stale submissions. Project and changed-content regressions observed RED→GREEN. |
| MP4 finalization failures can look successful | Propagate a successful-path muxer stop failure; retain cancellation/primary failure with cleanup errors suppressed. Fault-injection regressions observed RED→GREEN. |
| Custom presets disappear on switching | Persistent preset collection with Save/update, duplication and automatic retention on switching. Cold-reload and update regressions observed RED→GREEN. |

Seven of eight new host assertions failed before their fixes; all eight pass after the pass. The native queue regression separately reproduced the playback defect. Device testing also caught a progress-render callback reading a newly null value; the callback now captures its non-null composition value. A UI selector ambiguity was corrected in the test.

Deferred minors, exhaustively:

- The layer image-picker target can be lost when rotating while the external picker is open; choose the image again.
- Dismissing/reopening Practice resets its local A/B controls while an existing loop may continue; setting A clears the loop.
- Repeated preset export/reimport grows asset path prefixes and can eventually reach the pack path limit.

Rulings made, exhaustively:

- Build a source-based app with attributed Avee DSP/path components and a familiar workflow. Do not copy the attached proprietary APK's code or assets. Cost if wrong: some proprietary shader/preset behavior needs a future compatible implementation.
- Native BlazeViz packs are the complete interchange format. Avee imports show explicit partial-compatibility reports. Cost: some Avee looks require manual rebuilding.
- Use one deterministic Canvas-to-GL compositor for preview and export, keyed to source timestamps and seed. Cost: this first renderer can use more CPU than dedicated per-element shaders.
- Bundle Basic Pitch and CPU inference for offline operation. Preserve raw estimates separately from edits. Cost: analysis takes time and dense music still needs corrections.
- Bound full-track activation memory by device heap, capped at 30 minutes. Cost: smaller devices require shorter excerpts.
- Use an isolated-attack onset refiner that skips overlapping sustained notes; include its parameters/version in cache identity. Cost: it deliberately leaves some ambiguous attacks unchanged.
- Export original-speed music with sounding-pitch notes; Practice speed and written-instrument transposition affect the guide only. Cost: a slowed practice recording is not an export option in this preview.
- Let the H.264 encoder negotiate profile/level together. A forced profile without a level broke API26 configuration. Cost: codec-specific quality negotiation varies by device.
- Match Python and Android LiteRT at version 1.4 for model parity. Bound cross-platform activation error at 0.001, report every head, and retain exact event-timing and raw-F1 gates. The original 0.00005 budget rejected a 0.000059247 note-activation difference after version matching. Cost: activation differences below 0.001 are accepted and fixture reproduction requires the pinned Python runtime.
- Calibrate AAC encoder priming with a private known prefix, remove that prefix and measured delay, and check decoded audio against the source. Container timestamps alone missed a 93 ms content delay. Cost: each export includes a short calibration/decode step and an encoder that cannot be aligned is rejected.
- Keep this as a debug-signed preview in the existing draft PR; do not merge main or publish to a store. Cost: production signing, physical-device performance and owner familiarity acceptance remain release checks.

Declined-to-judge outcomes: native codecs and lifecycle are evaluated by instrumentation, API36 by CI; physical arm64 performance, arbitrary-song transcription and the owner's acceptance of Avee familiarity are not established by emulator fixtures.
