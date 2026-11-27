# BlazePwifi v0.4.0 Server and Admin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend BlazePwifi with a revisioned Lite-safe rental policy, QR Add Device workflow, bidirectional on-device/server policy edits, and a TailAdmin-derived rental management interface.

**Architecture:** Keep money/time state in the existing atomic shell/UCI design. Add a compact v2 policy record with compare-and-set revisions and generate signed structured JSON at the API boundary, avoiding a database or jq dependency on constrained routers.

**Tech Stack:** POSIX shell, UCI, uHTTPd CGI, HMAC-SHA256/OpenSSL, static HTML/JS/CSS, locally bundled TailAdmin-derived assets and QR generator.

**Spec:** `experiment/openwrt/BlazePwifi/docs/superpowers/specs/2026-10-05-blazepwifi-v0.4-launcher-design.md`

## Global Constraints

- EW1200G Pro remains a Lite target; no mandatory database, Node runtime or heavy JS framework.
- Preserve v0.3 device ID, secret, lease, Vendo and admin verifier records.
- One-time QR enrollment credentials expire and are consumed once.
- Server is source of truth for policy revisions.
- Admin state changes require authenticated role + CSRF.
- Phone admin password never appears in logs or QR.
- Standard/Full web UI runs from local assets with no mandatory CDN.

## Review Focus

- Two admins edit the same phone revision concurrently: stale writer is rejected and latest policy survives.
- Existing v0.3 policy row is upgraded: device/lease/password/Vendo survive without reset.
- Enrollment QR is replayed or expired: no partial device record or reusable secret remains.
- Inventory contains unexpected package names/large payloads: validation rejects unsafe input without corrupting state.
- Lite storage write fails during lease/policy update: operation fails closed and prior state remains readable.

---

### Task 1: Add v0.4 policy-v2 storage and migration

**Files:**
- Modify: `openwrt/rootfs/usr/lib/blazepwifi/rental.sh`.
- Create: `openwrt/rootfs/usr/lib/blazepwifi/rental_policy.sh`.
- Modify first-boot/migration script if required.
- Test: `tests/v04_rental_policy.sh`.

**Interfaces:**
- Produces `bp_rental_policy_v2_get DID`.
- Produces `bp_rental_policy_v2_patch DID EXPECTED_REV ...`.
- Produces `bp_rental_policy_v2_json DID`.
- Produces `bp_rental_policy_migrate DID`.
- Record fields: device id, revision, updated-at, updated-by, launcher mode, allowed packages, hidden packages, preferred Vendo, timer mode, timer user-toggle, quick-control allowlist, notifications enabled, admin gesture type/value, admin verifier metadata, offline grace and capability flags.

- [ ] **Step 1: Write migration/CAS failing tests.**
  Include v0.3 record preservation, revision-1 migration, stale expected revision rejection and atomic-write failure preservation.

- [ ] **Step 2: Run `sh tests/v04_rental_policy.sh`.**
  Expected: FAIL.

- [ ] **Step 3: Implement compact v2 policy storage and migration.**
  No jq/database dependency; reject tabs/newlines/oversized list fields before write.

- [ ] **Step 4: Run tests.**
  Expected: PASS.

- [ ] **Step 5: Commit.**
  `feat(blazepwifi): add revisioned rental policy v2`

---

### Task 2: Extend authenticated rental device API

**Files:**
- Modify: `www/blazepwifi/cgi-bin/rental`.
- Modify shared helpers only where necessary.
- Test: `tests/v04_rental_api.sh`.

**Interfaces:**
- Produces actions: existing `enroll`, `status`, `coin_start`, plus `policy_get`, `policy_patch`, `inventory_update`, `device_capabilities`.
- `policy_patch` requires `expected_revision`; success returns canonical signed policy.
- Stale revision returns current revision/policy and does not write.
- `status` remains backward-compatible with v0.3 client fields.

- [ ] **Step 1: Write failing API tests.**
  Verify HMAC/signature canonicalization, nonce requirements on state changes, stale revision conflict, malformed inventory rejection, expired lease reporting and v0.3 compatibility fields.

- [ ] **Step 2: Run API tests.**
  Expected: FAIL.

