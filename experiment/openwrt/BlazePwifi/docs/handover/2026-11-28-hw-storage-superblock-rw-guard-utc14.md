## PHX-HARDWARE UTC14 — STORCHK-0674 mutation harness correction

**Updated:** 2026-11-28T14:58:00Z  
**DRAFT PR:** [#376](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/376)  
**Branch:** `phoenix/hw-storage-superblock-rw-guard-20261128-utc14`  
**Previous head:** `af17462bf79859439a7a852e6c2ccbf3d39f23b6`

The second exact-head focused run [#46157057143](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46157057143), job `141015924749`, also failed in the test harness: the remaining escaped-slash expression was interpreted by `sed` as a label (`sed: can't find label for jump`). The existing mountinfo and physical-parent matrix passed before this step. This is a test harness syntax issue, not a parser false-acceptance result.

Correction: remove the fragile path-addressed `sed` mutations and use a small AWK helper that locates the exact mountpoint, changes only the post-separator superblock-options field, and exits nonzero unless exactly one row was changed. The `rwx`, `notrw`, and missing-`rw` token cases remain. The parser logic is unchanged.

Full run [#46157057189](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46157057189) was in progress at the time of this update; no terminal result is claimed. This source-test correction is co-committed with the canonical handover/current-state/ledger refresh so the next Full run evaluates a synchronized exact head.

All evidence remains SIMULATED / CI only. No mount, write, power cut, flash, reset, payment, migration, merge, release or deployment occurred. Production NO-GO.

---
## PHX-HARDWARE UTC14 — STORCHK-0674 test-harness correction

**Updated:** 2026-11-28T14:56:00Z  
**DRAFT PR:** [#376](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/376)  
**Branch:** `phoenix/hw-storage-superblock-rw-guard-20261128-utc14`  
**Previous head:** `6793c9e749081f5494f744896976aa1c495a4681`

The first docs-synced exact-head focused run [#46156833024](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46156833024), job `141015236831`, failed in the new synthetic harness because three newly added `sed` address expressions were over-escaped (`sed: can't find label for jump`). This was a test-harness syntax defect, not a parser acceptance failure. The existing mountinfo/physical-parent suite passed before the new harness step. The earlier focused run [#46156397146](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46156397146), job `141013890732`, passed the original read-only-superblock regression on exact checkout `13f8732d93b7a5897dcd23dceccb0853b14b40ee`.

Correction: normalize the three test-only path expressions to the same single-backslash POSIX BRE form already used by the passing cases. The added `rwx`, `notrw`, and missing-`rw` mutations remain in place. The parser logic is unchanged by this correction.

Full run [#46156833042](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46156833042) was still in progress at the time of this update; no terminal result is claimed. This commit co-updates the source test and canonical root handovers/ledger so the next exact-head Full validation does not fail merely because those records lagged the source change.

All evidence remains SIMULATED / CI only. No mount, write, power cut, flash, reset, payment, migration, merge, release or deployment occurred. Production NO-GO.

---
# PHX-HARDWARE UTC14 — STORCHK-0674 superblock read-only guard

**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** child of [#356](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/356), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-storage-superblock-rw-guard-20261128-utc14`  
**Base:** `phoenix/hardware-storage-preflight-device-separation-20261126-utc23@0ea32d31ed5c902b2187d98c181aab14bc9fdeae`  
**Status at authoring:** source change committed; hosted CI pending. No physical operation authorized.

## Proven gap

The read-only mountinfo parser checked the per-mount option field (`$6`) for `rw`, but ignored the superblock-options field after the `- FSTYPE SOURCE` separator. A synthetic, structurally valid mountinfo fixture with both bind-mount option fields set to `rw` and the underlying target or scratch superblock option set to `ro` was accepted by the parent parser.

This is a parser-coverage gap against the documented requirement to establish a writable persistent scratch backing filesystem. It is not evidence that any real device was mounted or that this combination occurred on physical hardware.

## Bounded correction

- Capture the superblock options for both the fixture mount and scratch mount.
- Require `rw` in both per-mount options and both superblock options.
- Emit `superblock_rw_verified=1` only after all existing source, filesystem, mount identity, physical-parent, and read/write checks pass.
- Keep `physical_powercut_verified=0` and `customer_install_authorized=0` unchanged.
- Add a Hardware-owned synthetic regression script under `tools/`; no QA-owned test path, firmware sketch, shared API, or Master coordination file changed.

## Failure-injection evidence

Local host test against the exact parent parser reproduced the expected RED: it accepted a read-only target superblock under `rw` mount flags. The corrected parser then passed the writable positive control and rejected read-only target and scratch superblock mutations, plus the existing per-mount read-only mutations.

**Local classification:** SIMULATED.  
**GitHub Actions:** pending exact PR checkout; no hosted result is claimed in this handover yet.

## Ownership and safety

This extends the existing Hardware-owned read-only STORCHK-0674 tool stack (#356). It does not edit `tests/`, `PROJECT_HANDOVER.md`, `CURRENT_STATE.md`, `CHANGE_LEDGER.md`, the overlapping #374/#375 sketch/workflow paths, or Master/CORE/QA-owned source.

No mount, write, power cut, flash, reset, coin, payment, customer state, signer, witness, migration, merge, release, or deployment occurred. The guard remains a preflight only; human confirmation of actual disposability and separate power-control evidence are still required.

## Next exact action

Obtain exact-head focused CI on the new PR. If it passes, request independent PHX-QA review of the synthetic mountinfo semantics and PHX-MASTER registration of this child stack. Keep #356 and this child DRAFT / unmerged.
