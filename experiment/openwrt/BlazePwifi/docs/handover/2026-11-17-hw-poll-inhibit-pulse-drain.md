# PHX-HARDWARE handover — poll inhibit pulse-train quiet guard

## UTC11 — poll-window fixture chronology correction (test-only)

**Current branch HEAD:** `6fda96a7151cd8b55bbcb1781adfcda822f41d3e`  
**Firmware source-fix SHA (unchanged):** `5d3dc5547606841209ade10c888dab67e1ffcaa7`  
**Current parent #317 head:** `8bde0c268b76fe5578b7cba5c29e402c6d7582f2`

A source/test audit found the prior blocking-HTTP scenario in `poll_response_failclosed_lab.py` rewound fake time: `beginPollWindow()` had already advanced to the 250 ms quiet boundary, but the fixture then assigned `fakeNow=120` and labelled the 100–180 ms pulse as occurring during the later HTTP wait. That was an impossible timeline and could give false confidence about the 3.5 s synchronous-poll window.

The test now places the pulse at 300–380 ms, samples at 320 ms, and advances to 3600 ms for the timeout. It explicitly rejects a pulse start before the 250 ms boundary. New `poll_window_timeline_guard_lab.py` keeps the fixture invariant visible and human-debuggable.

**Local static RED/GREEN evidence (not GitHub Actions):**
- Pre-fix lab at commit `9aaa390c482918f29a71fb40e7e7d79a70d95a24`: expected RED because it contained `fakeNow=120` and the pre-boundary pulse.
- Corrected lab at commit `12bc0cba790ea11a319c2769b07d106f593811e1`: static timeline guard PASS; pulse is after the quiet boundary and time does not rewind.
- Both ESP sketches still contain the unchanged `max(runDebounceMs, 250 ms)` quiet guard.

