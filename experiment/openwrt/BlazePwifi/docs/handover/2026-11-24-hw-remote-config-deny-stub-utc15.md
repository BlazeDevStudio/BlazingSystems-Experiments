# PHX-HARDWARE handover — deny-only remote-config sentinel

**Updated:** 2026-11-24T15:38:11Z (UTC15 activation checkpoint)  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Task:** remove the dormant unauthenticated remote-config parser and preserve an explicit deny-only compatibility entrypoint  
**Issue:** [#177 — synchronous poll pulse-loss](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Cleanup gate:** [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266), still OPEN / 0 of 7  
**PR:** [#340 — pre-poll intake deny](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/340), OPEN / DRAFT / UNMERGED  
**Parent candidate:** [#283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283), OPEN / DRAFT / UNMERGED  
**Branch:** phoenix/hardware-prepoll-intake-deny-20261122-utc01  
**Source/test commit:** ccc8e875b5ab56630677df8aaf786132e40329ec  
**Schema-note commit:** 9bb3460d855d565cdd8ed287cf56dcc3465f84b8  
**Branch HEAD at this handover:** 9bb3460d855d565cdd8ed287cf56dcc3465f84b8  
**Parent #283 live head:** 4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30  
**Child PR base SHA reported by GitHub:** 88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d

## Source changes

Both child-branch sketches retained a dormant applyRemoteConfig implementation that parsed untrusted response text with permissive defaults: enabled, coin_enabled, relay_enabled, and led_enabled defaulted to 1. It had no callsite in the deny-only branch, but its latent behavior was unsafe if a future change wired it to the current unauthenticated register or poll response.

Changes on the PHX-HARDWARE-owned child branch:
- removed unused jsonString, jsonTrue, and jsonInt parser helpers;
- removed the unused remoteRevision state;
- retained applyRemoteConfig for existing structural compatibility, but it is now a deny-only sentinel that calls denyRemoteControl();
- documented config_revision, coin_debounce_ms, pulse_group_ms, and max_wifi_retries as reserved fields intentionally ignored until CORE publishes an authenticated configuration envelope;
- left request signing, CGI producer, relay polarity, journal format, coin admission, and financial behavior unchanged.

The current main CGI register/poll responses do not carry an authenticated response_sig for the controller configuration object. Hardware did not invent one, parse an unauthenticated positive response, or modify CORE/QA-owned files.

## Regression and exact CI evidence

The new Hardware-owned lab is:
experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/remote_config_deny_lab.py

It compiles the actual writeLogical(), applyOutputs(), denyRemoteControl(), and applyRemoteConfig() bodies from both sketches with g++ -std=c++17 -Wall -Wextra -Werror.

Per board it tests three payloads (empty, forged all-enable, forged revision/pin) under active-high and active-low output polarity. It verifies all controller/coin/relay/LED permissions OFF, insertMode=false, active target cleared, and relay/LED output de-energized. Failure injection removes the deny call; the host harness must fail.

| Workflow | Run / job | Result |
|---|---|---|
| Poll Preflight Intake Inhibit | [45431090415](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45431090415) / 138576253780 | PASS — poll deny/order mutations rejected on both boards; new remote-config lab passed on both boards; missing-deny mutation rejected on both |
| Quarantine Append Readback | [45431090459](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45431090459) / 138576254319 | PASS — clear/commit 10/10 scenarios per board; ignored-clear-result mutation rejected; append/readback failure paths remain fail-closed |
| ESP32 Mbed TLS SHA256 guard | [45431090295](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45431090295) / 138576253573 | PASS — provider, output, nonce, and empty-signature deny checks; mutation cases rejected |
| ESP32 Arduino core 3.3.13 compile | [45431090405](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45431090405) / 138577281292 | PASS |
| ESP8266 Arduino core 3.1.2 compile | [45431090577](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45431090577) / 138576712118 | PASS |
| Full BlazePwifi build | [45431090422](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45431090422) | IN PROGRESS at handover: validate PASS; 13 firmware targets plus Android PASS; update_bundle PASS; browser, ESP32/ESP8266 and several OpenWrt simulations PASS; x86, Ruijie, and Android emulator simulations still running; signing, release and prerelease publication SKIPPED |

Focused tests are CI VERIFIED but remain host/source-extracted simulations. No physical relay, coin pulse, power-cut or soak acceptance is inferred.

## Audit leads and ownership

- The earlier #283 unconditional clearPending-after-failed-quarantine-append lead is not present at the live #283 head: quarantinePending returns false after an unsuccessful append and only clears pending after a verified append. The Quarantine workflow above independently exercises 10/10 scenarios per board and rejects an ignored clear result.
- The response_sig / register-poll mismatch remains a contract issue, not a firmware permission to fabricate a signature. Current register/poll producer responses do not authenticate the returned configuration object.
- PHX-CORE owns the authenticated register/poll configuration producer contract and canonical response bytes.
- PHX-QA owns the legacy positive poll-signature and controller compatibility assertions, including independent source-linked negative tests. Existing grep-based compatibility checks are not proof that remote config is authenticated or accepted.
- PHX-MASTER owns stack direction and cross-role integration records.

## Stack freshness and repository coordination

PR #340 is still OPEN / DRAFT / UNMERGED and GitHub currently reports mergeable=true. However its base SHA is 88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d while the live #283 branch head is 4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30. Keep the child DRAFT; Master must reconcile exact stack ancestry before merge. No rebase, force-push, merge, or retarget was performed.

Other live refs rechecked:
- Experiments main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b
- Master coordination branch / PR #288: c915134d4d36221e02d4dd10d010bd6356392f9f
- Hardware PR #239: d83b715b116185107737fef721c2eece8feebf39
- Hardware PR #254: 84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9
- Parallel Hardware PR #283: 4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30
- Hardware parent #347: 960184670379f01e20f0e7e8bc23b3e5eedacd3f
- Hardware sibling #349: 7eab719485dca333f06c1cac844a3fc943564e9b
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243
- COE #26: b382d233ff06c8791b1028bed3c617cc7b670d12, OPEN / DRAFT / FROZEN

The old BlazingSystems owner API path returns Moved Permanently; the canonical repository is BlazeDevStudio/BlazingSystems-Experiments.

The private BLAZE_PROJECT_REGISTRY_v11_20261027.json remains unavailable: no Google Drive connector is exposed in this execution, and Library search did not find v11. Older registry snapshots were not substituted and no private data was copied.

## Production status

- Source change and focused host regressions: CI VERIFIED.
- Physical relay/electrical pulse acceptance: NOT TESTED.
- 150 real power cuts: NOT TESTED.
- 30-device / 24-hour soak: NOT TESTED.
- Protected anti-rollback signer/witness: NOT ACCEPTED.
- Durable accounting/replay and reversible v1-to-v2 migration: NOT ACCEPTED.
- Independent QA/release signoff: PENDING.

**HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.** No secrets, live money, physical flashing, device resets, production migration, release tagging, deployment, or Codex were used.
