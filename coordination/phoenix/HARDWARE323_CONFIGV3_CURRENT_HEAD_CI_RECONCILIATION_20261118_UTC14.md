# PHX-MASTER — ConfigV3 and exact-head integration reconciliation

**Snapshot:** 2026-11-18 14:59 UTC  
**Role:** PHX-MASTER — coordination/phoenix, architecture/interface contracts, cross-repository provenance only  
**Disposition:** BLOCKED / PRODUCTION NO-GO

## 1. Live repository and PR snapshot

- Experiments main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Experiments development: `aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Master branch before this update: `dbff4813dab323a908ebcd4cedeaf7ad847c0f4b`; existing PR #288 remains OPEN / DRAFT against main.
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- COE integration PR #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN / DRAFT; five workflows remain QUEUED with zero jobs.
- The ownership manifest is unchanged at blob `e4db324315a1b3543fec17a148fbf960170fcb29`, status DRAFT_REVIEW_ONLY, and PHX-MASTER target null.

## 2. Hardware PR #323 — current review candidate

Current live PR #323 head is `4dc5fd566da6ed3e523e3e15174837f5cfb8b183`, parent #322 at `50d93e0de3d682550b6f02fb43484e76ad9c7e08`. It remains OPEN / DRAFT / UNMERGED. No Master source takeover occurred.

The exact ESP8266 sketch blob is `283dbe329a5445931cc9fe7096561a68b9c8bf62`. It now has a versioned ConfigV3 record containing relay/LED polarity values, a validity flag and checksum. Both V1 and V2 migrations explicitly leave output polarity unconfigured. The boot path loads and validates configuration before runtime pin setup. Unknown polarity keeps relay/LED pins as INPUT; poll and coin-POST gates require the local polarity-valid flag. The WPA2 setup AP requires explicit 0/1 values for both polarities. EEPROM commit is followed by end/reopen/readback and a full record comparison.

The boot-polarity host lab blob is `d928ad30ddb81379dfc37d6c54df782036fff3cc`. The poll-loop mutation lab is `b915319b55f33b8961eb990def3fe305d0fe7143`; its harness now records interrupt attachment, so the remove-edge-interrupt mutation is rejected. The poll-window lab is `3c5541089ed61ae3f292785e013b375cea50fd64`; the poll-response lab is `49f7179f99d56e859fa7a672fe919f3c12c48427`. Relay workflow blob: `1140daf71d5218c9c58cdf74ae4cc3ab3822c51a`; quarantine workflow blob: `2358e4ab940b9879e961046180f01fc3d5356709`.

### Exact-head CI

- [Quarantine/readback 44329837932](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44329837932) — SUCCESS.
- [Relay/output polarity 44329837962](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44329837962) — SUCCESS.
- [Full BlazePwifi build 44329837987](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44329837987) — PENDING at the snapshot; no Full acceptance claimed.

The focused logs show the ConfigV3 cold-boot lab passing; relay polarity 48/48 scenarios per board; output-enable sequence 5/5; poll-window drain 11/11 per board; coin-pulse capture 8/8 per board; poll-response deny cases 11/11, strict JSON cases 13/13, and coin disposition default-deny 4/4; pending-journal recovery 16/16 and pending-clear 17/17 per board; pending write/readback 22/22 per board; coin-POST gate 10/10 per board; and poll-fault output inhibition before secondary-store/LittleFS persistence. The remove-edge-interrupt-attachment, no-op ISR, ignored poll-edge delta, removed fault marker and deferred output-inhibit mutations are rejected on both boards.

These are source-extracted host simulations and GitHub CI only. The logs explicitly report physical relay/coin/power-cut acceptance as zero. The ESP32 sketch remains a separate configuration path; the ESP8266 ConfigV3 profile is not evidence that ESP32 has an equivalent locally validated polarity profile. Both poll-response admission and coin-post disposition remain hard-deny.

## 3. Other current role and destination evidence

- CORE #252 head `c82705f2de865c89ab733b10efa84f26f56a5cc4`: scoped run [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS. CORE source was not changed.
- RENTAL #289 head `68928774d0d7cf65adb26bc6b54199a3159d066c`: [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) SUCCESS.
- PISONET #255 head `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09`: [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS.
- QA #290 head `5c29d15994cee1279058f1eca12f2a3180704292`: [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS. QA #292 head `75a3f66d9563e38a0a48b9cf487b0b057a91ea96`: no workflow runs returned.
- RELEASE #291 head `ed3565395bd70c4de696e49a84f0bb454efebc8b`: [44328674893](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44328674893) SUCCESS for handover and Windows build; publish-release SKIPPED.
- Hardware #318 remains on older base `3ed38225...`; #321, #322, #324 and #325 remain separate open draft candidates. No automatic composition or merge was performed.
- COE #35 latest observed head `af5e2618b706bddc5c11f005ab2b10eb039108da`: case-collision passed; shared-contract and mandatory sandbox workflows were still in progress at the snapshot. Its previous exact-head sandbox failure was caused by the runner lacking bubblewrap (exit 125); the current run must be checked before any revised conclusion.
- COE #26 remains queued and has no combined integration acceptance.

## 4. Governance, registry and execution limits

The current branch-protection endpoints for Experiments main, development, Master and COE main returned 403 Resource not accessible by integration. The repository rulesets endpoint returned an empty list. A prior successful readback reported protected=false, but current protection cannot be independently reverified with this permission set; a repository administrator must confirm and enforce protections.

The canonical private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not available through the connected tool surface. Library search found only a noncanonical historical checkpoint that references the registry; it was not substituted. No Google Drive connector was exposed. No private registry data or identifiers are reproduced here.

The full Master suite was not run: local Git clone failed because the container could not resolve github.com. Twelve bounded source-grounded assertions against the exact #323 source/test blobs passed, covering ConfigV3 fields, V1/V2 fail-closed migration, EEPROM readback, boot order, INPUT defaults, poll/coin deny gates, local-only polarity selection, response default-deny, host-only disclaimers and separate workflow invocation. This is not the full Master Python suite.

## 5. Required next actions

1. PHX-HARDWARE: finish the Full workflow at exact #323 head; refresh the PR description and keep physical polarity/relay acceptance NOT TESTED.
2. PHX-QA: independently review the exact #323 SHA and replace the stale positive poll-signature fixture with negative deny-behavior tests; do not weaken firmware or add synthetic signatures.
3. PHX-RELEASE / infrastructure: verify the current COE #35 shared/sandbox runs and provide an authorized bubblewrap-capable runner; no privileged install or unsandboxed fallback.
4. Repository administrator: configure and independently verify branch protection and required checks on main, development, Master and COE main.
5. Registry custodian: restore authorized access to v11 and newer corrections; keep private data off public GitHub.
6. COE integration owner: resolve #26 queued workflows, source/test/license provenance and ownership before any migration proposal.

No migration, merge, release, signing, secret provisioning, flashing, physical test or real-payment operation was performed.
