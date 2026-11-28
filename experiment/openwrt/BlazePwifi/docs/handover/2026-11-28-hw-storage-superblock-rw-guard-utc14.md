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
