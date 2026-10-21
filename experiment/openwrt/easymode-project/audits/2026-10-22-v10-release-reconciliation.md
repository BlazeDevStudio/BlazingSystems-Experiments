# EasyMode V10 continuation — repository reconciliation and release integrity

Date: 2026-10-22

## Actual source of truth

- Repository: `BlazingSystems/BlazingSystems-Experiments`
- Source branch: `easymode-v7-production`
- R281 management lineage: `releases/v4.2.6-r281-consolidated/` → `releases/v10.0.0-r281/`
- Separate cross-device Traffic Intelligence component: `traffic/` version 7.0.0, six edition packages.
- The `main` branch still contains an obsolete `5.0.0-alpha.1` scaffold. Its version number is not evidence that it supersedes the deployed R281 V10 management application.

## Evidence

The V10 audit and handoff document a live installation on Notion R281 / OpenWrt 24.10.8 on 2026-10-19. The application version, UI/asset responses, services and cellular read-only connectivity were verified at that time. Earlier historical source 4.2.6 remains available.

V10 is an application update, not router firmware. It does not survive factory reset and its board-gated installer must not be run on generic OpenWrt systems. The six generic edition packages offer the Traffic Intelligence module, not full parity with the R281 management UI.

## Defect fixed on this branch

The V10 build generator previously removed the entire published `v10.0.0-r281` directory before copying and rebranding older 4.2.6 source. Rerunning it could erase or replace already-published V10 source and artifacts, including later changes.

- The historical build script now refuses to overwrite an existing V10 release. A subsequent functional release needs a new version and output directory, with a deliberate migration from current V10 source.
- The CI workflow now verifies the committed V10 source and archive without regenerating or deleting V10.
- `traffic/tools/verify-r281-v10.py` checks target board/release, source manifest, source payload file sizes/hashes, archive sidecar, embedded payload contents and modes, embedded checksums, and duplicate/unsafe member names.
- Synthetic regression cases cover a valid fixture, payload tampering, and committed source/manifest drift.

## Verification boundaries

- Local synthetic test fixtures: 3 passed (clean, tampered archive rejected, source drift rejected).
- Actual committed V10 archive check: requires CI execution against the checked-out repository (not yet claimed as passed here).
- No router login, network changes, device flash, hardware reset, or production deployment was performed in this pass.
- Full release acceptance still requires a complete installed-file readback/hash comparison, long-term stability, physical restart/reset validation, and non-R281 feature parity assessments.

## Next release policy

Never overwrite the published V10 archive. Make new feature changes from the **V10 source**, cut a new semantically versioned directory, rebuild, run read-only integrity/security gates, then validate on an approved R281 before production promotion.
