# Blaze Coin-Operated Ecosystem — large artifact Google Drive handoff policy

**Owner instruction:** 2026-10-24 (Asia/Manila). **State:** instruction recorded; automatic uploader NOT configured or tested by this documentation change.

## Destination and threshold

- **Owner-designated folder:** https://drive.google.com/drive/folders/15jHh7-ZFcsdIkRY3YOk2XxRxzkDEcd-g
- **Folder ID:** `15jHh7-ZFcsdIkRY3YOk2XxRxzkDEcd-g`.
- **Inclusive cutoff:** **200 MB or larger** (`>= 200,000,000` bytes, decimal MB; use actual byte length, not estimated/compressed source size).
- **Applies to:** every new or retained large distributable, firmware/system image, offline installer/ISO, build/archive/package, backup/export and relevant development handoff evidence for the **Blaze coin-operated ecosystem** (Full BlazePwifi, Standalone Rental, BlazeRental, BlazePisonet SoftTimer, ESP8266/ESP32 controllers, OpenWrt, Windows/Android or related supporting hardware build outputs). Include older large artifacts when an authorized, available source can be verified and uploaded.
- **Does not change** other unrelated BlazingSystems projects or license/permitted redistribution conditions.
- Keep normal source code, version history, small metadata, checksums and handover documents in GitHub. Do not commit giant binaries to the Git history or pretend that a GitHub Actions transient artifact is permanent backup.

## Required handoff procedure for each qualifying file

1. Inventory local output directories, build artifacts, release attachments and earlier retained archives. For each candidate, capture the actual filename/path, exact `size_bytes`, version, source commit SHA, build/workflow run ID, artifact ID, and whether it contains signing secrets, customer data or third-party licensed material.
2. If `size_bytes >= 200000000`, upload the **original file bytes** to the owner-designated Google Drive folder, using **authenticated Google Drive API / authorized uploader** with the least privileges necessary. Do not alter or transcode the file just to cross the threshold. Preserve structure with descriptive versioned names; never replace another file silently.
3. Treat any private keys, recovery materials, personally identifiable information, payment records or credentials as sensitive regardless of size. Never place these in a broadly shared/public folder unencrypted. A secure owner-approved encryption/key-management procedure and explicit authorization are prerequisites for any sensitive backup. Exclude prohibited/unlicensed third-party materials.
4. Compute local SHA-256 before upload; after upload, verify the returned Drive file ID, filename, byte size and folder parent; verify SHA-256 of downloaded bytes (or equivalent trustworthy end-to-end full-byte verification). Drive metadata alone does **not** prove file-content identity. If the verification path is unavailable, mark it **UPLOADED_UNVERIFIED**, not complete, and retain the original.
5. Register a link plus `drive_file_id`, byte count, source SHA, SHA-256, version, provenance, verification result/date and upload operator in an append-only artifact manifest/handover entry. For sensitive items, publish only non-sensitive manifest metadata; never log tokens, contents, URLs granting bearer access, or unprotected secrets.
6. **No deletion before success:** do not remove a local/GitHub artifact, existing release attachment, backup or source until the remote copy is verified, retention/reproducibility impact is reviewed and the owner authorizes any deletion. Google Drive is *additional storage*, not sole authoritative backup. Do not retroactively rewrite historical Git tags/releases.
7. On upload/verification failure, missing permission, quota exhaustion, network interruption or duplicate/conflict, stop, preserve the existing bytes, and record a precise `BLOCKED` or `PENDING` state with the next safe action. Never claim upload success based only on a policy change.

## Development and CI integration requirements

- The policy is mandatory for all coin-ecosystem handoffs. On future builds, add an authenticated, checksum-verifying post-build uploader as a **separate gated workflow**, not a bypass of existing CI/release/physical-acceptance gates. GitHub Actions must be used for legitimate build/release distribution, not permanent server hosting.
- GitHub-to-Google-Drive upload requires owner-granted credentials/identity and folder write permission. **No Drive deployment credentials or automatic uploader are installed by this documentation change.** Prefer an appropriately scoped short-lived identity; never commit OAuth refresh tokens or Google service-account private keys.
- Parallel builds should use unique artifact names and preserve provenance; store one manifest record per uploaded object. Automatic pruning, replacing files or making the folder public are NOT authorized.
- For files below 200 MB, existing release/storage conventions remain in force unless the owner separately directs otherwise. The threshold does not override external provider file-size limits.
- Release notes/README/handover must link to the Drive artifact and a checked SHA-256 instead of claiming a GitHub release contains a missing large binary. Document real accessibility: Drive viewer permissions are not assumed public.
- Ensure that older high-priority items (e.g., Full BlazePwifi image archives, Windows installers, Android releases, backups) are inventoried and transferred only when accessible and verified. The upload backlog is **not** complete merely because this policy was recorded.

## Per-file checklist entry template

```text
Artifact: <exact name>
Component/version: <ecosystem component and version>
Source: <repo / branch / commit SHA / workflow run ID / artifact ID>
Size bytes: <integer>  [>= 200000000]
Local SHA-256: <hex>
Drive destination folder: 15jHh7-ZFcsdIkRY3YOk2XxRxzkDEcd-g
Drive file ID and read link: <actual returned values, not guessed>
Remote byte length: <integer>
Remote full-byte SHA-256: <hex or UNVERIFIED>
State: PENDING | BLOCKED | UPLOADED_UNVERIFIED | VERIFIED
Access/security review: <non-sensitive summary>
Original retained: YES
Next action: <one exact action>
```

## Current checkpoint (2026-10-24)

The user-designated folder was **successfully listed** with a connected Google Drive account. It already contains `R281 archive.zip` (297,724,092 bytes, existing Drive file ID `16d0JRHO6Mt2rQc8wnBqRaFwQEwbxJUwX`) plus other preexisting items. **These items were not uploaded, modified, re-hashed, or independently verified by this policy change.**

**NEXT ACTION:** provision a write-authorized uploader for the exact folder, then inventory current ecosystem artifacts >=200,000,000 bytes and upload/verify each, recording its actual Drive link and content digest. Preserve all originals and existing production/security gates.
