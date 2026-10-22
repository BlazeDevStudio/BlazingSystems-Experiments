# Execution record

2026-10-22 recovery: source restored from the recorded changes after automated workspace cleanup. Remote recovery base: eff9b6d3250e512219a13ea3222669a51b8ff352. Old local commits and pending Android acceptance outputs were removed; no final export or quality pass from that lost run is claimed.

The owner authorized continuation and subsequent routine approvals. Continue the existing plan autonomously. Preserve source checkpoints on the remote feature branch.

Rulings retained: use a source-built Android app with attributed Avee DSP/path components, bundled Basic Pitch, a deterministic shared Canvas/GL compositor and Media3 source clock. Native packs are the complete interchange format; Avee conversion remains explicit and partial. Export uses original-speed audio. A forced H264 profile without a level broke API26 configuration and was removed, as confirmed against ACodec.cpp. Use CPU inference and 16-KiB-aligned LiteRT. Keep raw/corrected note data separate. The isolated-attack audio refiner skips overlapping sustained notes; caches include its version. Analysis is bounded to 30-minute tracks in this preview. Physical performance cannot be inferred from emulator results.

Recovery verification: 25 host tests passed after the image-content validation fix. All three import image regressions failed before the fix. The two changed-source regression tests failed with the old behavior (retained corrections and unchecked export snapshot), then the guarded implementation was restored for the full suite. Independent Python TFLite + Spotify postprocessing reproduced six synthetic notes and three recorded-flute notes. Raw Python flute onsets include an E-note 60 ms late; native acceptance must measure the optional isolated-attack refiner separately. Native results are not yet claimed.

Ruling: analysis allocation is bounded by 45% of the device heap and at most 30 minutes, with a one-minute lower limit — full-track activations otherwise risk memory exhaustion on small devices — longer tracks may need a shorter excerpt in this preview.
