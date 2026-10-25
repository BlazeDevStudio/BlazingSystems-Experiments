## 2026-10-25 — PHX-L-APPS UTC03 test-only source-linked negative committed, CI pending

- Added one native C# fake-OS test on DRAFT PR #197: `exact_open_time_swapped_adapter_must_not_emit_coin_pulse` expects 0 callbacks from substituted COM9 physical adapter, alongside existing `exact_open_time_adapter_swap_must_refuse`. Harness count 28 -> 29. No production source change, no paid credit, no hardware; new exact-head Windows CI conclusion pending. MASTER/VERIFY handle-bound identity review required; WMI recheck is not proof. Prior #40148317381 27/28 intended RED remains historical evidence.

## 2026-10-25 — PHX-L-APPS UTC03 test-only IN PROGRESS

- Planned: add one native fake-OS negative regression requiring zero `CoinPulseAccepted` after ExactDevice COM adapter substitution. Historical 27/28 RED preserved; no production source fix; MASTER/VERIFY handle-bound identity review pending. Evidence/run outcome pending.

## 2026-10-24 — PHX-L-APPS UTC23 exact-HEAD CI checkpoint

- PHX-L-APPS UTC23 (2026-10-24T23:55Z) — DRAFT #197 exact-HEAD Windows #40140886546, source unchanged: handover job 121012216899 SUCCESS; Windows job 121012248315 FAILED only at native C# fake-OS diagnostic with `UNEXPECTED exact_open_time_adapter_swap_must_refuse: connected=True, expected_connected=False` and `NATIVE_DIAGNOSTIC_MISMATCH`. Fixture compiled 0 errors, PAY-0717/0718 PASS, subsequent strict Windows build, NSIS, artifact and release SKIPPED. This is intended test-only open-time adapter substitution RED, NOT hardware/paid-money proof or unrelated compile failure. MASTER/VERIFY review requested on PR #197 comment 6391011069 for handle-bound identity proof; WMI recheck alone is not proof. Without reliable opened-handle identity, coin admission MUST remain inhibited. No production source fix/merge, PR remains DRAFT/UNMERGED; P0 #31/#32/#43/#34 and physical 150 cuts/30-device soak NO-GO. NEXT: await independent review of opened-handle identity and test observability before app-only source changes.
