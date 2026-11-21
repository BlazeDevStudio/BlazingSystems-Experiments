# PHX-HARDWARE — quarantine host-lab module split

Checkpoint UTC: 2026-11-21T19:55:13.861Z

**Role:** PHX-HARDWARE  
**Task:** Issue #177 / cleanup-first #266 / PR #336  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-quarantine-lab-modules-20261121-utc19`  
**Parent PR:** #335 at `d09b0c9dafad8dbbcda5723d8094f4975c14a274`  
**Source/test commit:** `741068c7804b83897f5deab5afc7739457532427`  
**PR:** https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/336

**Disposition:** OPEN / DRAFT / UNMERGED · focused CI VERIFIED · SIMULATED ONLY · HARDWARE ACCEPTED NO · PRODUCTION NO-GO.

## 1. Exact source change

The 674-line `quarantine_readback_lab.py` mixed source extraction/board-parity orchestration with a 17,937-character C++17 fake-LittleFS harness. This change:

- moved the literal C++17 harness to adjacent `quarantine_readback_lab_cpp.py`;
- changed the runner to import `CPP` from that module;
- preserved the extracted raw C++ template byte-for-byte (17,937 characters before and after);
- changed no ESP sketch, scenario, expected result, workflow, controller contract, financial code, signer, witness, GPIO or relay behavior.

This is a source-organization change only.

## 2. Exact-head CI evidence

### Focused Hardware workflow

