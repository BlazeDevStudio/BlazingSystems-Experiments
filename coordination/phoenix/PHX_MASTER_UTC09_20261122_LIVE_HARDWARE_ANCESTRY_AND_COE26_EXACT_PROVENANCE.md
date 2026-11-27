# PHX-MASTER UTC09 — live Hardware ancestry, role CI and COE #26 exact provenance

**Checkpoint:** 2026-11-22T09:40Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Scope:** coordination/phoenix only; architecture and integration provenance; no subsystem implementation.  
**Execution:** Strict NO CODEX. No Codex app, CLI, API, agent, workflow or delegation.  
**Disposition:** Audit evidence committed to the existing draft PR #288; production remains NO-GO.

## 1. Live repository references

- Experiments default branch: main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Literal branch named development: blazepwifi-v0.5.3-development at aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Separate v0.6 audit-foundation ref: 2fbd2475e9f54878c316fa7cea2f228386b0e859; it is not the literal development branch.
- PHX-MASTER branch before this update: 737af73dbc4d3ab3786b6f6b0b251106a5d1c7c3.
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243.
- COE integration PR #26: b382d233ff06c8791b1028bed3c617cc7b670d12, OPEN / DRAFT / FROZEN, five queued workflows and zero jobs.
- Existing Master PR #288: OPEN / DRAFT / UNMERGED, base main; 164 pre-update paths, all under coordination/phoenix/.
- OWNERSHIP_ROUTES.json: blob e4db324315a1b3543fec17a148fbf960170fcb29; 11 routes, DRAFT_REVIEW_ONLY, PHX-MASTER target null.
- Cleanup issue #266 remains OPEN, 0/7 tracks complete.

Repository guidance read: Experiments root AGENTS.md blob d8777e3b58efc41caa5aa3c969c932aee9103d5f and README.md blob feb909e3f74ffb7b5b22df50399ccd127ada3b95. The canonical cloud artifact policy and storage recovery handover were read from BlazeDevStudio/BlazingSystems main (policy blob 5e503925750c4e511314e4b7624579d82f60aae2; handover blob a15f14cb3baf46424b820e1a921462794422f06b). The private registry and sync ledger are prerequisites for Drive mirror creation; no such creation was attempted.

## 2. Owner PRs and exact-head CI

