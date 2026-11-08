# BlazePwifi v0.6.0 — Physical durability & reversible migration acceptance

**Status:** TEST PROTOCOL ONLY / NOT EXECUTED / NOT CUSTOMER AUTHORIZED  
**Work item:** MULTICTL-0673 (2026-10-09, Asia/Manila)  
**Evidence baseline:** v0.6.0 draft PR #30, source `2ad44a61e978b86be8b19c0f98a34e9517684c0b`. The first three-target SDK binary compilation is proven by GitHub CI; persistent-media powercut validation is NOT.

## Critical distinction: /tmp is not persistent flash

The existing native journal is deliberately **fixture-only** and its root is restricted to `/tmp/blaze-v2-native-*` (`BLAZE_FIXTURE_ONLY`, private synthetic marker). On common OpenWrt targets `/tmp` is **tmpfs**. Unplugging such a device destroys the synthetic directory. Therefore simply power-cutting the current fixture under plain `/tmp` **cannot prove power-loss durability**.

A legitimate hardware experiment needs a disposable, physically persistent scratch filesystem, with a single synthetic fixture directory bind-mounted *at the existing /tmp guard path*, after explicitly verifying the bind mount resolves to the scratch storage. Do not change the program's permitted root prefix or remove its fixture guard to obtain a passing result. Do not use customer `/overlay`, `/etc`, real payment directories, live router flash partitions, or shared persistent state. Mount setup and partition handling require operator review; this document intentionally does **not** supply destructive partitioning commands or authorize remote execution.

No test result is valid unless the backing mount/flash device, filesystem, and actual persistence after unclean reboot are evidenced. A successful GitHub-hosted simulation or clean software restart is not physical power-loss evidence.

## Read-only operator scratch-mount preflight (STORCHK-0674)

A LAB-only fail-closed mountinfo inspection has been added:

```sh
sh tools/v060_lab_storage_preflight.sh \
  /tmp/blaze-v2-native-test01 \
  /dev/DEDICATED_SCRATCH_PARTITION \
  /mnt/blaze-v2-lab-media-test01
```

**This command does not create a mount, modify storage, run a financial transaction, or switch production on.** Before invocation, the operator must arrange a **real dedicated scratch filesystem** mounted beneath `/mnt/blaze-v2-lab-media-*`, with a private *subdirectory* bind-mounted exactly at the isolated `/tmp/blaze-v2-native-*` test fixture root. The root must contain the existing private `.blaze-v2-fixture-only` marker and permissions used by the synthetic native journal. The second argument must be the actual expected scratch *block* source and must agree with `/proc/self/mountinfo`; loop, ram, overlay, tmpfs and misidentified mounts are rejected. Nothing authorizes mounting on any real customer partition or using `/overlay`.

