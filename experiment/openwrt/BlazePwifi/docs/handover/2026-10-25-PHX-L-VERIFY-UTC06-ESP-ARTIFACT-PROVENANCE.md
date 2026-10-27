# PHX-L-VERIFY UTC06 — ESP firmware artifact ZIP provenance (read-only QA)

**2026-10-25T06Z · Development evidence only · NO CODEX · NO PRODUCTION**

- Repository: `BlazingSystems/BlazingSystems-Experiments`; draft stacked PR #193 literal source/docs HEAD `5695b458a0ed77a3e65838b31abb29296ef0cc81` onto draft PR #179 `e5a9781ea5234b09501d5356cf966f9237ac8172`. No firmware merge or deploy.
- Artifact-producing workflow: [Full #40167832536](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40167832536), **COMPLETED FAILURE** (15 jobs SUCCESS, validation FAILURE, 13 skipped). The `esp8266` and `esp32` compiler jobs themselves were SUCCESS; validation job `121092428098` executed source-linked tests with **13 PASS + 2 actual security RED per board**. [Native #40167832547](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40167832547) SUCCESS does not clear the firmware RED.
- Downloaded the actual GitHub Actions ZIP bytes through connected GitHub artifact API and independently read them with Python stdlib `zipfile`, `hashlib` and `re`. **62/62 assertions PASS**, 0 mismatch. ZIP metadata digest+byte length, ZIP CRC, path uniqueness/traversal, every non-manifest entry against `SHA256SUMS`, root/bundled sketch equality, shared header and literal PR #193 Git blob equality, ESP32 duplicated build outputs, and three read-only tamper scenarios per board were checked.

| Evidence | ESP8266 | ESP32 |
|---|---|---|
| GitHub Actions artifact ID | `12588897935` | `12589245202` |
| ZIP bytes | `2194583` | `14839801` |
| ZIP SHA-256 | `15d9c2c8a061c31f94b1febd6796e3cb6bfa620314d76e465e5480c78db71a77` | `566737a356d410804b5177e7d93b3cd14176d5ff5a9dc1d44da7ce0767601689` |
| ZIP entries / manifest entries | `10 / 9` | `24 / 23` |
| Audit assertions | `21/21 PASS` | `41/41 PASS` |
| Source Git blob, matches PR #193 | `a64dd08ecb4eaa71da3b29b43d86ffa8a58df5b5` | `7b2d3a9c9c0ea076992265bdf1113a6db75a350f` |
| Shared pending header blob, matches PR #193 | `aad7c52e9376e4ca2995e9d9b9cc8d5ed71c76d4` | `aad7c52e9376e4ca2995e9d9b9cc8d5ed71c76d4` |
| Tamper fixtures | changed sketch, changed manifest digest, unlisted file: `3/3 detected` | same `3/3 detected` |

**Reproduction**: Download the two artifact ZIPs from the named Full run (IDs above). Verify `sha256sum` and byte lengths against the table; for each ZIP check `zipfile.testzip()`, parse `SHA256SUMS` and independently SHA-256 every entry, enforce exact set equality between non-manifest entries and manifest paths, and compute Git blob SHA-1 as `sha1(b"blob " + len(data) + b"\\0" + data)` for the source sketch and shared header. Simulate the three negative cases only in memory. Local executed audit script SHA-256 `0f04f1d17d800ee56e16c890e5447d44893228d6ce05386860a8d3ff26f8ea04`; JSON evidence SHA-256 `0f0c684abda352710c66c1dc63932e011bfe63668a661818845692dfa7b00c7c`. Local script/JSON are conversation artifacts, not claimed to be committed in GitHub.

**Scope limits:** `SHA256SUMS` is self-asserted inside the archive, not a cryptographic release signature; GitHub metadata matching bytes is not an independent trusted build attestation. The bundled `source/README.md` says Arduino core installation tracks upstream release rather than a pinned core version, so bit-for-bit reproducible builds have **not** been established. No source modification, hardware flashing, electrical relay/pulse test, 150 physical cuts, 30-device 24h soak, independent protected monotonic witness #43, reversible migration, paid ACK authority #31/#32, permanent signing or commercial release. **ARTIFACT_INTEGRITY_PASS / CONFIG_AUTH_REBOOT_SOURCE_RED / PRODUCTION_NO_GO**. MASTER controls guarded integration.