| Role / PR | Exact head | Current evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | [Build #42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS (scoped). CORE remains separately owned. |
| RENTAL #328 | 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | [APK identity #44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) and [API21/API23 #44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS. [Full #44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAILS mandatory handover freshness and ESP32 compile because mbedtls/sha256.h is missing. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | [Windows synthetic #42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM/device acceptance NOT TESTED. |
| HARDWARE #327 | final 21315a8ad024b1e5341bf3e2b3998c67d23d5f34; source/test 4019851a62262c43bc8d958124ee3803fd61eac4; base #326 58c558fb6a237935214621adc3dee65a10fe1a51 | [Quarantine #45007220029](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45007220029) and [Relay #45007220186](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45007220186) PASS. [Full #45007220017](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45007220017) FAILS Controller protocol parity at the inherited Missing poll signature check. |
| HARDWARE #339 | final b3e1558845ae2cd508e42d0d4722fdcd28293e32; source/test f3dca92cd1f27bb3b1c717d1589fcb46baf5ccba; base #338 1a6a7cacf95722a78330d70de057e858143520f2 | [Quarantine #44986635350](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44986635350) PASS. [Full #44986635417](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44986635417) FAILS at the same poll-signature gate. |
| HARDWARE #340 | final 20c5889fc4ceeb95ab0b05c7c11952704caff36b; source/test 4eefce64719f40fd30621296db7c3fa764a44f1a; separate child of #283 88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d | [Poll preflight #44983396365](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44983396365), [Quarantine #44983396263](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44983396263), [Mbed TLS #44983396273](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44983396273), [ESP8266 #44983396281](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44983396281), [ESP32 #44983396267](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44983396267), and [Full #44983396262](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44983396262) PASS. Signing/publication skipped; physical acceptance NOT TESTED. |
| QA #290 / #292 | 5c29d15994cee1279058f1eca12f2a3180704292 / 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | [#290 Windows #43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS. #292 has zero PR-triggered runs and a stale Master base. |
| RELEASE #291 | 42797e2f3d65c30a1070caf49c93aebec149d897 | [ESP32 compatibility #44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) PASS. [Full #44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) and [Windows #44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) FAIL at mandatory handover freshness; publishers skipped. |
| COE RELEASE #35 | 49f7489781e7b6a7d5eb13aa054f6214ba7db1b8 | [Case guard #45007482064](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45007482064) PASS. [Shared #45007482052](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45007482052) executed 178 tests and emitted the manifest-durability marker, then all ten appliance profiles failed closed without an approved site ULA /48. [Sandbox #45007482082](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45007482082) passed 33 host tests, then Bubblewrap was absent (exit 125). |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows QUEUED / zero jobs; FROZEN. |

## 3. Hardware ancestry reconciliation

GitHub compare #327...#339 returns DIVERGED: 64 commits ahead, 32 behind, merge base 827fa75fa4e56ff3033076cc2f9b7ebb0cddf1a8. #327 is based on #326; #339 is based on #338. #340 is a separate child of #283.

The exact fixture blob in #327, 894589c45500f76c0728ffa1ce16c12992da4f12, differs from the older #339 blob ab18b709de2fdf7a2acc4432c1b902007e538caf. #339 does not contain the current #327 phase-2/inactive-branch fixture hardening. This is a parent-tree freshness issue, not proof that the #339 normalizer patch itself is defective.

**Master decision:** do not merge, rebase, retarget, cherry-pick or force-push either Hardware branch. HARDWARE must state whether #339 is intentionally independent or should port the exact #327 fixture changes after owner review. QA/CORE must resolve the poll-signature producer/consumer contract; firmware default-deny must not be weakened to satisfy the inherited positive lexical marker.

## 4. Exact COE #26 migration provenance

All recursive trees were complete (truncated=false):

| Exact ref | Tree entries | Blobs | Board-local Python helpers |
|---|---:|---:|---:|
| Experiments main | 2,340 | 1,764 | baseline |
| HARDWARE #327 | 2,475 | 1,896 | 32 |
| HARDWARE #339 | 2,479 | 1,900 | 36 |
| HARDWARE #340 | 2,363 | 1,784 | 7 |
| COE #26 | 286 | 207 | 0 |

Exact firmware sketch blobs:

| Ref | ESP32 | ESP8266 |
|---|---|---|
| Experiments main | 117c6e937e8f12f3890ace2ae23b3a23ff1c3df0 | bfb94920eb0a189ca01d52e5443954fa133f5423 |
| #327 | 7ffb7b534c7163678726902946a17b04992950a0 | c2aa71963eaa0288721f0bb13cff771aaaabc42f |
| #339 | 53b27aa80fa4a91aabac71de57f550a8eef2cb61 | 71160ac8ebd5163b19a56d6c9e229a5429975fc8 |
| #340 | 6a6b1c826872af9f21721fb82cbc5754785c7888 | fdd4e45b2346957ce5f55ae529734854e4c78c7f |
| COE #26 | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 | c8be98f72596681e36a3ad1f8939bf8046c96887 |

Test identities diverge: #327/#339 source test blob 41211b2c110ab409f6d9d1812ef12fda73b13211; #340 source test blob dc20a6ce1a1828c9cba9631fc67193840de5c224; COE Hardware test blob f921c56cecc19cab1989507b9b4ade1f45dac54e. No byte-identical test import is established.

Licensing: source BlazePwifi/LICENSE and COE Pisowifi/LICENSE match at 1ee55b94183417be977ca287cd7391f9a6f7e721. Source root NOTICE.md exists at f6d92cd21465312be5993631fe26977219be0fb9; COE root NOTICE.md is absent; COE Hardware/LICENSE and Hardware/NOTICE.md are absent.

**No migration is authorized or staged.** No copy, move, overwrite, cherry-pick, rebase, destination edit or route promotion occurred. OWNERSHIP_ROUTES.json remains unchanged, 11 routes, DRAFT_REVIEW_ONLY, Master destination null. COE #26 remains frozen.

## 5. Test execution and access limitations

- Remote GitHub tree/blob inspections and CI logs were read at exact SHAs; these are not local repository test execution.
- Master head 737af73 had zero PR-triggered workflow runs and zero combined status checks.
- Full Master Python suite NOT RUN. Local git ls-remote failed with “Could not resolve host: github.com”; no local checkout was available.
- Private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections are not accessible through the exposed connector surface. No Google Drive connector is available. Older registry snapshots were not substituted; no Drive readback or write occurred.
- Cleanup #266 remains OPEN, 0/7. The Master duplicate/dead-code inventory remains incomplete.
- Effective branch protection was not re-verified in this activation.

## 6. Next exact actions

1. HARDWARE owner: decide whether #339 remains independent or needs an owner-reviewed port of the #327 fixture fix; preserve the separate #340 lineage.
2. CORE + QA owners: define the authenticated poll response contract and update the stale positive fixture only after the contract is approved; keep firmware default-deny.
3. RENTAL owner: refresh the exact handover and resolve the ESP32 Mbed TLS header compatibility.
4. RELEASE / infrastructure: provide approved site ULA /48 authority and a trusted Bubblewrap-capable runner.
5. Registry custodian: restore authorized private v11 registry and newer-correction access.
6. Human runner: restore authenticated GitHub network/checkout and execute the full Master coordination unittest suite and verifier.
7. Independent QA / hardware owners: provide native acceptance, 150 real power cuts and 30-device/24-hour soak evidence before any production gate review.

No merge, release, signing, secret provisioning, flash, financial migration, physical test or owner-authorized production approval occurred. **PRODUCTION NO-GO.**