The preflight verifies exact mountpoint/source/major-minor/filesystem relationships and a private fixture marker using the **actual process mount namespace**; it rejects generic `/tmp` and ambiguous stacked mounts. It is deliberately conservative (ext4, f2fs, xfs or btrfs scratch sources) and may refuse otherwise usable storage; operator manual review is required, never a bypass. These checks are based on the Linux kernel mountinfo format (see https://www.kernel.org/doc/html/latest/filesystems/proc.html). The separate `tests/v060_lab_storage_preflight.sh` uses **text-only fake mountinfo input** to verify fail-closed behavior in CI; passing that test does not establish real storage persistence.

Even a successful operator preflight prints `physical_powercut_verified=0` and `customer_install_authorized=0`. It only allows **consideration** of a controlled physical experiment after independent confirmation of the isolated scratch device. It never authorizes an actual power interruption, changes the native fixture's accepted root or releases a customer build.

## HWPRE-0683 — read-only, on-device scratch-media observation

On a deliberately isolated, **operator-approved noncustomer appliance**, after an operator has separately prepared a dedicated disposable persistent block partition and its correctly private bind-mounted `/tmp/blaze-v2-native-*` fixture, this lightweight shell-only command can inspect the *current* kernel mount namespace without Python or network access:

```sh
sh tools/v060_physical_pretrial_readonly.sh \
  /tmp/blaze-v2-native-OPERATOR_FIXTURE \
  /dev/DEDICATED_DISPOSABLE_BLOCK_PARTITION \
  /mnt/blaze-v2-lab-media-OPERATOR_FIXTURE
```

The command calls the existing `v060_lab_storage_preflight.sh` (fixture marker, private permissions, actual mountinfo relationship, writable allowed persistent filesystem) and adds the requirement that the expected `/dev/*` path be an **existing, non-symlink block-special device**. This closes the gap where a plausible device-name string alone could be treated as sufficient evidence. It reports local kernel and architecture metadata and **only** a pretrial observation. It does **not** perform any mount, write, power cut, payment, network request, artifact upload, off-device evidence verification or customer installation. Do not copy real hardware identifiers, secrets, customer data or whole operator output into public Git/CI.

On an ordinary Linux machine, CI runner, volatile `/tmp` directory or an unsupported OpenWrt layout, the command should BLOCK. A successful observation would still report `physical_powercut_verified=0`, `actual_hardware_powercuts_completed=0`, `offdevice_power_controller_authenticated=0`, `financial_migration_authorized=0` and `customer_install_authorized=0`. It cannot prove the partition is disposable or assess the physical safety of cutting power, which requires independent operator review. In particular, NEVER choose a boot, overlay, customer data or removable drive containing important files simply to make the preflight pass.

`tests/v060_physical_pretrial_readonly.sh` in Full CI performs **only negative tests** using a throwaway private marker and nonblock/unsafe device paths. It does not run the positive case, simulate an authorized owner, create a mount or obtain genuine power-loss telemetry. A CI pass is no substitute for the real controlled physical trial or human acceptance.

## Equipment & operator authorization (hard preflight)

All items must be recorded for *each physical target* — Ruijie RG-EW1200G Pro MIPS, Orange Pi Zero 3 AArch64 and x86-64:

- Dedicated non-customer hardware, isolated LAN, no production coin acceptor or active vending/rental stations.
- Physical power controller capable of removing supply power at recorded checkpoints; safe supply protection and recovery access. Never disconnect power to equipment holding customer balances.
- Dedicated disposable persistent storage with explicit capacity, mount source, filesystem (and barriers/journaling mode), kernel and storage model. Prove the `/tmp/blaze-v2-native-*` path is a bind mount into **this** scratch storage, not plain tmpfs.
- Verified SHA-256 of lab executable and package, target ELF machine, OpenWrt 25.12.5 ABI, target-specific SDK run, and no source from another architecture. Lab `.apk` must never be distributed to customers.
- Fixture-only fake controllers/accounts, randomly generated **test** HMAC keys, private marker, private directory 0700/files 0600. Use no exported live accounts, member secrets, signing keys, enrollments or transaction IDs.
- Authorized operator, fixture backup/snapshot plan and immutable off-device logging. Abort if mount/fixture/source ownership checks fail.
- Confirm the running binary has **no** customer CGI endpoint, init service or packet listener. A local synthetic CLI is not live payment authority.

## Required test cases, each with independent recorded start/end state

1. **Baseline/replay:** independent controller A and B keys, interleaved paid-credit, spend, transfer and lease operations on a shared synthetic bank. Record unique event IDs, exact signed input, durable ACK/replay classification, expected and actual balances, controller high-water marks and immutable receipt identity. Never log test keys or actual HMAC secrets.
2. **Bad input:** altered signed payload, wrong controller key, stale sequence outside the retained receipt window, same event with changed amount, skipped sequence, missing protected marker, symlink/hardlink/permission tamper. Each must fail with **zero ledger mutation and zero payment ACK**.
3. **Synthetic deterministic fault stages:** `before-source-fsync`, `before-rename`, `after-rename-before-dir-fsync`, and `after-dir-fsync-before-ack` (the names currently supported by the fixture). These software faults test state-machine behavior but are NOT evidence of a real power cut.
4. **Actual supply interruption on scratch persistent mount:** use instrumented operator-controlled shutdown at corresponding write/rename/dirsync/ACK boundaries (not arbitrary wall-clock delays). On reboot, mount/recover scratch storage without rewriting it; record ledger bytes before any replay attempt. Old state or new state may be valid at uncertain commit boundaries, but **never a partially valid balance/receipt pair**. No success ACK may be asserted for unknown durability.
5. **Replay after uncertain outcome:** resend the **same** signed controller ID, sequence and payload. If committed, return the stored outcome without new money/time; if not committed, the retry may commit once. Controller sequence high-water, member sums and rental lease must remain coherent. Never resolve uncertainty by minting an extra credit or overwriting a corrupt journal.
6. **Unavailable or full storage:** read-only mount, ENOSPC, EIO and sudden disconnection must fail closed and preserve an auditable uncertain state. Safe recovery is required before resuming paid ingress. Restore only from validated isolated snapshots.
7. **Sustained soak:** operate 30 synthetic mixed device identities (Wi-Fi, two independent Windows controllers, Android rental lease fixtures) with network loss, process restarts and concurrent requests. Performance, accuracy, and lost/duplicate ACK counts require genuine captured measurements; do not report synthetic input as successful real device enrollment.

Each physical platform should complete **at least 10 independent power interruptions at each of five checkpoint classes** (including post-commit/ACK-lost), plus a 24-hour isolated mixed-client run before being considered for field qualification. More iterations may be necessary for SSD wear-leveling, flash translation layers or flaky power supplies. These are minimum proposed acceptance targets, not completed test claims.

## v1 financial migration design gate (do not execute on customer data yet)

1. **No live conversion without explicit release approval.** Freeze coin/rental/Windows incoming writes, let in-flight events resolve and obtain evidence that no writer or pending unacknowledged event remains. If a pending/uncertain payment exists, block migration and reconcile manually.
2. Take encrypted **off-device** snapshot of existing v1 member, account, voucher, rental, controller replay and audit records, configuration and owner credentials through an owner-reviewed backup process. Do not print sensitive payloads into Actions logs or Git.
3. Under a throwaway synthetic copy first, perform deterministic mapping with an immutable migration ID/source snapshot digest, idempotent per-record identity and collision rules. Refuse unknown columns, duplicate owners, out-of-range seconds, corrupt history, key mismatches or ambiguous receipt status; do not silently reset credit to zero.
4. Check exact conservation across every supported unit: total banked seconds, active paid session expiry policy, outstanding rental lease time, unredeemed vouchers, controller high-water/event receipt history, and pending refunds/chargebacks; a cash amount is not interchangeable with seconds without a locked rate revision.
5. Stage v2 files on the same scratch filesystem, fsync file and parent directories, write a non-bypassable migration commit marker referencing the source digest and destination digest. Any interrupted conversion remains resolvable to exactly one authoritative version; no dual writer and no automatic replay before reconciliation.
6. Validate restoration in both directions **using the untouched encrypted source snapshot** and original signer/identity. A rollback must not discard paid v2 transactions made since migration; require quiescence and a replay/reconciliation plan before falling back.
7. Record manual owner sign-off separately for money integrity, operational recovery and native Android Lineage-2 Device Owner enrollment. All three are required before production promotion.

**Current state:** No v1-to-v2 migration converter or owner-approved rollback has passed a real hardware/financial cutover. This checklist is acceptance design only.

## Evidence record (one per target *and* physical trial)

Store a redacted immutable JSON report off-device with:
- `candidate_git_sha`, `build_run_id`, `sdk_job_id`, `package_sha256`, `native_elf_sha256`, `target_arch`, `firmware_version`;
- `hardware_model`, `hardware_revision`, `storage_model`, `persistent_mount_source`, `filesystem_type`, `scratch_only_verified`;
- `test_case`, `trial_index`, `power_controller_event_time`, `fault_checkpoint`, `pre_state_sha256`, `post_state_sha256`;
- `controller_id_redacted`, `event_id_redacted`, `expected_ack_kind`, `actual_ack_kind`, `credit_delta_seconds`, `total_seconds_before`, `total_seconds_after`, `receipts_consistent`, `replay_duplicate_count`;
- `operator_signoff`, `test_outcome` = `pass` or `fail`, `failure_log_reference`, `recovery_steps`.

Do not store plaintext keys, customer identifying information, production HMACs, transfer-password recovery contents or private Android signing material in these reports or public Git.

## PEVID-0679 — read-only *structural* trial-evidence review (NOT hardware certification)

The repository includes \`tools/v060_physical_evidence_contract.py\`, which accepts only a
private **local inspection fixture** (\`/tmp/blaze-v2-evidence-*\`, owner 0700) with
a 0600 \`manifest.json\`, a private 0600
\`.blaze-physical-evidence-fixture-only\` containing exactly
\`BLAZE-POWER-CUT-STRUCTURE-NOT-HARDWARE-PROOF\n\`, and a 0700 \`captures/\`
directory containing privately held 0600 digest-referenced log files.

\`\`\`sh
python3 tools/v060_physical_evidence_contract.py --root /tmp/blaze-v2-evidence-OPERATOR_REVIEW_COPY
\`\`\`

The closed-format \`manifest.json\` uses schema
\`blaze-v060-physical-evidence-structure/1\`, \`fixture_only: true\`,
\`claim_origin: "operator-claimed-unverified"\`, a full 40-character lowercase hexadecimal Git SHA-1 commit ID (\`candidate_git_sha\`),
150 claimed trials (each of three architectures × five physical fault
checkpoints × trials 1–10), and one claimed ≥86,400-second/≥30-client soak
for each architecture. Required trial observations include exact target
identity, package digest, persistent scratch source and filesystem, before/after
state hashes, claimed applied seconds and observed totals, unique redacted
event references, zero duplicate ACKs, replay/receipt consistency, UTC power
event timestamp, and two **distinct** content-hash-verified capture logs for
power-controller observation and recovered state. The five checkpoint classes
are \`before-source-fsync\`, \`before-rename\`,
\`after-rename-before-dir-fsync\`, \`after-dir-fsync-before-ack\`, and
\`after-ack-observed\`. The final class requires operator-confirmed ACK receipt,
not merely a simulator calling an ACK handler.

This parser can reject omitted trials, wrong amounts, duplicate IDs, reused
captures, missing soak results, altered or linked log files, insufficient
private permissions and synthetic-claim schema misuse. It CANNOT independently
attest a power interruption took place, prove boot media persistence, verify an
operator's identity, authenticate an external power controller, or infer an
actual 24-hour soak from a reported duration. Therefore even when every
structural check passes, the **only** success status is
\`STRUCTURE_READY_FOR_INDEPENDENT_REVIEW\`, accompanied by
\`physical_powercut_verified: false\` and
\`production_release_authorized: false\`. A result of \`BLOCKED\` is a refusal.

The matching \`tests/v060_physical_evidence_contract.py\` creates entirely
**MOCKED CI records**, not real operator captures. They exercise the checker
but MUST NEVER be submitted as genuine trial evidence. Real acquisition,
external immutable custody, signed controller telemetry, operator review,
real per-device hardware identifiers, reproducible native build hashes, and
owner acceptance remain separate; this tool does not gather or upload data.

## PEVID-0680 — independent physical-event chronology and capture anti-copy rule

A claim of 150 distinct hardware interruptions must not reuse one timestamp for every observation. The LAB-only structural checker now rejects impossible calendar dates and duplicate UTC-second `power_event_time_utc` claims across the trial manifest, and rejects identical SHA-256 capture contents copied under different filenames, even when the modified manifest supplies the matching digest. The fixture regression creates unique mock event timestamps, injects repeated/impossible dates, and copies one log to another with a recomputed digest to prove refusal.

This is a **quality gate for claimed evidence**, not an authenticated power controller, clock attestation, verified event sequence, or independent hardware observation. When two trials genuinely occur within the same second, the operator must obtain independent higher-resolution timing/provenance and request an explicitly reviewed schema revision, **not** alter a timestamp to trick the checker. The existing `physical_powercut_verified=false` and production NO-GO policy remain mandatory even when the complete structural gate passes.

## PEVID-0682 — changes during a structural review (not a snapshot)

A structural evidence bundle may be modified during a long review even when
its initial capture checks all pass. The read-only checker now performs a
second pass over every referenced capture's private metadata and SHA-256,
rechecks the initial bytes/identity of the private manifest and fixture
marker, and rechecks the root/captures directory identity and listing.

`tests/v060_physical_evidence_contract.py` injects four deterministic changes
**after** the final claimed capture is inspected: modifying an early capture,
replacing it with the same bytes, editing the manifest and adding a new
capture. Each must refuse `STRUCTURE_READY_FOR_INDEPENDENT_REVIEW` with a
redacted `BLOCKED` result. This is entirely **MOCKED CI**, not a real
hardware interruption. Repeat reads merely detect some concurrent changes;
they are **not** an atomic multi-file snapshot and cannot authenticate
operator captures, prove power removal, override source-owned quiescence,
or authorize any financial migration or customer install.

## Release NO-GO checklist

**PASS requires actual evidence, not self-assertion.** Any incomplete/failed case leaves `PRODUCTION_v0.6.0_RELEASED=0` and `CUSTOMER_INSTALL_AUTHORIZED=0`.

- [ ] All three named physical targets with persistent-media, power-cut and recovery evidence
- [ ] All shared-ledger financial invariants and duplicate/replay protections confirmed
- [ ] Reversible/quiesced encrypted v1 cutover on disposable copy and owner-approved paid migration
- [ ] 30-client/24h real controller + rental + Windows interoperability and network resilience
- [ ] Permanent Lineage-2 signed Android current/rescue APK, factory-reset Device Owner and standard binding acceptance
- [ ] Exact-SHA release build, installable per-target image/EXE/APK/INO, SHA256SUMS, transparent risk disclosure and owner production sign-off

If interrupted, resume by reviewing `PROJECT_HANDOVER.md`, `docs/handover/CURRENT_STATE.md` and `docs/handover/CHANGE_LEDGER.md`. Do not claim these tests were run merely because this protocol exists.
