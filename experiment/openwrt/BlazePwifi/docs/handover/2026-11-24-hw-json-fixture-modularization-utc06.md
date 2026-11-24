# PHX-HARDWARE UTC06 — strict JSON grammar fixture modularization

**Role:** PHX-HARDWARE  
**Tasks:** #177 / #266 / #349  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**PR:** [#349 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Parent/base:** #347 `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test commit:** `da046d5ea80a8daac7258d302ecc310cd5634b24`  
**Workflow-trigger correction:** `95d57ff8388592fdefd18e32c4f193470d71a883`

## One bounded cleanup task

Moved the strict poll-JSON grammar lab's four large fixture definitions out of the Python orchestration file into:

`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_json_array_primitive_lab_fixtures.py`

Moved names, byte-for-byte:

- `PARSER_FUNCTIONS`
- `PROTOTYPES`
- `COMPOSITE_MAIN`
- `PRIMITIVE_MAIN`

The orchestration file now imports these fixtures and retains only source extraction, compile/run, baseline assertions and failure-injection logic.

- Orchestrator: 12,937 → 8,313 characters (4,624 fewer; 35.7% reduction).
- New fixture module: 5,018 characters.
- GitHub read-back comparison confirmed the entire original fixture block is present unchanged in the new module.
- All four imports are present; all four fixture definitions are absent from the orchestration file.

The Relay workflow path filters now include the poll-response lab, its fixtures, the JSON grammar lab and its new fixture module exactly once in both `push` and `pull_request` sections. This makes direct edits to the grammar lab or fixture module trigger the owning focused workflow, rather than relying on another changed file in the same PR.

## Exact CI evidence

Final tested PR head: `95d57ff8388592fdefd18e32c4f193470d71a883`.

- Relay PR [run #45342723099](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45342723099):
  - `source-output-polarity`, job `138269939037`: **PASS**.
  - `esp32-boot-polarity`, job `138269938622`: **PASS**.
  - The source-output log proves the JSON lab was actually invoked through `poll_response_failclosed_lab.py`.
  - ESP8266 and ESP32 each report primitive grammar **9/9 valid, 16/16 invalid**, with **4/4 primitive fail-open mutations rejected**.
  - ESP8266 and ESP32 each report composite grammar **6/6 valid, 12/12 invalid**; the array terminator, array separator, object separator, raw-control, unsupported-escape and non-hex Unicode mutations are rejected.
  - The same run also passes poll-response deny tests, debounce/window guards, bounded HTTP response tests and relay/boot polarity checks.

- Full PR [run #45342722861](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45342722861): validation job `138270051677` **FAIL** at the inherited `Missing poll signature check` in the ESP8266 sketch. Firmware/platform jobs were still running at handover time; no Full success is claimed. The failing assertion remains a CORE producer / QA consumer-contract issue, not a reason to invent a positive signature or weaken default-deny.
- Quarantine PR [run #45342722855](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45342722855), job `138269937889`: **IN PROGRESS** at handover time; no pass is claimed.

## Scope and safety boundary

No production `.ino`, controller API, register/poll contract, financial schema, coin admission, relay actuation, GPIO, signer, witness, migration or accounting behavior changed. This is a test-harness organization and CI-trigger correction only.

All results are host/source-extracted simulation and CI evidence. Physical coin acceptor, relay/electrical recovery, LittleFS power-loss, 150 controlled power cuts and 30-device/24-hour soak remain **NOT TESTED**. **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

## Revalidated parallel blockers

- #239 remains OPEN/DRAFT; current head `d83b715b116185107737fef721c2eece8feebf39`.
- #254 remains OPEN/DRAFT; current head `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`.
- #283 remains OPEN/DRAFT; current head `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`. Both sketches guard `clearPending()` behind successful quarantine append, but `quarantinePending()` remains definition-only with no active callsite. `response_sig` appears only in comments; current main CGI emits no authenticated register/poll response envelope. Keep this path deny-only.
- Master #288 remains OPEN/DRAFT/UNMERGED; current Master coordination head `0fadd1019359b1b88ab24917ef3a568df375e664`. Master retains coordination-only ownership.
- Cleanup-first #266 remains OPEN, 0/7 tracks complete.
- COE main remains `a6513ab4412b4c014eee2863e45cbe32d06cb243`; COE PR #26 remains OPEN/DRAFT/FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`. No migration or promotion was performed.
- Safety #34, financial #31/#32 and witness #43 remain OPEN P0 release blockers.

## Next exact action

PHX-QA independently reviews the fixture extraction and mutation evidence. PHX-CORE publishes the approved authenticated register/poll response envelope and canonical golden vectors; PHX-QA reconciles the inherited parity assertion against that contract. PHX-MASTER refreshes the #349 exact-head pins. Hardware remains deny-only and must not synthesize `response_sig`.

The private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available through the connected Library search, and no Google Drive connector is exposed in this execution. No older registry was substituted.
