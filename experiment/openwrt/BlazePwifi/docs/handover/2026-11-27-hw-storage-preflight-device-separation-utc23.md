# PHX-HARDWARE — STORCHK-0674 root/overlay device separation

**Observed:** 2026-11-26T23:45:00Z
**Issue:** https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/34
**Draft PR:** https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/356
**Branch:** phoenix/hardware-storage-preflight-device-separation-20261126-utc23
**Base:** blazepwifi-v0.6.0-audit-foundation @ 2fbd2475e9f54878c316fa7cea2f228386b0e859
**Test-only commit:** 68907bfa993c1b6b635e41e0935193c80126b7ac

## Defect

The existing read-only preflight parser verified that the synthetic fixture bind mount and scratch mount share one expected block-device identity. It rejected obvious /dev/root, loop, ram, MTD, UBI, NBD and overlay path strings, but did not compare the scratch major:minor with the actual mount identities for /, /overlay, /rom or /boot. A plausible device path could therefore identify the same mounted system partition while avoiding the string deny-list.

## Test-first evidence

- Push RED #45912530609, job 140224038590: expected failure at scratch reuses root filesystem block device.
- PR RED #45912560098, job 140224138127: same expected failure.
- Full run #45912530717, validation job 140224091948: handover freshness failed because the test-only commit was not yet followed by canonical synchronization. This is recorded as a sequencing failure.

## Correction plan

Require exactly one root mount identity; reject scratch major:minor reuse with /, /overlay, /rom and /boot; reject duplicate protected mountpoints; require a separately identified /overlay mount when the root filesystem type is overlay; retain all existing source/path/filesystem/private-marker checks.

## Evidence limits

All regression inputs are synthetic mountinfo text. The shell test creates only a private temporary directory and removes it. It does not mount/unmount, write block devices, interrupt power, operate a coin acceptor, run a payment, migrate data, or authorize installation. Distinct major:minor proves distinct mounted block-device identity only; it does not prove physically separate media or owner-confirmed disposability. CI remains SIMULATED / CI VERIFIED only.

## Next exact action

Implement the parser correction, run the focused exact-source workflow, then update this handover plus CURRENT_STATE.md, CHANGE_LEDGER.md and the top of PROJECT_HANDOVER.md with terminal evidence. Keep PR #356 DRAFT and unmerged.
