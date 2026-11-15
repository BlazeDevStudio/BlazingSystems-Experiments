# PHX-HARDWARE handover — blocking poll coin-intake guard

**Date:** 2026-11-15 Asia/Manila  
**Role:** PHX-HARDWARE  
**Task:** Experiments #177  
**Branch:** `phoenix/hardware-poll-intake-guard-20261115`  
**Stack base:** DRAFT #293 at `a3f589063036fb9df00cded207ee928f93aa2728`  
**Classification:** DRAFT / LAB ONLY / PRODUCTION NO-GO

## Why this exists

Both current ESP8266 and ESP32 loops called synchronous `post("poll")` with a
3.5 second HTTP timeout before sampling the coin GPIO. While the acceptor relay
remained enabled, a normal short pulse could occur entirely inside that blind
window and never reach the pending flash journal.

Historical DRAFT #179 reproduced and guarded this failure on an older
development base. This branch composes the same safety invariant onto the
current #293 quarantine/journal stack without copying its obsolete finance,
quarantine, response-signature, or handover behavior.

## Source change

- `canStartPoll()` allows polling only when LittleFS is available, journal
  recovery is not required, there is no pending or settling coin, and the coin
  line is idle.
- `pollIntakeSuspended` is asserted and `applyOutputs()` de-energizes the
  acceptor before the blocking request. It is cleared only after `post("poll")`
  returns.
- A ready pending coin is prioritized over status polling.
- Existing signature verification, quarantine readback, journal ambiguity
  denial, and default-deny output gates remain in place.

## Verification

`tests/v060_esp_poll_intake_guard.py` extracts and compiles the actual
`canAttemptCoinPost`, `coinLineIdle`, `canStartPoll`, `applyOutputs`, and
`loop` functions from both sketches. It injects:

1. normal GPIO sampling,
2. a pulse wholly inside the 3.5 second network window,
3. an already-active edge at poll time,
4. an unsettled pulse group,
5. an owed pending coin, and
6. journal-recovery denial.

At handover creation, exact-head GitHub Actions are **NOT RUN / PENDING**.
Do not infer a pass from the test source or historical #179 runs.

## Explicit limits

- No physical relay polarity, electrical pulse waveform, brown-out, Wi-Fi,
  acceptor inhibit timing, or board reboot was tested.
- No firmware was flashed and no customer or real-money system was touched.
- Firmware still must not clear a pending coin based only on an unbound
  `"ok":true`; MASTER/CORE must approve the signed durable receipt ACK.
- #31, #32, #34, and #43 remain production blockers.


## Check-to-inhibit race closure

A follow-up source audit found a time-of-check/time-of-use interval in the first
guard: `canStartPoll()` sampled an idle GPIO before `pollIntakeSuspended`
disabled the acceptor. `beginPollWindow()` now performs the state/idle check,
disables outputs, and samples GPIO a second time. An edge arriving between
those reads cancels the poll, restores normal output policy, and is processed
by the existing journal path in the same loop.

The source-extracted host lab now injects this exact second-read transition,
bringing the modeled set to seven scenarios per board. Exact-head CI after this
change is **PENDING / NOT YET CLASSIFIED** at documentation time. This remains a
software timing model; real relay turn-off latency and acceptor pulse behavior
are **NOT TESTED**.