- [ ] **Step 3: Implement v0.4 device actions and canonical signature format.**
  Preserve enrollment and lease semantics.

- [ ] **Step 4: Run tests.**
  Expected: PASS.

- [ ] **Step 5: Commit.**
  `feat(blazepwifi): add rental policy sync API`

---

### Task 3: Add admin rental-device CRUD and QR enrollment API

**Files:**
- Modify: `www/blazepwifi/cgi-bin/admin`.
- Modify: `usr/lib/blazepwifi/rental.sh` for device/event helpers.
- Reuse bundled QR generator and provisioning helper.
- Test: `tests/v04_rental_admin.sh`.

**Interfaces:**
- Produces admin actions: `rental_device_add`, `rental_device_qr`, `rental_device_get`, `rental_device_list`, `rental_policy_set`, `rental_lease_add`, `rental_lease_expire`, `rental_device_rename`, `rental_device_revoke`, `rental_admin_password_set`, `rental_events`.
- QR response exposes only short-lived enrollment material and provisioning metadata.

- [ ] **Step 1: Write failing role/CSRF/QR tests.**
  Operator/Admin permissions, viewer denial, QR TTL, replay rejection, no permanent secret/password leakage.

- [ ] **Step 2: Run tests.**
  Expected: FAIL.

- [ ] **Step 3: Implement admin actions and event audit.**
  Reuse atomic state helpers and role framework.

- [ ] **Step 4: Run tests.**
  Expected: PASS.

- [ ] **Step 5: Commit.**
  `feat(blazepwifi): add rental device and QR administration API`

---

### Task 4: Build the TailAdmin-derived Rental Devices interface

**Files:**
- Create local vendor attribution/assets under `ui/vendor/tailadmin/`.
- Modify/replace Standard/Full `www/blazepwifi/admin.html` shell.
- Create focused modules under `www/blazepwifi/admin/`: `core.js`, `rental.js`, `controllers.js`.
- Create Lite-compatible staged assets selected by build target.
- Modify build staging scripts.
- Test: `tests/v04_admin_ui.sh`.

**Interfaces:**
- Consumes Task 3 admin actions.
- Produces Add Device QR modal, device list/cards, app inventory toggles, allow/hide controls, lease operations, mode/timer/notification/quick-control policy, password reset, rename/revoke, revision and controller views.

- [ ] **Step 1: Write failing static UI tests.**
  Assert local assets, TailAdmin license attribution, no mandatory CDN, all required rental controls/actions, and Lite asset-budget/staging rules.

- [ ] **Step 2: Run UI test.**
  Expected: FAIL.

- [ ] **Step 3: Vendor a trimmed static TailAdmin visual system.**
  Keep only CSS/icons/components actually used; no Next.js runtime.

- [ ] **Step 4: Implement Rental Devices UI and QR modal.**
  Render friendly app name/icon when inventory provides it; package ID remains secondary technical data.

- [ ] **Step 5: Implement Lite staging.**
  Remove/hide heavy charts/components instead of exposing broken controls.

- [ ] **Step 6: Run static tests.**
  Expected: PASS.

- [ ] **Step 7: Commit.**
  `feat(blazepwifi): add TailAdmin rental management UI`

---

### Task 5: Browser/security integration gate

**Files:**
- Create/update: `simulation/browser_v04_audit.py`.
- Modify `tests/security.sh` and/or create `tests/v04_security.sh`.
- Workflow consumed by the build/simulation plan.

**Interfaces:**
- Consumes Tasks 1-4.
- Produces deterministic click-through/security evidence for rental/admin/portal flows.

- [ ] **Step 1: Add failing browser/security scenarios.**
  Login/logout, Add Device QR, app allow/hide, stale revision display/retry, add/expire lease, password reset, revoke, controller policy, captive Insert Coin/Done/Buy Time/voucher/pause/resume/end, malicious input escaping.

- [ ] **Step 2: Run test workflow.**
  Expected: missing/incorrect behavior fails.

- [ ] **Step 3: Fix server/UI defects with a reproducing test first.**

- [ ] **Step 4: Run complete server/admin/browser suite.**
  Expected: PASS.

- [ ] **Step 5: Commit.**
  `test(blazepwifi): pass v0.4 admin and browser gate`
