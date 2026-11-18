# Poll Response Producer/Consumer Contract Reconciliation — 2026-11-18 UTC08

**Role:** PHX-MASTER  
**Task:** #172 / #266 coordination and interface audit  
**Disposition:** DOCUMENTATION CORRECTION COMMITTED; poll authorization remains BLOCKED / PRODUCTION NO-GO.

## Executive finding

The current Experiments development CGI authenticates incoming request tuples but does not emit a signed response. Current HARDWARE #323 deliberately denies every poll response and every coin POST disposition. The legacy QA fixture still requires the literal `|poll|` string and therefore rejects this deny-only candidate. COE integration #26 contains a separate derived `response_sig` producer, but that construction is not an approved protocol and is not consumed by #323.

The correct next step is a QA-owned negative regression and a CORE-owned canonical response contract. Do not weaken firmware, copy the COE candidate, or claim positive admission.

## Exact refs read

| Item | Live ref |
|---|---|
| Experiments default branch | `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments development branch | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master PR #288 | `phoenix/master-coordination@9fb0d615c58731e488ea8f876e96d3e81425efb3`, base `main@f4e8a891...` |
| Hardware PR #323 | docs/head `4850b16a31a1ccb67f265e5224a2799b25cf2e01`; source/test `c13dfb8d9b7ae83c15aa97c94842c339db8b8584`; base #322 `50d93e0de3d682550b6f02fb43484e76ad9c7e08` |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| Ownership manifest | `OWNERSHIP_ROUTES.json@e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, Master target null |

## Producer/consumer evidence

### Experiments development producer

- `experiment/openwrt/BlazePwifi/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo`: blob `a1c19180385e618c412b4af21c0e91c1f47da1dd`.
- `common.sh`: blob `ca4920d3d9572382fb381a325183a18311be5954`.
- `controller.sh`: blob `54bdc59949884bd3e734f8c07ddeb1d7c2cf9848`.

`bp_check_vendo_sig()` validates the request signature. `bp_json()` only emits the supplied body. The current `register|ping`, `poll` and `coin` responses do not contain `response_sig`.

### COE #26 candidate producer

- `Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo`: blob `0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e`.

It defines `vendo_poll_sig()` and includes `response_sig` in poll JSON. Its digest is a keyed SHA-256 concatenation, not standard HMAC. No approved canonical schema, key/version lifecycle, shared golden vectors or exact combined-tree QA was found. This candidate is not accepted by #323.

### Current #323 consumer

- ESP8266 sketch blob: `8e79b9eb8856e67d966f4c6385f89fccdc8be7fc`.
- ESP32 sketch blob: `bd74b11c1496b0943404ff387ee72bb45d4743e5`.

Both `acceptPollResponse()` functions clear the target, set insertion false and return false. Both `coinPostDispositionVerified()` functions return false. Register response authentication also remains false when `response_sig` is absent, leaving remote configuration disabled.

## Exact CI readback

| Run | Result | What it establishes |
|---|---|---|
| [44262258247](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44262258247) | SUCCESS | Focused quarantine/readback host lab |
| [44262258937](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44262258937) | SUCCESS | Focused relay/output host lab |
| [44262258842](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44262258842) | FAILURE | Validation job 134658178171 reports `Missing poll signature check`; all 14 firmware target jobs and Android succeed; downstream import/update/simulation/sign/candidate/publish jobs skip |

The merge-tree QA fixture `v05_firmware_hardening_test.sh` blob `41211b2c110ab409f6d9d1812ef12fda73b13211` requires `response_sig` and `|poll|` string presence. It does not verify that the current deny-only behavior is safe. The entrypoint `controllers.sh` blob is `f7896647713d6bf8034ff48ed19b6383e4dedea0`.

COE #26 still has five queued workflows and zero jobs. No combined destination acceptance exists.

## Owner-routed next actions

- **PHX-QA:** replace the positive poll-string assertion with negative source-linked behavior tests for both boards, at the exact #323 source/test SHA. Verify missing/forged responses cannot enable intake and coin disposition stays denied.
- **PHX-CORE:** define the canonical response envelope, algorithm, key identity/version, nonce/target binding, freshness, canonical serialization and golden vectors. Do not call concatenated SHA-256 HMAC.
- **PHX-HARDWARE:** retain the fail-closed consumer until CORE and QA gates are met; refresh its own PR/handover.
- **PHX-RELEASE:** keep signing and publishing skipped while Full validation fails.
- **PHX-MASTER:** maintain contracts, matrix and provenance only; no subsystem source takeover.

## Registry, policy and execution limitations

Root Experiments `AGENTS.md` was read at blob `d8777e3b58efc41caa5aa3c969c932aee9103d5f`. It requires the private Drive registry, artifact manifest and sync ledger before any artifact movement. The canonical Drive v11 registry and newer corrections were not available in the exposed Library/Drive surface. No older registry snapshot was substituted and no private contents were published.

The AGENTS-linked cloud artifact policy and storage handover could not be retrieved through the available GitHub connector or web endpoint. COE root `AGENTS.md` returned 404. These are access blockers, not evidence that the documents are absent.

No local repository checkout or full Master Python suite was available because GitHub DNS resolution failed in the execution container. No Master PR-triggered CI run was returned for the pre-change head. The focused and Full CI outcomes above are real GitHub Actions evidence; no physical hardware test was performed.

No source file, destination file, payment record, secret, firmware image or hardware was changed. No migration, merge, release, signing, flashing or customer cutover occurred.

**Production remains NO-GO.**
