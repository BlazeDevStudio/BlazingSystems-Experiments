# PHX-HARDWARE handover — deny-only remote-config sentinel

**Updated:** 2026-11-24T15:38:11Z  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Task:** remove the dormant unauthenticated remote-config parser and preserve an explicit deny-only compatibility entrypoint  
**Issue:** [#177 — synchronous poll pulse-loss](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Cleanup gate:** [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
**PR:** [#340 — pre-poll intake deny](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/340), OPEN / DRAFT / UNMERGED  
**Parent candidate:** [#283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283), OPEN / DRAFT / UNMERGED  
**Branch:** phoenix/hardware-prepoll-intake-deny-20261122-utc01  
**Parent PR head at start:** 4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30  
**Child PR base SHA currently reported by GitHub:** 88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d

## Why this cleanup is safe

Both child-branch sketches retained a dormant applyRemoteConfig implementation that parsed untrusted response text with permissive defaults: enabled, coin_enabled, relay_enabled, and led_enabled defaulted to 1. The function had no callsite in the deny-only branch, but its latent behavior was unsafe if a future change wired it to the current unauthenticated register or poll response.

The current branch already denies remote actuation and keeps register/poll as discovery only. The cleanup therefore:
- removes unused jsonString, jsonTrue, and jsonInt helpers;
- removes the unused remoteRevision state;
- preserves the applyRemoteConfig symbol for existing structural compatibility, but changes it to a deny-only sentinel that calls denyRemoteControl();
- leaves both sketches' request format, CGI producer, relay polarity, journal format, coin admission, and financial behavior unchanged.

The controllers.sh structural check still finds applyRemoteConfig, but no parser or remote-field enable path remains. No QA-owned file was changed.

## Regression design

New Hardware-owned source-extracted lab:

experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/remote_config_deny_lab.py

The lab compiles the actual writeLogical(), applyOutputs(), denyRemoteControl(), and applyRemoteConfig() bodies from both sketches with g++ -std=c++17 -Wall -Wextra -Werror.

Per board it tests:
- empty response;
- a partial/forged all-enable object;
- a forged revision/pin object;
- active-high and active-low relay/LED output polarity;
- all controller/coin/relay/LED permissions OFF, insertMode=false, and active target cleared;
- failure injection removing the deny call, which must fail the host harness.

Expected host-only coverage: 6 payload/polarity cases per board (12 total), plus one rejected missing-deny mutation per board.

The exact-source workflow .github/workflows/phx-hw-poll-preflight-inhibit.yml now runs both the existing poll-preflight lab and the new remote-config deny lab. GitHub Actions evidence is pending for the new source/test commit.

## Coordination and limitations

- PHX-CORE owns the authenticated register/poll configuration producer contract.
- PHX-QA owns the legacy response_sig/|poll| assertions in tests/v05_firmware_hardening_test.sh and independent contract vectors. Hardware did not edit those files or invent a response signature.
- The #340 PR base SHA remains the earlier 88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d while the live #283 branch is 4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30. Keep this child DRAFT; Master must reconcile stack ancestry before merge. No rebase or force-push was performed.

**Classification:** host source-extracted tests = SIMULATED / CI pending; physical relay/electrical acceptance = NOT TESTED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
