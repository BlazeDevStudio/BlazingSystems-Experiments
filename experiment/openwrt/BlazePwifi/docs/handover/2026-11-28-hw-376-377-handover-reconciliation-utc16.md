# PHX-HARDWARE — #376/#377 handover reconciliation (UTC16)

Updated: 2026-11-28T16:03:49Z

## Branch sequencing

Keep #376 and #377 as independent Hardware drafts; do not merge, cherry-pick, or rebase one onto the other.

- #376: `phoenix/hw-storage-superblock-rw-guard-20261128-utc14@22ff6eb054b9578daf74a30d5c04d51fd754917e`, child of #356@0ea32d31ed5c902b2187d98c181aab14bc9fdeae. Read-only STORCHK-0674 parser/preflight.
- #377: `phoenix/hw-poll-deny-wrapper-child-20261128-utc15@95e54790ab986dab3c1b3723ea9603a3d125c0d6`, child of #374@cfb19ed5df920bf5fa7e33e08dc73a25f8b14db9, preserving #375@94b1231c631eb32da0f019604ce00a4a0851a471 as second parent. Deny-only poll candidate.
- Shared append-only handovers are reconciled by cross-reference; neither branch is the active v0.6 branch. Master retains integration authority.

## Exact-head evidence

#376:
- Focused #46157303529 / job 141016684329 PASS.
- Mbed #46157303545: source contract + core 3.3.13 + core 4.0.0 = 3/3 PASS.
- Full #46157303505: validation PASS; 14/14 target/platform jobs PASS; 9/9 simulations PASS; update bundle PASS; production import/sign/release stages skipped.
- Explicit evidence boundary: SIMULATED_ONLY=1, PHYSICAL_POWER_CUT_VERIFIED=0, CUSTOMER_INSTALL_AUTHORIZED=0.

#377:
- Poll #46158944089 PASS; Mbed #46158944181 3/3 PASS.
- Native #46158944131 FAIL at QA-owned PAY-0745 literal assertion.
- Full #46158944182 FAIL at QA-owned controller parity after 14/14 target/platform jobs PASS.

## Current blockers

- Active v0.6 branch remains 2fbd2475e9f54878c316fa7cea2f228386b0e859 and still performs synchronous poll before first coin sample on both boards; #177 remains OPEN.
- QA owns semantic PAY-0745 and controller-parity assertions; CORE owns authenticated register/poll/receipt/disposition.
- Physical pulse/relay/power acceptance, 150 cuts, 30-device/24-hour soak, protected witness/signer, durable accounting/replay, v1-to-v2 migration and independent QA/release acceptance remain unverified.

No firmware/API/finance source, COE destination, physical device, or production state changed in this reconciliation. Keep both drafts open and unmerged.
