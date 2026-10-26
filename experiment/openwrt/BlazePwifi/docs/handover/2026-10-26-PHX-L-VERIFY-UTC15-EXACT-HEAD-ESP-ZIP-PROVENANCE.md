# PHX-L-VERIFY UTC15 — exact-head ESP firmware ZIP byte and PR-merge provenance (NO CODEX)

**Audit executed 2026-10-26 UTC14–15; documentation checkpoint UTC15.** Owner PHX-L-VERIFY. **Scope:** independent read-only firmware/build-release QA on draft PR #193, stacked on unmerged #179. **Production NO-GO.** No firmware edits, flash, customer money/device, signing, integration or release.

## Exact authority / CI

- Repository `BlazingSystems/BlazingSystems-Experiments`; current default `main@1719b625173ab33cbf90f0729716e43fce8759ed`; development comparison-only `blazepwifi-v0.6.0-audit-foundation@5a8fe3efbc4afb9ecf1260c4f09cf6903c26795a` (**not an authorized Phoenix integration base**).
- Pre-report draft #193 literal HEAD `f3e7349b714433ec9c33cbae3d795b9f163cfc9f`, base draft #179 `e5a9781ea5234b09501d5356cf966f9237ac8172`, GitHub PR synthetic merge `ec3f2da3327c14a221d6673a19596f404b9215a1`. Draft #150/#183 remain separate and unmerged.
- [Full #40319558582](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40319558582) **COMPLETED FAILURE**, validate job `121561908988` 15 GPIO cases per board with two genuine REDs per board: `untrusted_positive_revision_cannot_enable_coin` and `cold_reboot_older_positive_revision_cannot_enable_coin`. Both ESP Arduino compile jobs and mandatory handover PASS; production signing/publishing SKIPPED. [Native #40319557932](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40319557932) **COMPLETED SUCCESS**. Native success and artifact integrity DO NOT override Full failure.
- Both actual ESP build-job logs (`121561908809`, `121561908759`) checked out `refs/remotes/pull/193/merge` at `ec3f2da`; source HEAD, synthetic merge and job checkout are distinguished. GitHub exact Git blobs matched HEAD and merge for **6/6** inspected files: both ESP sketches, shared pending header, target-bound and GPIO regression tests, and Full workflow. Sketch blobs `a64dd08ecb4eaa71da3b29b43d86ffa8a58df5b5` / `7b2d3a9c9c0ea076992265bdf1113a6db75a350f`; pending header `aad7c52e9376e4ca2995e9d9b9cc8d5ed71c76d4`.

## Independent actual ZIP-byte execution (NOT metadata-only)

Downloaded actual Actions artifacts and ran read-only Python stdlib audit against ZIP bytes (not just published digests):

| Check | ESP8266 | ESP32 |
| --- | --- | --- |
| Artifact ID | `12648253172` | `12649145404` |
| ZIP bytes | 2,194,583 | 14,839,779 |
| Independent ZIP SHA256 | `a8616ad44d230247e6d75d9a16c39987307eb7982bddcc2fa4446e5e95928885` | `edf83863f58a88769171930148cab99f24a3978750ef9eb12e894f5517e2911d` |
| Matches GitHub metadata and job upload log | YES | YES |
| Internal manifest verified | **9/9** | **23/23** |
| ZIP CRC/member safety | PASS | PASS |
| Packaged sketch Git blob equals exact HEAD/merge | PASS | PASS |
| Shared pending header Git blob equals exact HEAD/merge | PASS | PASS |
| ELF / image magic | PASS | PASS |

ESP32's six duplicated build outputs were byte-identical. Validator positive **2/2 real ZIPs PASS**; **14/14** negative fixtures rejected (synthetic malformed manifests/path/source/magic and one-byte actual archive tamper per board). Python syntax compilation PASS; evidence ZIP CRC PASS. **Reproducible conversation-local test-only package:** `phx_verify_utc14_artifact_provenance.zip`, SHA256 `57008eb1d83619a6b2477cfdef8f12aa5901cb821fef285e9527035d05b35b44`; includes `audit_esp_artifacts.py`, `results.json`, `github_crosswalk.json`, `README.md`. Firmware ZIP bytes were downloaded into a disposable QA workspace but are NOT included in the small evidence package and NOT uploaded to this PR.

## Decision / limits / next

This is **artifact byte-integrity, Git source identity and CI checkout provenance**, not deterministic rebuild proof, authenticated signing, safe firmware, source correction, deployed relay proof, paid ACK or electrical durability. **Full CI is RED.** The old source-level GPIO/polarity controls remain distinct from unverified electrical acceptance. MASTER/CORE must approve authenticated configuration revision, independent cold-start freshness and signed terminal ACK contracts before a guarded source fix; no merge until reviewed and exact-head CI accepted. Continue independent off-device test planning only.

Hard gates remain OPEN: #31/#32 paid finance, #43 independent monotonic witness, #34 150 actual isolated power cuts + 30-device/24-hour soak, reversible migration, permanent signing, electrical coin acceptor/relay/pulse and physical flash acceptance. **PRODUCTION_v0.6.0_RELEASED=0; no Codex, customer devices, financial records, keys, flashing or commercial release.**
