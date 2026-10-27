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


## Cross-run byte reproducibility supplement — same UTC15 checkpoint

After the first audit, independently downloaded prior Full #40311571867 artifacts ESP8266 `12641717658` (ZIP SHA256 `c19f743bf2c51a688ef61acb2dbcf833c8f1203ac075a6691525658737b01f30`) and ESP32 `12641767684` (ZIP SHA256 `015842485b41b7324f81478ced2d1cc1a50f0515d7c398de495ff9626f081cca`). Both old and current run build logs show ESP32 Arduino core `3.3.12`, and the GitHub sketch/header blobs are unchanged. Executed `compare_esp_builds.py` on all actual ZIP member bytes:

- **ESP8266:** 10/10 internal members byte-identical across the two runs; outer ZIP SHA differs (archive metadata/packaging bytes).
- **ESP32:** 17/24 internal members byte-identical. The seven changed members are app `.bin`, `.elf`, `.merged.bin`, their three duplicate build-directory copies and `SHA256SUMS`. Actual ELF differs in **4 bytes**; app BIN and merged BIN each differ in **69 bytes**. Image bytes contain different build-time strings `10:03:56` and `12:07:19` on October 26, 2026. Diff positions and both per-member hashes are recorded in `cross_run_results.json`.
- **Interpretation:** This demonstrates **ESP32 output byte drift despite unchanged checked source and reported toolchain version**. The observed timestamps/hash fields are plausible contributors, but no semantic binary-equivalence proof, independent deterministic recompilation or firmware safety acceptance is claimed. No changes were made to firmware or CI to mask the difference.

Updated conversation-local reproducible evidence ZIP SHA256 **`a37762ffc1f8ace2e67c2d315c9e3ce70715154341a8a137fe1413184e804f19`**, containing original ZIP auditor, `compare_esp_builds.py`, both JSON results, GitHub crosswalk and README. This supersedes the earlier smaller evidence ZIP checksum recorded above; neither package is a GitHub firmware artifact.

**Successor exact documentation HEAD `87daf1f8a2b22774c61a2565f7f84ca51ddb1a20`:** [Full #40345296014](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40345296014) **COMPLETED FAILURE**, 15 success / 13 skipped / 1 failed validate `121650613856`, the same two source-linked config-auth/cold-reboot REDs per board; both ESP Arduino jobs and mandatory handover PASS. [Native #40345295558](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40345295558) **COMPLETED SUCCESS**. This same-hour documentation supplement changes no firmware or workflow and requires its own exact-head CI classification. **Production NO-GO.**


## 2026-10-26 UTC15 same-hour supplement — cold-boot GPIO admission (source-transcribed C++ host only)

At literal draft PR #193 HEAD `5c8a76566ad5861f689e07b34031ff241d7f4183`, source blobs ESP8266 `a64dd08ecb4eaa71da3b29b43d86ffa8a58df5b5` and ESP32 `7b2d3a9c9c0ea076992265bdf1113a6db75a350f` show `setup()` assigns persisted `cfg.coinPin`, `cfg.relayPin`, `cfg.insertLedPin` directly to runtime pins and calls `configureRuntimePins` without rejecting aliases or board-restricted pins. Remote `applyRemoteConfig` guards are not a cold-boot guard. An isolated source-transcribed C++17 host test compiled and ran with fake `pinMode`/`digitalWrite`: 7/7 unsafe saved pin cases issued the three `pinMode` calls (both boards coin=relay, relay=LED and GPIO6 flash-bus relay; ESP32 GPIO34 input-only relay). Valid default mappings passed 2/2. Reproducible ZIP SHA256 `d110a5e16431eed7d079c555ff9ee442ae6c30d333f3057530ec3402281c29db`. These are modeled GPIO calls, **not actual physical relay or power tests**. No source or workflow change; MASTER/CORE must review board-specific boot allowlists, polarity-first deenergization, and persistence-failure acknowledgment before any correction. Exact-head Full #40346138639 COMPLETED FAILURE (validate 121653560305 two config-auth/reboot REDs per board, ESP builds/handover PASS); Native #40346138602 SUCCESS. All P0 gates and production NO-GO remain.


**Prior-art reconciliation (UTC15):** The same ESP8266/ESP32 source blobs and persisted startup GPIO admission defect were already reported in [2026-10-25 UTC10 BLAZE-COMMS #6396809047](https://github.com/BlazingSystems/BlazingSystems-Experiments/issues/172#issuecomment-6396809047), with 12/12 host scenarios (10 invalid vectors), and in `2026-10-25-PHX-L-VERIFY-UTC10-ESP-STARTUP-GPIO-ADMISSION.md`. This supplemental 7-vector/2-control execution is **independent reconfirmation only**, NOT a novel firmware defect or a source fix. MASTER/CORE review was already requested; do not duplicate the existing test-first work. This note corrects any implied novelty in the UTC15 supplement.
