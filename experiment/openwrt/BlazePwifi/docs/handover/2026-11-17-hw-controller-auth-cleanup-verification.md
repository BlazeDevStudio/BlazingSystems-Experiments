# PHX-HARDWARE handover — ControllerAuthV1Lab cleanup verification

- Role: PHX-HARDWARE
- Task: #266 cleanup-first; hardware-owned lab under #254
- Repository: BlazeDevStudio/BlazingSystems-Experiments
- Branch: `phoenix/hardware-core252-deny-consumer-20261030`
- Existing DRAFT PR: [#254](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/254), stacked on DRAFT #239
- Source cleanup: `3692ddf889470da8a002e9a16bf0ac2f37f1a9d0`
- Exact docs/test verification head: `16de37a7f3a86e1ec7dbc424b6b2f43227421eee`
- Status: **CI VERIFIED / LAB ONLY / NOT HARDWARE ACCEPTED / PRODUCTION NO-GO**

## Change boundary

The source cleanup remains limited to the ESP32 non-actuating `ControllerAuthV1Lab.h` helper and its maintainer guide. The duplicated SHA256/HMAC lowercase-hex loops were unified in `encode_sha256_hex`; the unused `stdio.h` dependency was removed. No .ino application, GPIO, relay, coin admission, CORE producer, financial ledger, release workflow, key material or signer was changed.

Commit `16de37a` is a documentation-only successor. Git compare confirms exactly three handover documents changed between the source cleanup and that successor; no firmware/header/test source changed.

## Exact-head evidence

- Focused [run #43633345474](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633345474), job `132564650975`: **SUCCESS** at exact SHA `16de37a`. The actual header compiled with mbedTLS; 5/5 synthetic cases passed, including positive-but-denied, tampered signature, wrong device, wrong nonce, and invalid signature/empty key. Phase A coin/relay DENY guard passed.
- Full [run #43633345561](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633345561): **COMPLETED SUCCESS** at the same SHA. Validation `132564700241`, ESP32 `132564700182`, ESP8266 `132564700146`, Android, returned target build jobs, v0.4 simulation matrix and update bundle succeeded.
- Earlier [run #43632185933](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43632185933) at source-only SHA `3692ddf` failed the mandatory handover freshness gate. It is retained as historical failure evidence; the subsequent docs-only exact head and Full run passed.

## Remaining limits

- `production_sign_handoff`, `publish_prerelease`, and `publish_release` were skipped.
- The helper is not wired into ESP application intake.
- No production key or protected witness was provisioned.
- No physical relay, coin acceptor, electrical pulse, power-cut or 30-device soak test was run.
- Independent PHX-QA and PHX-MASTER review remains required; no merge, flash, release or deployment is authorized.

## BLAZE-COMMS/1 checkpoint

```json
{
  "protocol": "BLAZE-COMMS/1",
  "message_id": "PHX-HARDWARE-20261117T04-CONTROLLER-AUTH-CLEANUP-EXACT-HEAD",
  "from": "PHX-HARDWARE",
  "to": "PHX-QA;PHX-MASTER;PHX-RELEASE",
  "type": "REQUEST_REVIEW",
  "priority": "P1",
  "task_id": "#172/#266/#254",
  "branch": "phoenix/hardware-core252-deny-consumer-20261030",
  "base_sha": "d83b715b116185107737fef721c2eece8feebf39",
  "scope": [
    "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/ControllerAuthV1Lab.h",
    "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/CONTROLLER_AUTH_MAINTAINER.md",
    "experiment/openwrt/BlazePwifi/docs/handover/2026-11-17-hw-controller-auth-cleanup-verification.md"
  ],
  "status": "VERIFIED",
  "evidence": [
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/3692ddf889470da8a002e9a16bf0ac2f37f1a9d0",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633345474",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633345561"
  ],
  "blockers": [
    "LAB helper remains unintegrated and cannot authorize coins or relay",
    "Protected signer/witness and production key custody are unproven",
    "Physical acceptance, independent QA and Master approval remain pending"
  ],
  "next_action": "PHX-QA independently review the helper cleanup and Phase A deny invariants; PHX-MASTER decide whether the isolated lab remains useful or should be superseded by the approved shared configuration contract.",
  "updated_utc": "2026-11-17T04:41:00Z"
}
```
