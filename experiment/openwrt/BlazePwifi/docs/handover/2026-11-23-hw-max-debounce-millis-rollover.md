# PHX-HARDWARE — maximum debounce quiet-window rollover regression (UTC08)

**Disposition:** focused Quarantine and Relay CI VERIFIED · Full validation BLOCKED by the inherited QA-owned poll-signature assertion · SIMULATED ONLY · HARDWARE ACCEPTED NO · PRODUCTION NO-GO.

## Exact source position

- Repository: `BlazeDevStudio/BlazingSystems-Experiments` (repository ID `1389289885`).
- Role: `PHX-HARDWARE`.
- Existing draft: [PR #327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327), OPEN / DRAFT / UNMERGED.
- Branch: `phoenix/hardware-prepoll-edge-abort-20261119`.
- Parent/base: #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`.
- Source/test commit: `e4ad49fd15a48e8f5aaad6d5ae4fa9314f5f61e3`.
- This file is the narrow handover added after that source/test commit; the introducing commit is the documentation head for this increment.

## Bounded task

The blocking-poll quiet-drain lab already checked the 250 ms minimum, but did not directly prove that the drain honors a larger configured debounce interval or remains correct when `millis()` wraps.

Added a source-extracted scenario that:

1. Starts the fake monotonic clock at `0xFFFFFF00`.
2. Sets the configured debounce to its supported upper bound, 2000 ms.
3. Calls the exact production `beginPollWindow()` extracted from both board sketches.
4. Requires exactly 2000 elapsed milliseconds using unsigned subtraction across wrap.
5. Requires intake to remain suspended, relay/LED OFF, and no drain-abort latch.

The scenario and runner are split across the existing fixture modules to keep the test orchestration and C++ scenario readable.

## Changed paths

- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab_fixtures.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab_scenario_fixtures.py`

No production `.ino` sketch, shared API, server, financial ledger, QA-owned test, release workflow, signer, witness or COE destination was changed.

## Failure injection and exact-head evidence

**Quarantine** — [Run #45141790467](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45141790467), job `137581324194`: SUCCESS at source/test SHA `e4ad49fd...`.

- ESP8266: `POLL_QUIET_WINDOW_LONG_DEBOUNCE_ROLLOVER_PASS`.
- ESP32: `POLL_QUIET_WINDOW_LONG_DEBOUNCE_ROLLOVER_PASS`.
- Capping the quiet window at 250 ms is rejected on both boards (expected exit 61).
- Replacing unsigned elapsed-time comparison with `millis() < started + quietMs` is rejected on both boards across wrap (expected exit 61).

**Relay/output and parent poll-loop lab** — [Run #45141790327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45141790327): SUCCESS.

- ESP32 boot-polarity job `137581324068`: PASS.
- Source/output-polarity job `137581324389`: PASS.
- The same long-debounce rollover scenario and both mutations are visible in the exact job logs for ESP8266 and ESP32.

**Full build/integration** — [Run #45141790462](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45141790462): FAILURE.

- Validation job `137581324403`: FAILED at `Missing poll signature check` in the ESP8266 sketch. This is the inherited QA-owned assertion against the current deny-only poll consumer; PHX-HARDWARE did not invent `response_sig` or edit QA-owned tests.
- All 14 target/platform jobs, including ESP8266, ESP32, Android, x86_64, Ruijie and the configured Orange Pi targets: SUCCESS.
- 12 downstream simulation, bundle, candidate, signing and publication jobs: SKIPPED.

Focused test results are **CI VERIFIED / SIMULATED ONLY**. The Full workflow is not green.

## Coordination and blockers

- Master `ROLE_ASSIGNMENTS.md` at current PR #288 head `876051f1b7c3c0a13a2c322c5a127306d0908b21` still pins #327 to stale head `b6304208...`; actual PR #327 head advanced to this increment. Master must refresh the role pin.
- Master UTC08 report also records PR #345 as current Hardware evidence while the role-assignment table still names #327 as active child. Master should reconcile this stack/assignment discrepancy without rebasing, retargeting or merging either branch.
- CORE/QA still need an approved authenticated register/poll and event-bound receipt contract plus golden vectors. The current poll consumer remains default-deny.
- Private Google Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` is unavailable through the connected surface; no older registry snapshot was substituted.
- Repository ownership is canonicalized to `BlazeDevStudio`, but the root README still contains historical `BlazingSystems` owner links. This is a Master-owned documentation cleanup request, not a Hardware edit.

## Release status

- Poll quiet-window upper-bound/rollover regression: **CI VERIFIED** (host simulation).
- Physical coin acceptor and relay: **NOT TESTED**.
- 150 power cuts, 30-device/24-hour soak, electrical pulse/recovery: **NOT TESTED**.
- Protected anti-rollback signer/witness, v1-to-v2 financial migration, durable accounting/replay and independent QA/release signoff: **NOT ESTABLISHED**.

**HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.**

## Next exact action

PHX-MASTER must refresh #327's actual head and reconcile #327/#345 assignment records; PHX-CORE and PHX-QA must resolve the authenticated poll/receipt contract. PHX-HARDWARE will revalidate all branch heads at the next activation before selecting another owned task.
