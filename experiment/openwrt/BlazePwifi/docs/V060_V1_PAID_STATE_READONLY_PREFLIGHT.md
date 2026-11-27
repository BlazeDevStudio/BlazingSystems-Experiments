# BlazePwifi 0.6.0 migration: read-only v1 paid-state discovery

**MIG-0645 · Development fixture only · Not an installation, conversion or customer-data backup.**

Before attempting a v1-to-v2 cutover, BlazePwifi must discover and validate **every source of paid balances and replay receipts** with no service writes. New firmware may not infer a zero balance from a missing or corrupt record. Physical devices may have mixed 0.5.x histories, partially redeemed vouchers, controller events, rental leases and deleted account IDs. A disconnected preflight report is insufficient until operators explicitly quiesce coin acceptors, Wi-Fi portal payments, SoftTimer cashier clients and rental payments.

## What the implemented test actually checks

`tools/v060_v1_inventory_fixture.py` is **deliberately limited to disposable `/tmp/blaze-v1-audit-*` directories** bearing a private sentinel. It reads through a directory file descriptor, refuses symlinks, hardlinks and unsafe modes, caps file sizes, verifies source descriptors have not changed during each read, and checks:

| Data | Read-only checks | Not yet verified |
|---|---|---|
| `accounts.tsv` | Unique account ID, 9-field schema, integer credit/time, paused flag, aggregate Wi-Fi cents | Controller origin/signature, historical receipts, live timer conversion |
| `members.tsv` | Unique member ID, 11 fields, positive banked seconds, member revision floor | Cross-platform same-transaction receipts and administrator identity |
| `member-events.tsv` | Unique event IDs, 8 fields, numeric deltas and results | Entire unbounded prior history and external cashier ACK reconciliation |
| `rental-devices.tsv` / `rental-events.tsv` | Unique device/paid receipt, lease integer and expected fields | OEM Device Owner binding, signed lease and installed-APK state |
| `vouchers.tsv` | Unique voucher ID, 2/3 fields, positive/zero denomination | Independent redemption ledger and physical coins accepted |
| Optional `credits.tsv` / `sessions.tsv` | Two-column legacy entries, uniqueness and numeric values | Correct de-duplication against newer device credits |
| `targets/*.tsv` | Private files and six-field source windows | Quiesced electrical coin acceptor and unacknowledged in-flight payments |
| `paid-state-uncertain` | Financial quarantine marker forces BLOCKED | Operator-level signed reconciliation |

Only redacted **record counts and aggregate balances** are printed. No usernames, device IDs, voucher codes, bank details, signing secrets, original rows or private file hashes may be emitted. Any unsupported row structure, missing required fixture record, non-private source or uncertain financial marker fails closed with a stable diagnostic code.

A clean fixture returns `SCHEMA_READABLE_UNQUIESCED` and **always** sets `migration_authorized:false`, `quiesced:false`, and `balances_verified_against_external_receipts:false`. Exit zero means *this limited lab schema inspection passed*, **not** that conversion, backup, restore or customer installation is permitted.

## Reproduce in CI or an isolated developer workspace

```sh
python3 experiment/openwrt/BlazePwifi/tests/v060_v1_inventory_fixture.py
```

The test creates only synthetic temporary directories and tests deliberate corruption, duplicate IDs, legacy inconsistencies, symlinks/hardlinks, missing markers and quarantine. Do not copy production business TSVs into a public runner to execute it. The existing source contracts still block every 0.6-family update.

## Required next stage before migration can be enabled

1. Compile verified deployed-version schemas (including unknown optional/vendor fields) and a complete on-device file inventory; no fabricated default account balances or signed receipt floors.
2. Implement read-only, operator-approved **maintenance freeze** across all four money endpoints and physical coin acceptors. Drain/controller-ACK in-flight operations and verify that no paid writer can mutate the source while snapshotting.
3. Create encrypted, authenticated, private, durable backup of **all** program/config/credential/member/rental/customer state. Verify both bytes and ownership/mode; store outside the future update overwrite boundary.
4. Generate an isolated canonical v2 ledger and reconcile each source bank/voucher/lease to independently captured previous receipt and current floor. If data is ambiguous, **stop and preserve it**; never silently set to zero or multiply credit.
5. Use a signed fsync/dirsync-backed migration journal with PREPARED → BACKED_UP → MIGRATING → VERIFIED → COMMITTED transitions. Prove safe reboot at every transition on the exact Ruijie, Orange Pi and x86 storage format.
6. Reopen payments only after all readers and controllers use the same durable journal. Never roll back an older money snapshot after new transactions were accepted.

**Release decision:** v0.6.0 production remains blocked. Public v0.6.0-alpha.3 is an immutable **lab prerelease** built before MIG-0645 and does not include this tool. See `RELEASE_0.6.0_MIGRATION.md`, `LEDGER_TRANSACTION_V060.md`, and `docs/handover/CURRENT_STATE.md`.
