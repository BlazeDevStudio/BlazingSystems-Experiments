# Blazing Visualizer — independent Avee functional recon

Date: 2026-10-23. Owner-authorized Android implementation. No Avee APK/decompiled code is bundled or analyzed here. This is a clean-room **feature and interaction comparison**, not a brand clone.

## Source ledger

| Source | Demonstrates | Limitations |
|---|---|---|
| https://aveeplayer.com/ | Official Avee list: library/playlists/queue, folder browse, internet radio, equalizer, Bluetooth/media control, 18 templates, image/GIF layers, variable fps/aspect, 4K export, and .viz support from 1.2.83 | Marketing/FAQ evidence, not proof of controls on exact currently installed Android version |
| https://github.com/BlazingSystems/BlazingSystems-Experiments/tree/blazing-visualizer/experiments/Blazing-Visualizer | Current owner source for Blaze UI, playback, export, note visuals and imported subset | Source alone is not verified runtime behavior |
| GitHub Actions run https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39880221516 | Clean JDK17 host build pass, API26/36 device failures with test-report artifacts | Emulator only; no physical microphone/export acceptance |

## Screen inventory (first-party source)

| ID | Screen | Entry | Primary controls | Observed states |
|---|---|---|---|---|
| S01 | Library | bottom tab | Search, Refresh, Import, song play, playlists | Empty, search-no-match, filled, permission denied (source/tests) |
| S02 | Visualizer | default/visualizer tab | Practice, Mic Live/Off, presets, editor, export, mini-player | No track, imported track, mic mode, arranging |
| S03 | Queue | bottom tab | Sort, reorder by long-press, remove, playlist save | Empty, filled, sorted |
| S04 | Preset chooser | Visualizer icon | Builtins, saved, import, export | Partial .viz import confirmation |
| S05 | Element editor | Edit icon | Layer type/properties, note routing, image, custom note-wheel text | Layer selected, arrangement |
| S06 | Export | Share/export icon | Frame mode, orientation, quality, timeline and MP4 save | Running/completed/failed |
| S07 | Practice | Practice chip | Speed, transpose, note wheel/piano | Selected track |
| S08 | Android system permission prompt | First launch/refresh/mic | Deny, allow | API26 crash reported in emulator, real UI on API36 |

## Representative user flows

| ID | Core job and taps | Risk / edge |
|---|---|---|
| F01 | Library → choose song → continuous queue → next track | Last-track repeat, long song, disconnect/restart |
| F02 | Visualizer → choose preset → Edit → arrange layer → Done | Small phone, drag/tap targets, scroll |
| F03 | Visualizer → Export → portrait → Optimize → Save | Bottom blank space, fit/cover and export parity |
| F04 | Queue → Save playlist → Library → Playlists → open/delete | Save dialog race, large library |
| F05 | Permission prompt → Deny → Library → Refresh → Allow | Android 8 SystemUI failure; rerun needed |
| F06 | Visualizer → Mic Live → input note → note wheel | Permission, background transition, polyphonic sound |
| F07 | Visualizer → Import preset .viz → review approximation → Accept | Unknown effect, missing asset, binary format |

## Scope and gaps

S/M: F04/F05 click semantics; L: F03 physical export parity, F01 session continuity; XL: full Avee .viz binary/effect compatibility and multi-note live transcription. Media3, YIN and FFT sources are independently implemented; older or marketing Avee information cannot prove modern DSP internals. Clean-room source should remain Blaze-branded.
