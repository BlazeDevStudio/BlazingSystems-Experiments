# EasyMode 5.0.0-alpha.1 test report

## Current source regression checks (2026-10-25)

The development fixtures are `tests/static-test.sh`, `tests/detector-run.sh`,
`tests/ubus-url.sh` and `tests/ubus-rpc.cjs`. The dedicated
`easymode-static.yml` workflow runs them on Ubuntu at the exact PR/source head.
Its detector check uses only `--check-detector`; it does not install EasyMode.
The page fixture executes the shipped inline script with a fake DOM/transport:
nine URL forms, blank refusal, HTTP failure and rejected login (12 cases),
including both actual JSON-RPC request URLs and unchanged login/board bodies.
It reproduced `/ubus/ubus` on the old page before the endpoint fix.

Local Windows/Git-shell checks passed syntax/manifests, endpoint helper cases,
all 12 page cases, read-only detector entrypoints and PowerShell parsing.
The local mode-644 fixture could not run because this Git shell lacks `chmod`;
the dedicated Linux CI supplies that POSIX permission proof. Exact source
`eb91170e79a21b05f6750d49cefffc65f8311e08` passed push run
[40112898303](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40112898303)
and PR run [40112909733](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40112909733).
Their static, detector mode-644, helper and 12 actual-page cases passed.
These checks do not establish hardware or live-network acceptance.

## Reconciliation
- Canonical real-hardware baseline: EasyMode 4.1.4.
- No newer numbered EasyMode source existed in the connected GitHub repository before this import.
- Existing 4.1.4 R281 compatibility rules remain constraints.

## Passed
- Shell syntax for core/install scripts.
- JSON parsing for all six edition manifests.
- Browser JavaScript syntax for Offline HTML installer.
- Release archive/checksum generation.
- Secret-pattern audit of generated material.

## Hardware verification still required
- Live `ubus`/rpcd registration.
- R281 Wi-Fi scan.
- PXA1826 AT/SMS/USSD/band operations.
- WAN failover/balance and watchdog recovery.
- Real DSA/swconfig mutation tests.
- Browser bootstrap upload/install endpoint (the alpha performs connection testing and provides package fallback).

Status: **Static Tested / Hardware Verification Required**.
