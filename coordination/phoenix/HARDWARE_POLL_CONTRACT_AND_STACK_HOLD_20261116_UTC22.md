# PHX-MASTER — Poll-response trust and hardware stack hold

**Checkpoint:** 2026-11-16 UTC22  
**Role:** PHX-MASTER  
**Scope:** Architecture/interface contract and cross-role branch coordination only  
**Disposition:** BLOCKED / DRAFT / PRODUCTION NO-GO

## 1. New exact-head hardware evidence

| PR | Role branch | Exact head | Base |
|---|---|---|---|
| #294 | `phoenix/hardware-poll-intake-guard-20261115` | `8cbd4ecec6fcc4a5b0c758c300de986abee5cf40` | `a3f589063036fb9df00cded207ee928f93aa2728` |
| #315 | `phoenix/hardware-quarantine-append-failclosed-20261117` | `953b743f3edc26671ddf7a457c2a4a4ac0de093f` | #314 head `556adc20ef0cfd355089aff3b979c0169af79bdd` |
| #316 | `phoenix/hardware-poll-response-failclosed-20261117` | `888e6941e3a7a81641682c23d937f97d8117d2ea` | #294 head `8cbd4ecec6fcc4a5b0c758c300de986abee5cf40` |

#315 and #316 both modify the same ESP32 and ESP8266 `.ino` files. Their tips are **diverged**: comparing #315 head as base to #316 head gives #316 **10 commits ahead and 108 behind**. #315 is 108 commits ahead of #294's head. The branches therefore cannot be treated as one linear stack.

The patches show distinct changes in overlapping files:

- #315 changes `quarantinePending()` so a failed quarantine append latches `journalRecoveryRequired` and blocks same-boot coin POST retry.
- #316 adds `acceptPollResponse()` and changes the poll loop in both sketches.

**Master disposition:** no branch selection, cherry-pick, rebase, merge or firmware edit by PHX-MASTER. PHX-HARDWARE must consolidate the changes into one owner-controlled linear stack, preserve both behaviors, and ask PHX-QA to verify the combined exact head.

## 2. #316 CI: one confirmed validation failure; full run incomplete

At exact #316 head `888e6941...`:

- [Full run 43972511250](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43972511250) was still `in_progress` at last observation.
- Validation job [133668043447](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43972511250/job/133668043447) completed **failure** at the `Controller protocol parity` step.
- ESP32 compile job [133668042967](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43972511250/job/133668042967) completed success; ESP8266 compile job [133668043518](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43972511250/job/133668043518) completed success.
- Orange Pi PC and Android jobs were still in progress at last observation.
- Focused run [43972511337](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43972511337) completed success, but its workflow is the inherited quarantine byte-readback lab, not proof that the new poll-response matrix passed.
- PHX-HARDWARE reports the validation failure is because the existing #294 source-extraction loop omits the new `acceptPollResponse()` function, yielding an undeclared-function error in generated C++. The job status is independently visible; the exact compiler diagnostic was not independently retrieved in this Master pass.

#294's own runs [43669122948](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43669122948) and [43669122828](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43669122828) completed success, but they predate #316's added function. #315's scoped runs [43963997471](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43963997471) and [43963997475](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43963997475) completed success for its quarantine scope; they do not validate #316.

## 3. Poll-response trust contract gap

The #316 patch's `acceptPollResponse()` initializes `signatureOk=true`, then performs signature verification only when `cfg.key` is nonempty. With an empty key, a response containing `"ok":true` can proceed to set `insertMode` and `activeTarget` without a verified response signature.

That source-level behavior conflicts with the existing Master architecture contract: unauthenticated or signature-mismatched poll responses must be ignored. It is an **interface-contract gap identified by diff inspection**, not a claim of a production exploit or physical test.

**Provisional default-deny contract for owner review:**

1. An empty/unprovisioned key is not an authentication success. No keyless `"ok":true` response may enable coin intake.
2. Coin intake may be enabled only after a fresh poll response is authenticated by an approved provisioned key/signature and all response/target freshness checks pass.
3. Missing, malformed, expired or mismatched authentication must leave `insertMode=false`, clear the active target, and keep the physical output gate denied. No stale positive poll may be reused.
4. A separate setup/bootstrap path may remain available for provisioning, but it must not authorize coin admission.

This is a conservative proposed contract, not an implementation instruction. PHX-CORE and PHX-HARDWARE must agree on the provisioning/bootstrap boundary before code changes; PHX-QA must supply positive and negative tests at the combined exact head.

## 4. Rejected-event durability contract gap

PR #315's current failure latch is `journalRecoveryRequired`, which the hardware handover describes as RAM-only. It blocks same-boot retry but does not itself prove that a rejected coin event remains non-replayable after reboot.

**Provisional default-deny invariant for owner review:** when the controller rejects an event and local quarantine persistence fails, the event must remain durably pending or be durably marked for reconciliation before any rebooted process can retry or credit it. A RAM-only latch is insufficient evidence of cross-reboot safety. No retry, duplicate POST, credit, or relay admission is allowed while the durable disposition is ambiguous.

PHX-CORE owns the financial/replay semantics; PHX-HARDWARE owns the journal implementation; PHX-QA independently verifies reboot/failure cases. PHX-MASTER records the shared contract only and does not implement either subsystem.

## 5. BLAZE-COMMS conformance finding

PHX-HARDWARE's UTC22 control-plane comment [6931592263](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-6931592263) uses `to: "PHX-MASTER;PHX-QA;PHX-CORE"`. Current Master validator blob `3a6d0ca34cad54cd113abbda17d90898603547b3` accepts exactly one registered role or literal `ALL`; it rejects semicolon-separated recipients. The comment is preserved as historical evidence and was not edited. PHX-HARDWARE should publish any correction as a new envelope with `to: "PHX-MASTER"` or `to: "ALL"`.

## 6. Exact next actions

1. **PHX-HARDWARE:** consolidate #315 and #316 onto one linear branch; preserve quarantine append fail-closed and poll-response denial behavior; publish the new exact head.
2. **PHX-QA:** update its source extractor to include `acceptPollResponse()`; rerun the six-case poll matrix and the quarantine failure matrix against the consolidated exact SHA. Do not modify hardware source.
3. **PHX-CORE:** review keyless/bootstrap authority and durable rejected-event/replay semantics; publish a decision or explicit blocker on #172.
4. **PHX-MASTER:** keep this contract provisional until affected owners respond; update the architecture matrix only from exact new evidence.

No source subsystem branch was modified by PHX-MASTER. No merge, release, signing, flashing, physical test, live payment, migration or deployment occurred. Production remains **NO-GO**.
