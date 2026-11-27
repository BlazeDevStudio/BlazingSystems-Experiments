# BlazePwifi v0.4.0 Build and Simulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce and execute the v0.4 build matrix for Android, ESP8266/ESP32, Ruijie, x86 BIOS/UEFI and required Orange Pi boards, then run truthful environment simulations against the compiled artifacts.

**Architecture:** Preserve the v0.3 controller/OpenWrt foundation unless v0.4 interfaces require changes. CI builds artifacts once, simulation jobs download those exact artifacts, and backup generation is downstream of passing simulations rather than recompiling different binaries.

**Tech Stack:** GitHub Actions, Arduino CLI, OpenWrt ImageBuilder, Android Gradle, apksigner, QEMU, Android Emulator, qemu-user, esptool, binwalk.

**Spec:** `experiment/openwrt/BlazePwifi/docs/superpowers/specs/2026-10-05-blazepwifi-v0.4-launcher-design.md`

## Global Constraints

- Required targets: Ruijie RG-EW1200G Pro v1.1, x86_64 BIOS, x86_64 UEFI, Orange Pi Zero 3, Orange Pi One, Orange Pi PC, ESP8266, ESP32 and signed BlazeRental APK.
- Optional Orange Pi assets publish only when their own validation passes.
- GitHub-hosted lack of exact board emulation must be labeled honestly.
- Simulation consumes compiled candidate artifacts, not source-only substitutes.
- Existing v0.3 controller behavior remains compatible with v0.4 server.

## Review Focus

- Artifact has wrong board/profile behind a plausible filename: inspect target/profile metadata, not filename alone.
- Android signing identity changes accidentally: release gate rejects wrong certificate fingerprint.
- x86 boots but BlazePwifi service/listeners are dead: QEMU gate checks live ports/pages/API.
- Orange Pi rootfs mounts but target userspace cannot execute: image is not validated.
- ESP binary parses but protocol fields drift from server: protocol tests block publication.

---

### Task 1: Reconcile v0.4 controller protocol compatibility

**Files:**
- Modify ESP8266/ESP32/Linux agent only if v0.4 interfaces require it.
- Test: `tests/controllers.sh`.
- Create: `tests/v04_controller_compat.sh`.

**Interfaces:**
- Consumes existing Vendo API and rental targeting.
- Produces unchanged signed coin-event semantics and server-managed runtime configuration.

- [ ] **Step 1: Write failing compatibility tests.**
  Cover v0.3/v0.4 poll/register envelopes, target-bound coin events, runtime GPIO/polarity/debounce/retry settings.

- [ ] **Step 2: Run controller tests.**
  Expected: only new compatibility cases fail.

- [ ] **Step 3: Implement minimum firmware/agent changes.**

- [ ] **Step 4: Run controller tests.**
  Expected: PASS.

- [ ] **Step 5: Commit.**
  `feat(blazepwifi): preserve v0.4 controller compatibility`

---

### Task 2: Upgrade version metadata and build matrix to v0.4.0

**Files:**
- Modify: `VERSION`, Android version metadata, build scripts and `.github/workflows/blazepwifi-build.yml`.
- Create: `releases/0.4.0/README.md`, `ASSETS.md`, `manifest.json` skeleton.
- Test: `tests/v04_build_matrix.sh`.

**Interfaces:**
- Consumes completed Android and server/admin plans.
- Produces CI artifacts for every required target and successful optional Orange Pi targets.

- [ ] **Step 1: Write failing matrix test.**
  Assert version/tag, required target names, expected artifact patterns and preserved v0.3 release history.

- [ ] **Step 2: Run test.**
  Expected: FAIL.

- [ ] **Step 3: Update v0.4 metadata/build matrix.**

- [ ] **Step 4: Run build-matrix test.**
  Expected: PASS.

- [ ] **Step 5: Commit.**
  `build(blazepwifi): prepare v0.4 target matrix`

---

### Task 3: Establish stable v0.4 Android signing lineage

**Files:**
- Modify production signing workflow/handoff for BlazeRentalLauncher.
- Store only signed APK/public cert/fingerprint under `releases/0.4.0/`.
- Private signing key remains outside public Git.
- Gate verifies APK signature schemes and expected public fingerprint.

**Interfaces:**
- Consumes unsigned v0.4 release APK.
- Produces signed `BlazeRental.apk`, public certificate/fingerprint and recoverable private-key backup outside public Git.

- [ ] **Step 1: Add failing signing gate.**
  Reject unsigned APK and APK signed by a different certificate.

- [ ] **Step 2: Build unsigned release APK.**

- [ ] **Step 3: Sign with the persistent v0.4 production identity and verify v2/v3.**

- [ ] **Step 4: Run signing gate.**
  Expected: PASS.

- [ ] **Step 5: Commit only public APK/certificate metadata where repository policy permits.**

- [ ] **Step 6: Commit.**
  `release(blazerental): establish v0.4 signing lineage`

---

### Task 4: Build required hardware artifacts and verify checksums

**Files:**
- Existing `build/build-openwrt-image.sh`, Android/ESP/OpenWrt workflows and output manifests.

**Interfaces:**
- Produces exact candidate binaries consumed by Task 5.

- [ ] **Step 1: Trigger full candidate build.**
  Required jobs: Android, ESP8266, ESP32, Ruijie, x86_64, Orange Pi Zero 3, Orange Pi One and Orange Pi PC.

- [ ] **Step 2: Require all required jobs green.**

- [ ] **Step 3: Verify every target's SHA256SUMS.**

- [ ] **Step 4: Inspect board/profile identity from build metadata/logs.**

- [ ] **Step 5: Fix target-specific build defects without weakening gates.**

- [ ] **Step 6: Commit any required build fixes.**

---

### Task 5: Run environment simulation against compiled artifacts

**Files:**
- Create/update:
  - `simulation/browser_v04_audit.py`
  - `simulation/android_v04_audit.sh`
  - `simulation/x86_v04_qemu_audit.py`
  - `simulation/orangepi_v04_userspace_audit.sh`
  - `simulation/esp_v04_audit.sh`
  - `simulation/ruijie_v04_audit.sh`
  - matching GitHub Actions workflows.

**Interfaces:**
- Consumes candidate artifacts from Task 4.
- Produces audit JSON, logs, screenshots and pass/fail state consumed by the release/backups plan.

- [ ] **Step 1: Browser simulation.**
  Click required captive/admin controls and fail on console/action errors.

- [ ] **Step 2: Android simulation.**
  Install signed APK in emulator and execute the Android plan's full acceptance set.

- [ ] **Step 3: x86 simulation.**
  Boot BIOS and UEFI images in QEMU; verify BlazePwifi services/pages/API/config persistence.

- [ ] **Step 4: Orange Pi simulation.**
  Inspect partition/rootfs and execute target userspace via qemu-user for every published board image.

- [ ] **Step 5: ESP simulation.**
  Parse binaries with esptool and run controller protocol/state tests. If reliable ESP8266 CPU emulation remains unavailable, record that explicitly rather than fabricating it.

- [ ] **Step 6: Ruijie simulation.**
  Validate target identity, firmware structure and config backup; do not claim physical MT7621 boot.

- [ ] **Step 7: Rerun until all required gates are green.**

- [ ] **Step 8: Commit.**
  `test(blazepwifi): pass v0.4 environment simulation`
