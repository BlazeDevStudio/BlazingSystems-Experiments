# AGENTS.md — Blaze Systems Experiments

Repository-specific coordination guidance for human and AI development workers.

## Storage and recovery
1. Read the canonical [Blaze Systems Cloud Artifact Policy](https://github.com/BlazingSystems/BlazingSystems/blob/main/BLAZE_CLOUD_ARTIFACT_POLICY.md) and the [verified recovery handover](https://github.com/BlazingSystems/BlazingSystems/blob/main/BLAZE_CLOUD_STORAGE_HANDOVER.md).
2. GitHub remains source control. Large binaries, firmware, ISO/VM files, testing logs, CI artifacts, and source-recovery snapshots are stored in the owner's **restricted** Google Drive mirror under `Experimental Projects/Blaze-Systems-Project-Mirror`.
3. Before new folder/artifact creation, open the *private* `BLAZE_PROJECT_REGISTRY.json`, `BLAZE_ARTIFACT_MANIFEST.json`, and `BLAZE_SYNC_LEDGER.json`; deduplicate by exact SHA256 and preserve existing versions. Do not put private Drive file/folder IDs into a public repository.
4. An artifact is only VERIFIED after successful destination readback and SHA256/size comparison. State NOT_RECOVERED or BLOCKED when source or transfer access is missing. A CI archive is **not** a Git-history backup.
5. Never expose credentials, certificates with private keys, customer data, proprietary forms, raw router configs, or unlicensed third-party assets.

## Production safety boundary
- Phoenix LIGHT / BlazePwifi financial admission and hardware release remain **NO-GO** pending independent durable accounting, anti-rollback/registry witness, QA review, and physical acceptance. Neither CI pass nor mirroring changes these gates.
- Keep draft safety PRs draft. Do not merge, flash devices, deploy production, or duplicate control-plane comments under an archival directive.
- Treat different project branches as different source refs; do not assume `main` is the current Phoenix implementation. Confirm exact PR/branch heads before touching code.

## Coordination
External ChatGPT workers are isolated. A repository document is discoverable guidance, **not proof of worker notification**. Record actual coordination only when an authenticated user or worker acknowledges it. Keep every read/write scope limited to the task.

**This file adds storage-process instructions only; it does not change code, release approvals, source ownership, or user permissions.**
