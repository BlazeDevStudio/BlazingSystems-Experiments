# PHX-L-VERIFY UTC03 — HWPRE-0683 exact-source early-denial audit

Date: 2026-10-27 UTC03. NO CODEX. PRODUCTION NO-GO.

## Live CI and integration status

- `main`: `1719b625173ab33cbf90f0729716e43fce8759ed`; development comparison-only `blazepwifi-v0.6.0-audit-foundation@1890e522843d262c33a5109dcea11768896c2e5f`. No MASTER-approved integration base.
- Parent draft #179 `e5a9781ea5234b09501d5356cf966f9237ac8172`; child draft #193 prior literal `91cb42d0a06ec4add159d74cea9aa08ea9b6a146`; #150/#183 open draft unmerged.
- Previous exact Full #40441077954 COMPLETED FAILURE: validate #121981357347; mandatory handover PASS, ESP8266 job #121981357293 and ESP32 #121981357323 SUCCESS, 13/13 target-bound controls per board PASS, 13/15 reconfiguration controls per board with two existing genuine REDs: `untrusted_positive_revision_cannot_enable_coin`, `cold_reboot_older_positive_revision_cannot_enable_coin`. Native #40441078003 COMPLETED SUCCESS.

## Independent executed QA

- Actual `tools/v060_physical_pretrial_readonly.sh` matched Git blob `848c3b930937df3537b36af94629aaed0026e28b` using `git hash-object` and was executed by `/bin/sh` in an isolated Linux host test.
- Eleven invalid controls: regular file, symlink to regular file, directory, FIFO, Unix socket, missing source, `/dev/null` and `/dev/zero` character devices, symlink to character device, too few args, too many args. All 11 returned exit 9 with `HWPRE-0683 BLOCKED`, no success marker, and no call to a deliberately nonfunctional downstream guard sentinel. Disposable fixture SHA256 remained unchanged (12/12 expected assertions PASS).
- Evidence ZIP SHA256 `a54a22173e9f0a8f2f845d87e8f88208e73d0daaddb7c488e870ae48cdc91efe`; test script SHA256 `7c64b8aa76d62d4caf155cb1f074db7c3a9b83e82185070c44284757046d4e3e`, results SHA256 `058bdba273dab89e45e5f51a65ead3b4461cf3a902da52b5c5e27cc30c508fdf`.

## Boundary / next

This is NEGATIVE-ONLY source execution, not a real block-special device or the real downstream storage guard positive path, mountinfo admission, actual coin relay, 150 physical power cuts, 30-device soak, independent witness, financial authority, reversible migration or permanent signing. No hardware, payment, customer data, keys, flashing, merge or release. MASTER/#34 to arrange explicitly authorized isolated test equipment and independent telemetry; MASTER/CORE to resolve authenticated configuration revision and cold-start RED. PRODUCTION NO-GO.
