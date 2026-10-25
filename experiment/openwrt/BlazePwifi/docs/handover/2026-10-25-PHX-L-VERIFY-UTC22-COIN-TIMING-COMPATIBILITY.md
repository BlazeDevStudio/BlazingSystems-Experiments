# PHX-L-VERIFY UTC22 — ESP coin timing-pair admission audit (2026-10-25 UTC)

**Scope:** QA-only, both ESP Vendo firmware sketches, no source edit, no Codex, no hardware, no customer payment, no release. Source PR #193 documentation HEAD `53e86fc966840e5c48c9322cacaf92a6034224c4`, stacked on unmerged draft #179. ESP8266 Git blob `a64dd08ecb4eaa71da3b29b43d86ffa8a58df5b5`; ESP32 `7b2d3a9c9c0ea076992265bdf1113a6db75a350f`.

## Source observation and independently executed host model

Both `applyRemoteConfig()` implementations clamp `coin_debounce_ms` to 1..2000 and `pulse_group_ms` to 10..10000 **independently** (ESP8266 lines 262-263; ESP32 230-232). Both `loop()` implementations close the pending pulse group after `millis()-lastEdge>runPulseGroupMs` and set `pendingReady=true` (ESP8266 380-405; ESP32 341-353). Neither path validates the selected timing pair against a measured acceptor pulse waveform. `applyOutputs()` inhibits the coin relay once `pendingReady` is true.

Strict C++17 source-transcribed host model: `g++ -std=c++17 -O2 -Wall -Wextra -Werror` **compiled successfully**; **20/20 expected traces matched** (10 per board). Four timing scenarios per board, **8/20 modeled cases total**, closed the group before subsequent synthetic coin edges: 1 modeled journal write for 2 or 3 presented active edges. Default 40/400 ms with 100 ms spacing produced 3/3 modeled journal writes; long-group controls also retained their modeled edges. One separate too-rapid pulse case was intentionally debounced and was NOT counted as premature closure. First synthetic edge at 10,000 ms to avoid startup debounce as a confounder. This is a host timing model, **not source-extracted Arduino execution**.

Reproduction artifact in conversation sandbox: `phx_verify_utc21_timing_compat_evidence.zip`, SHA256 `d47bcb1a5d004cd4b35a9610eccfda827ba97c61802d3bec364213eb76e63ae1`; harness SHA256 `dc18194034c955ed149597087e1d0f36068617fe4be6af620d9f115e6a2796db`; result log SHA256 `7457a74d40aa31e43f838bf84959e0a567ef757c9f9163fab6723422f39e580d`. The archive is not uploaded to GitHub; link/provenance is not an independently accessible GitHub artifact.

## Evidence boundary / release status

An incompatible timing pair can prematurely close the **modeled** pulse group; no physical coin loss, electrical relay behavior, LittleFS durability, server ACK or actual misconfiguration has been demonstrated. A rule such as `group_ms > debounce_ms` alone does not prove waveform compatibility. MASTER/CORE must approve per-acceptor measured pulse width, minimum/maximum inter-pulse spacing, idle gap and disarm/rearm policy before any firmware source change. Preserve previously journaled events; do not silently discard ambiguous pulses.

**Exact-head CI:** Full #40233018181 at `53e86fc966840e5c48c9322cacaf92a6034224c4` **COMPLETED FAILURE**, validate job 121288627112: HND-0700 and CI-0701 PASS, 13 pass + 2 existing config-auth/cold-reboot RED per board, both Arduino compiler jobs SUCCESS; native #40233018253 **COMPLETED SUCCESS**. This is not a source safety GREEN. No source merge/integration base approved.

**P0 NO-GO:** independent witness #43, financial #31/#32, physical #34 (150 actual cuts, 30-device 24h), migration, permanent signing and electrical coin-acceptor waveform remain unverified. #150/#183 separate unmerged recovery work, #173 closed/unmerged. No flashing, keys, commercial release or customer data.

**NEXT EXACT ACTION:** MASTER+CORE decide waveform timing envelope and safe rejection/quarantine policy. VERIFY then add an extracted-source regression for timing-pair admission in a separate reviewed TEST-FIRST change, re-run exact-head Full/native/ESP compilers and only after approved physical scratch acceptance consider merge.
