# EasyMode 5.0.0-alpha.1 test report

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