[Run #44943004243](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44943004243) — **SUCCESS**  
Job `quarantine-source`: **136964113650**  
Exact checked-out SHA: `741068c7804b83897f5deab5afc7739457532427`.

Log markers:
- `SOURCE_QUARANTINE_PASS 36/36 scenarios` for ESP32 and ESP8266;
- `PENDING_WRITE_READBACK_PASS 22/22` for both board source paths;
- coin pulse capture `17/17` for ESP8266 and ESP32;
- source mutation probes rejected missing guards and weakened failure paths;
- final sentinels explicitly state `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, `FINANCIAL_PRODUCTION_AUTHORIZED=0`.

### Full BlazePwifi integration

[Run #44943004250](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44943004250) — **FAILURE**  
Exact checked-out SHA: `741068c7804b83897f5deab5afc7739457532427`.

- All **14/14** target/Android build jobs passed, including ESP32 job `136964114307`, ESP8266 job `136964114498`, Orange Pi Zero 3 job `136964114438`, Ruijie job `136964114558`, and Android job `136964114457`.
- Validation job `136964114416` failed at the inherited QA-owned assertion: `Missing poll signature check` in `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`.
- Downstream signing, candidate, update-bundle and publication jobs were skipped.

This is not caused by the module split; no QA-owned assertion was changed.

## 3. Revalidated audit leads

- Current parallel PR #283 head `88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d`: both sketches return false on failed quarantine append before `clearPending()`, but each contains only the helper definition; no active `quarantinePending()` callsite is present there.
- Active parent PR #335 head `d09b0c9dafad8dbbcda5723d8094f4975c14a274`: both sketches have an active callsite; the helper checks pending evidence and the durable attempt marker, latches `journalRecoveryRequired` on append failure, and reaches `clearPending()` only after append success. This remains DRAFT source evidence, not physical LittleFS acceptance.
- Main controller producer `cgi-bin/vendo` at `2e3a1430d08cc6606429a042df3b5848f53c7267`: `register|ping` and `poll` replies still do not carry an approved `response_sig`; signatures on member endpoints are not a substitute. No ad-hoc signature or firmware authorization was added.

## 4. Remaining gates / limitations

- Authenticated register/poll/coin receipt contract: BLOCKED on PHX-CORE contract and PHX-QA source-exact tests.
- Physical LittleFS durability, electrical pulse/recovery, 150 controlled power cuts, and 30-device 24-hour soak: NOT TESTED.
- Protected anti-rollback signer/witness, v1-to-v2 financial migration, durable accounting/replay, and independent release signoff: NOT ESTABLISHED.
- The requested private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available through the exposed connectors. Library search surfaced older v7/v5/v3 snapshots only; no Google Drive connector was exposed. Those older snapshots are not substitutes for v11.

## 5. Next exact action

PHX-QA to independently review PR #336 at source/test SHA `741068c7804b83897f5deab5afc7739457532427` and confirm the runner import executes from the exact PR checkout. Keep #336 DRAFT and unmerged. PHX-CORE must publish the canonical domain-separated register/poll/coin receipt contract before QA changes the positive signature assertion; PHX-MASTER owns stack reconciliation and release sequencing.

```json
{
  "protocol": "BLAZE-COMMS/1",
  "message_id": "PHX-HARDWARE-20261121T19-QUARANTINE-LAB-MODULE-SPLIT",
  "from": "PHX-HARDWARE",
  "to": ["PHX-MASTER", "PHX-QA", "PHX-CORE"],
  "type": "REQUEST_REVIEW",
  "priority": "P2",
  "task_id": "#177/#266/#336",
  "branch": "phoenix/hardware-quarantine-lab-modules-20261121-utc19",
  "base_sha": "d09b0c9dafad8dbbcda5723d8094f4975c14a274",
  "scope": [
    "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/quarantine_readback_lab.py",
    "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/quarantine_readback_lab_cpp.py"
  ],
  "status": "PR_READY",
  "evidence": [
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/741068c7804b83897f5deab5afc7739457532427",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44943004243",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44943004250",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/336"
  ],
  "blockers": [
    "Full validation fails at QA-owned Missing poll signature check",
    "Physical hardware acceptance not tested",
    "Google Drive v11 registry unavailable through exposed tools"
  ],
  "next_action": "PHX-QA independently review exact source/test SHA 741068c7804b83897f5deab5afc7739457532427; keep PR #336 DRAFT.",
  "updated_utc": "2026-11-21T19:55:13.861Z"
}
```


## UTC20 follow-up — isolate board parity from the quarantine runner

**Source/test HEAD:** `7e008ea74ef154446e273f7d25423ea07be28d70`  
**PR:** [#336](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/336) — OPEN / DRAFT / UNMERGED  
**Parent:** #335 at `d09b0c9dafad8dbbcda5723d8094f4975c14a274`.

### Source organization

The next cleanup pass moved the ESP32/ESP8266 board source extraction, 23-function parity inventory, local polarity guard checks, lexical-extractor fixture, and fail-open mutation probes into adjacent `quarantine_readback_lab_parity.py`.

The runner `quarantine_readback_lab.py` now owns only the source-extracted C++ harness substitution/compile/scenario path and downstream lab orchestration. The existing `quarantine_readback_lab_cpp.py` template was not changed. No firmware sketch, controller contract, financial code, signer/witness, GPIO/relay behavior, workflow, or production admission path changed.

### Exact-head focused evidence

At source/test SHA `7e008ea74ef154446e273f7d25423ea07be28d70`:

- Focused Quarantine Byte Readback [run #44948196546](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44948196546), job `136980070966`: **SUCCESS**.
- Board parity: 23/23 functions byte-identical.
- Mutation probes rejected fail-open append verification, fail-open coin disposition, permissive poll status parsing, positive poll admission, quarantine escape mapping drift, and removed local polarity gates.
- Quarantine source-extracted host scenarios: 36/36 per board (72/72).
- Escape boundaries: 4/4 per board; length sweep: 161/161 per board; legacy dangling-escape defect reproduction: 5/5 per board.
- Existing pending-attempt marker tests: 29/29 per board; mount, pending-journal, pending-clear, pending-write/readback and coin-disposition labs also passed in this focused workflow.
- The workflow's final sentinels remain `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`.

An intermediate commit `abdc677e95f16bbae16c8e40df90bb6cd6eba549` failed the focused job because the Python escape-anchor spelling did not match the extracted C++ source. The anchor was corrected in `7e008ea...`; the exact-head focused run above is the successful result. The failure remains visible in Actions history and is not hidden.

### Full integration at the same source/test SHA

- Push run [#44948192001](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44948192001), exact SHA `7e008ea74ef154446e273f7d25423ea07be28d70`.
- Validation job `136980131013`: **FAILURE** at inherited QA-owned `Missing poll signature check` in the ESP8266 sketch.
- All 13 firmware target jobs completed **SUCCESS**, including ESP8266, ESP32, x86_64, Orange Pi Zero 3, and Ruijie.
- Android job `136980130866` was still building the BlazeRental APK at the last read; overall run was still in progress. Downstream signed import, update bundle and simulation jobs were skipped after validation failure.
- The PR-triggered Full run `#44948196547` remained queued at the last read.

No signature was invented and no QA-owned assertion was modified. The current main producer still lacks the approved authenticated controller register/poll response contract. Keep firmware default-deny until PHX-CORE publishes canonical bytes/golden vectors and PHX-QA owns the corresponding assertion update.

### Acceptance classification

- **SIMULATED:** source-extracted C++17 fake-LittleFS and Python parity/failure-injection labs.
- **CI VERIFIED:** focused exact-source workflow at `7e008ea...`; 13 firmware target builds in the Full run.
- **Full integration:** FAILED at the inherited poll-signature validation gate; Android remained in progress at last read.
- **HARDWARE ACCEPTED:** NO. Physical LittleFS durability, coin/electrical pulse, relay recovery, 150 controlled power cuts and 30-device/24-hour soak remain NOT TESTED.
- **PRODUCTION READY:** NO-GO.

### Next exact action

PHX-QA independently reviews the new parity module and replaces the stale positive poll-signature fixture only after PHX-CORE publishes the authenticated register/poll and event-bound receipt contract. PHX-HARDWARE keeps #336 DRAFT and does not modify the shared API or QA-owned assertion.
