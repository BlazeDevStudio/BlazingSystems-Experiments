# Replica Diff — Blaze vs official Avee feature set

Checked on 2026-10-23. Baseline: official https://aveeplayer.com/ publicly described feature set. Clone evidence: first-party source + Android CI reports on `blazing-visualizer`. No current-version competitor screenshots or legitimate .viz sample collection is available, so **numerical pixel parity and complete behavioral parity are not measurable** and no invented score is reported.

**Core parity blocked:** Full Avee .viz renderer/animations, folder browsing, equalizer, device-control acceptance, and accurate playable/export parity. Continuous playback is in Media3 source but actual physical-device resilience remains untested. User-only features (live musical notes/chords) are independent additions, not evidence of Avee parity.

**Verified vs planned:** source presence ≠ runtime pass. Host build/tests passed in run 39880221516; API26 and API36 instrumented suites failed as documented in `replica/bugs.md`. Physical device, screenshot-state and audio output comparisons: NOT RUN. Must-have defects B01–B04 mean no shippable or parity verdict.

**REA boundary:** Private REA plugin integration is installed, but its `rea-agents@6.7.0` local stdio MCP engine is not connected; no modern Avee code, binary, resource, API or signal-processing algorithm was extracted. Use authorized first-party project static inspection and public feature information only.