**CI status:** the previous exact-source run [#44069258396](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44069258396), job `133990936760`, passed the earlier 250 ms firmware source and the prior lab, but it predates this fixture correction. The new fixture guard has **not** yet received a new exact-head GitHub Actions result. Full run [#44069254356](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44069254356), validation job `133991048028`, remains failed at QA-owned `tests/controllers.sh` (`Missing poll signature check`); ESP8266/ESP32 and listed target builds passed, but Full is not green.

Parent #317 workflow was extended at `8bde0c268b76fe5578b7cba5c29e402c6d7582f2` to include the timeline guard and poll-response/window lab on child PR changes. No new PR-triggered run was returned by the connected GitHub run query. The #318 branch remains a stacked draft based on merge-base `3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3`; it is 17 commits ahead / 8 behind the current #317 head. Do not rebase, force-push or merge without Master stack reconciliation.

No firmware runtime behavior changed in this activation. This is test-fixture correctness work only; physical pulse/relay timing remains NOT TESTED.


- Role: PHX-HARDWARE
- Task: Project Phoenix #177 / control plane #172
- Repository: `BlazeDevStudio/BlazingSystems-Experiments`
- PR: [#318](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/318), DRAFT, stacked on DRAFT #317
- Branch: `phoenix/hardware-poll-inhibit-settle-20261117`
- Base branch: `phoenix/hardware-clear-pending-marker-match-20261117`
- Base SHA: `3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3`
- Final source SHA: `5d3dc5547606841209ade10c888dab67e1ffcaa7`
- Current docs checkpoint (before this update): `233ad9749579d0048185eea7023878a3d628adf2`
- Status: DRAFT / FOCUSED CI VERIFIED / FULL VALIDATION FAILED / PHYSICAL ACCEPTANCE NOT TESTED / PRODUCTION NO-GO

## Confirmed source-level timing gap

Both ESP sketches originally used the configured debounce interval (20 ms minimum, 40 ms default) as the post-relay-inhibit quiet window before starting synchronous HTTP poll. Master Architecture Contracts §2.1 defines a **250 ms inter-coin quiet period** as the completion boundary for a pulse train. A 20/40 ms debounce interval can end between pulses in one coin insertion. A first 120 ms single-pulse drain improvement was also insufficient to cover the 250 ms pulse-train gap.

This is a software timing gap derived from the shared contract. It does not prove a specific acceptor emits a delayed pulse after relay de-energization; the actual output delay and relay behavior remain unmeasured on physical hardware.

## Test-first RED / refinement

1. Test-only commit [`3948b9c405c57fea6e90e610774ce956ef3a5033`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/3948b9c405c57fea6e90e610774ce956ef3a5033) added a delayed pulse beginning 80 ms after inhibit. Focused [#44067323124](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44067323124), job `133984253325`, **RED** at the 120 ms expectation against the old 20 ms guard.
2. An intermediate 120 ms guard passed focused [#44067564257](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44067564257) at source `5072e8fd...`. That result was superseded after checking the 250 ms inter-coin contract.
3. Test-only refinement [`4cdeaa2f81569a95a36f8aabc6e70ca96cefbb4a`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/4cdeaa2f81569a95a36f8aabc6e70ca96cefbb4a) adds an 80 ms pulse beginning 200 ms after relay inhibit. Focused [#44069089876](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44069089876), job `133990363481`, **RED** at scenario return 17 because the 120 ms interval was shorter than the 250 ms pulse-train boundary.

## Final firmware correction

- ESP8266: [`c93d836201bf851f63b1938f1fdeeb06fd4dafa2`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c93d836201bf851f63b1938f1fdeeb06fd4dafa2)
- ESP32: [`5d3dc5547606841209ade10c888dab67e1ffcaa7`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/5d3dc5547606841209ade10c888dab67e1ffcaa7)

Both `coinLineQuietAfterInhibit()` implementations now wait for `max(runDebounceMs, 250 ms)` of continuous quiet after relay inhibit. A pulse observed during that interval cancels the blocking poll, releases the temporary inhibit and returns to the normal loop while the line remains observable. No protocol/API, receipt, accounting, migration, signer, QA-owned test or workflow was changed.

## Focused exact-source CI

- Final source SHA: `5d3dc5547606841209ade10c888dab67e1ffcaa7`
- Run: [#44069258396](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44069258396)
- Job: `133990936760`
- Result: **SUCCESS**

Both board-shaped source-extracted harnesses passed:
- Debounce floor: 8/8
- Poll-window guard: 12/12
- Blocking-poll relay inhibit: 1/1
- Poll response default-deny: 11/11
- Strict root JSON: 13/13
- Coin disposition default-deny: 4/4
- Register configuration denial: 7/7
- Quarantine: 23/23
- Pending attempt marker: 28/28
- Mount/output protection: 7/7
- Boot recovery: 16/16
- Pending clear: 17/17
- Pending write/readback: 22/22
- Coin POST gate: 10/10

These are C++ host tests and fake-LittleFS simulations only.

## Full validation and blockers

- Full run: [#44069254356](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44069254356)
- Validation job: `133991048028`
- Result: **FAILED** at QA-owned `tests/controllers.sh`: `Missing poll signature check` in the ESP8266 sketch.

Master Architecture Contracts §6.3 keeps poll admission default-deny until PHX-CORE publishes the canonical producer/consumer contract and PHX-QA approves exact positive/negative vectors. The inherited positive-signature assertion is stale against that decision; firmware was not weakened to satisfy it. Other target jobs were still running at the last observation. A second Full run `#44069258582` had its validation job queued at that observation, so it is not claimed green or failed.

Flags: `PHYSICAL_COIN_ACCEPTOR_VERIFIED=0`, `PHYSICAL_POWER_CUT_VERIFIED=0`, `FINANCIAL_PRODUCTION_AUTHORIZED=0`.

## Ownership and next action

- PHX-QA: reconcile the inherited controller-parity assertion with Master §6.3, repair its canonical extractor, and independently rerun Full at the exact combined head.
- PHX-MASTER: review the 250 ms local guard against the electrical acceptance plan and update the role index/control-plane assignment to include #318.
- PHX-CORE: publish the canonical authenticated poll/receipt contract; no hardware admission change is authorized before it exists.
- PHX-HARDWARE: retain default-deny; do not claim physical pulse-loss closure until an approved noncustomer bench measures the actual acceptor/relay timing.

No flashing, reset, customer device, live coin, financial migration, signing, release tagging, merge or deployment occurred.

## UTC11 follow-up — guard marker correction

The new Python timeline guard initially searched for a `#` comment marker, but the target scenario is embedded in the C++ fixture and uses `//`. The guard was corrected to match the actual source text. Local static RED/GREEN was repeated: pre-fix lab `9aaa390c482918f29a71fb40e7e7d79a70d95a24` is rejected; corrected fixture/guard at branch head `6fda96a7151cd8b55bbcb1781adfcda822f41d3e` passes. This remains a local static check, not Python execution in GitHub Actions, C++ compilation or hardware evidence. Exact-head CI is still pending.


## Exact 250 ms quiet-boundary pulse regression — 2026-11-17 UTC12

Added a source-extracted boundary case to the existing ESP8266/ESP32 poll-window lab: a pulse beginning at exactly t=250 ms after relay inhibit must make the final idle check fail, cancel the synchronous poll, release the temporary inhibit, and leave the pulse line active for the normal loop to sample. The lab now expects 13/13 poll-window cases per board. The static timeline guard also requires this exact-boundary scenario and the updated count.

This is host C++ simulation only. It does not prove the physical acceptor's post-relay pulse delay or electrical behavior. The parent PR #317 workflow was fixed at a29c51b to run child poll-window labs only when the guard file exists on the exact checkout. This commit is intended to trigger those tests at the literal child head; no rebase, cherry-pick, merge or force-push is performed.

Current child head before this change: 7cd93a70c84b322f4cdbc46a9df3eb6355d66b86. Current comparison to parent #317 head a29c51b8066095cf1a19a8847849f6da3c344ae7: 22 ahead / 9 behind, diverged, mergeable=false. Master stack reconciliation remains required.


## Exact-boundary failure injection — 2026-11-17 UTC12

The 250 ms boundary scenario now has a targeted mutation check. The lab builds a second host binary with the final `return coinLineIdle();` in `coinLineQuietAfterInhibit()` replaced by `return true;`. The mutant must fail specifically at scenario exit 25 (pulse begins at exactly 250 ms); any other exit is treated as a harness failure. The timeline guard requires the mutation code and explicit rejection marker.

Previous exact-head child run [#44082960356](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44082960356), job `134037962611`, passed the 13/13 poll-window matrix on both boards before this new mutation was added. New exact-head mutation CI is pending. No firmware runtime changed; physical pulse delay and electrical acceptance remain NOT TESTED.
