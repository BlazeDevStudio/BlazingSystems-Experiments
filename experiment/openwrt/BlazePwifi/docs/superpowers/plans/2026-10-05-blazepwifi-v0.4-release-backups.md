# BlazePwifi v0.4.0 Release and Backup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate configured backups only from passed simulation environments, assemble installation-ready v0.4.0 assets, audit them, and publish the production GitHub Release.

**Architecture:** Backup generation is downstream of simulation and uses the exact validated candidate artifacts. The repository stores lightweight indexes/checksums; large images live in GitHub Release assets.

**Tech Stack:** GitHub Actions/Releases, gzip/tar/sha256, OpenWrt config backup, QEMU/emulator outputs.

**Spec:** `experiment/openwrt/BlazePwifi/docs/superpowers/specs/2026-10-05-blazepwifi-v0.4-launcher-design.md`

## Global Constraints

- Do not overwrite or delete v0.3.0.
- No placeholder or failed binary may appear in v0.4.0 assets.
- Large backup images live in GitHub Release assets; `releases/0.4.0/images/` is the persistent index.
- Physical-hardware validation claims remain separate from simulation/build validation.
- Ruijie backup is production sysupgrade plus matching config archive, not a fake mutable-state sysupgrade.

## Review Focus

- Backup came from a different binary than the published base image: manifest must link source SHA256 to backup SHA256.
- Configured image became truncated/corrupt after mutation: decompress/mount or boot check must pass again.
- Release manifest omits an uploaded asset or lists a missing asset: publication gate compares both directions.
- APK certificate/fingerprint does not match published APK: release fails.
- Optional board failed simulation but artifact is accidentally uploaded: per-target status blocks it.

---

### Task 1: Generate configured backups from passed simulations

**Files:**
- Create: `releases/0.4.0/images/README.md`.
- Create: `releases/0.4.0/images/manifest.json`.
- CI produces large binary backup assets.

**Interfaces:**
- Consumes green simulation artifacts/logs from the build/simulation plan.
- Produces x86 BIOS/UEFI configured `.img.gz`, configured `.img.gz` for each published Orange Pi image, Android emulator userdata backup for reproducibility, exact validated ESP factory/merged binaries, and Ruijie sysupgrade + config backup archive.

- [ ] **Step 1: Write failing backup-manifest test.**
  Require source SHA, backup SHA, simulation run ID, validation level and target name.

- [ ] **Step 2: Generate backups only from green simulation jobs.**

- [ ] **Step 3: Revalidate backup decompression/mount/QEMU boot where applicable.**

- [ ] **Step 4: Run manifest test.**
  Expected: PASS.

- [ ] **Step 5: Commit lightweight image index.**
  `release(blazepwifi): index v0.4 validated backups`

---

### Task 2: Assemble production release assets

**Files:**
- Modify production release workflow for `v0.4.0`.
- Create/update: `releases/0.4.0/RELEASE_NOTES.md`, `ASSETS.md`, `manifest.json`, `SHA256SUMS`.
- Test: `tests/v04_release_manifest.sh`.

**Interfaces:**
- Consumes signed APK, hardware artifacts and validated backups.
- Produces the exact GitHub Release upload set.

- [ ] **Step 1: Write failing release-manifest test.**
  Mandatory assets: signed APK, QR setup HTML, ESP8266 BIN+INO, ESP32 BIN+INO/merged image, Ruijie sysupgrade/config backup, x86 BIOS+UEFI images, Zero3/One/PC images, checksums, manifests and simulation report.

- [ ] **Step 2: Assemble install-ready assets.**
  Source/docs may be present, but compiled installers/flashables are the primary outputs.

- [ ] **Step 3: Generate SHA256SUMS and manifest from actual bytes.**

- [ ] **Step 4: Compare manifest entries to upload set in both directions.**

- [ ] **Step 5: Run release-manifest test.**
  Expected: PASS.

- [ ] **Step 6: Commit release metadata.**
  `release(blazepwifi): prepare v0.4.0 production assets`

---

### Task 3: Final audit, publication and branch integration

**Files:** no planned runtime files; only review-driven fixes.

**Interfaces:**
- Consumes all prior plans.
- Produces published `v0.4.0` Release and a clean merge candidate.

- [ ] **Step 1: Run the complete validation/build/simulation/backup/release suite on the final candidate commit.**

- [ ] **Step 2: Perform whole-branch code/security review against the approved spec and all Review Focus items.**

- [ ] **Step 3: Fix Critical/Important findings with RED→GREEN tests, then rerun the full required suite.**

- [ ] **Step 4: Verify public tree contains no private signing material, permanent enrollment secret, plaintext phone-admin password, or prohibited proprietary material.**

- [ ] **Step 5: Verify v0.4.0 GitHub Release assets and digests after upload.**

- [ ] **Step 6: Preserve v0.3.0 tag/release unchanged and prepare the v0.4 merge.**

- [ ] **Step 7: Merge/publish only after the user-approved publication side effect is reached.**
