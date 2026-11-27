# BlazePwifi v0.5.3-dev.5 — ZeroTier Live Activation Green Candidate

Date: 2026-10-07

## Scope

This development slice adds transactional ZeroTier live activation to Full/Standard BlazePwifi while preserving the frozen v0.5.2 production release and keeping `profiles/standalone-rental` reference-only.

## Identity

- VERSION: `0.5.3-dev.5`
- BlazeRental versionName: `0.5.3-dev.5`
- BlazeRental development versionCode: `50294`
- Development range: `50290–50298`
- Frozen v0.5.2 rescue: `50299`
- Final v0.5.3 production code remains reserved at `50300`

No production v0.5.3 tag/release/signing action was performed.

## ZeroTier ownership and secret handling

BlazePwifi uses the current OpenWrt ZeroTier UCI model:

- `zerotier.global=zerotier`
- stable `zerotier.global.secret`
- Blaze-owned `zerotier.blazepwifi=network`
- `allow_managed=1`
- `allow_global=0`
- `allow_default=0`
- `allow_dns=0`

Safety rules:

- The ZeroTier secret is generated/stored on-device only.
- The secret is never returned to browser/API/log/audit output.
- Only the 10-character public node ID is exposed.
- Legacy `.join` layouts are refused.
- Foreign/custom ZeroTier network sections are refused.
- The stock `earth` sample is pruned only when it is still untouched/default, global ZeroTier is disabled and the secret is empty.
- Lite/Ruijie targets do not gain the ZeroTier runtime package.

## Transactional live apply

ZeroTier apply is accepted only after all of the following succeed:

1. valid staged ZeroTier profile;
2. stable local node identity;
3. transaction snapshot and pending journal;
4. Blaze-owned UCI write;
5. ZeroTier service restart;
6. node state ONLINE or TUNNELED;
7. target network status OK;
8. actual ZeroTier interface discovered;
9. assigned IPv4 address;
10. mesh route validation:
   - no default route;
   - no overly broad route;
   - no overlap with other directly-connected networks;
   - management allowlist must lie inside the accepted mesh route;
   - the current admin path must not be captured;
11. restricted firewall zone/rule creation;
12. dedicated restricted remote-admin listener;
13. unchanged default/current management route signatures.

WireGuard and ZeroTier cannot be active simultaneously.

## Rollback and recovery

The rollback snapshot contains:

- network config;
- firewall config;
- generic remote runtime;
- ZeroTier config;
- ZeroTier runtime.

Snapshots are restrictive because they may contain ZeroTier identity secret material.

Apply/disable failure paths include:

- ACCESS_DENIED / non-OK network status;
- missing interface or IPv4;
- unsafe managed routes;
- route overlap or management capture;
- firewall failure;
- remote-admin listener failure;
- service restart failure;
- watchdog timeout;
- reboot during transaction;
- lost transaction ownership.

Rollback restores the previous live transport/runtime and deletes the secret-bearing snapshot after restore.

Disable must be initiated from a local/non-ZeroTier management path. Stable node identity persists for future re-enable.

## Real bugs found during validation

### Pre-transaction identity mutation

The initial dev.5 implementation unconditionally rewrote and committed an already-valid `zerotier.global.secret` before transaction snapshot creation.

That changed UCI line ordering and proved that the live configuration had been mutated outside the rollback boundary.

Fix:

- existing valid secret is now a true no-op;
- global type/enabled are written only when missing/incorrect;
- UCI commit occurs only when identity preparation actually changes config.

### Transaction-engine corruption during the fix

A tooling replacement used JavaScript `String.replace(old, replacementString)` while the shell replacement text contained the regex suffix `$'`.

JavaScript interpreted `$'` as the special “suffix after match” token, which duplicated the remainder of `remote_apply.sh`, truncated the identity regex and appended stale ZeroTier code after the authoritative EOF marker.

The candidate was repaired by rebuilding `remote_apply.sh` from clean dev.5 commit `e3aa76944ca185ec3da08f22873e3006e094190a`, then applying the identity no-op fix with a replacement callback so the shell `$'` sequence remained literal.

Final integrity:

- one authoritative engine;
- one `bp_remote_zt_identity_prepare()`;
- valid shell syntax;
- one authoritative EOF seal;
- no code after EOF.

## Exact green candidate

Application candidate:

`29a3815e81c9bd7db54c8f60eb6f579c818f34ad`

Push workflow:

`37540065074` — PASS

PR #25 synthetic merge-tree workflow:

`37540072921` — PASS

Both passed:

- static/security/config validation;
- WireGuard network-survival regression;
- ZeroTier network-survival regression;
- centralized SoftTimer member regression;
- dev.4 metadata migration regression;
- accounting/replay stress;
- browser runtime;
- Android current + v0.5.2 rescue builds;
- Android Device Owner emulator;
- ESP8266/ESP32;
- Ruijie;
- required Orange Pi targets;
- x86_64 QEMU;
- transactional update bundle;
- final candidate gate.

## Browser evidence

Retained artifact `BlazePwifi-v0.5-browser-simulation` from push workflow `37540065074` reports:

- `remote_profile_saved=true`
- `wireguard_live_apply=true`
- `wireguard_staged_edit=true`
- `wireguard_safe_disable=true`
- `zerotier_identity_prepared=true`
- `zerotier_live_apply=true`
- `zerotier_safe_disable=true`
- `advanced_terminal_session=true`
- `member_metadata_export=true`
- `member_import_preview=true`
- `member_import_apply=true`
- `dual_csrf_transport=true`
- `portal_session_countdown_live=true`
- `portal_coin_window_countdown_live=true`
- `console_errors=false`

## Release guard

This is a development candidate only.

Before final v0.5.3 production:

- reconcile remaining approved v0.5.3 scope;
- move Android to versionCode `50300` / versionName `0.5.3`;
- run exact full candidate matrix again;
- sign BlazeRental with the permanent Lineage 2 production signer;
- verify package upgrade/signing fingerprint;
- generate Device Owner provisioning checksum/QR from the final signed APK;
- verify WireGuard and ZeroTier rollback/recovery on final release assets;
- publish only after exact signed candidate and recovery path are green.
