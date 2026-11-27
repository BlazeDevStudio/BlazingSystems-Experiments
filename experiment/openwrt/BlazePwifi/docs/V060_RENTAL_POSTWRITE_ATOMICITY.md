# RENT-20261022-ATOMIC — coin-controller paid lease/receipt crash audit

**Severity:** P0 #32. **Status:** confirmed non-atomic v1 behavior in a *synthetic local process-death* test; production accounting cannot ship as v0.6.0. **Scope:** Full BlazePwifi `openwrt/rootfs/usr/lib/blazepwifi/rental.sh`. No Standalone/R281 firmware, customer DB, native rental APK, published tag, signer, or production controller changed.

## Evidence

Branch: `fix/rent-20261022-atomic-postwrite-proof` from development base `72987a376d66b2a9027a0685e9681fc5cd45b674`.

Test source: `tests/v060_rental_postwrite_process_crash_red.sh` commit `29ec396007b0a9aca278c1d649682e15db1bf691`. Focused workflow `.github/workflows/blazepwifi-v060-rental-postwrite-red.yml` commit `e6a7484a8301e11a39fdab7893797a547a7737a0`.

[Exact focused Actions #39741266570](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39741266570) **COMPLETED SUCCESS as a RED *defect reproduction***. CI reads exit 1 and only reports success if the exact expected-unsafe signature appears, never labels financial safety green.

Test uses canonical private `/tmp/blaze-rent-postwrite-*` with `BLAZE-SYNTHETIC-ONLY` marker and fictional device/controller IDs. It invokes the unmodified source's actual `bp_rental_apply_coin` after overriding **only** the receipt append function to terminate the shell process with status 78, immediately after the actual lease rename. New process reads persisted state; checks no receipt and no ACK, marker persists, and repeat/simultaneous second-device credit is refused. It does **not** simulate electrical brownout or fsync reliability.

Observed output:

```text
RENT-20261022-ATOMIC RED: process died after rental lease rename; lease=124056, receipt absent, no ACK, quarantine persists
NOT PRODUCTION SAFE: this is a synthetic process-death boundary, not physical power-loss acceptance
EXPECTED RED REPRODUCED: v1 is non-atomic; this is not a release approval.
```

## Exact source defect

In `bp_rental_apply_coin`, `bp_paid_begin` persists an uncertainty marker and takes writer lock, `bp_rental_device_write` performs a separate atomic replacement of `rental-devices.tsv`, and `bp_rental_append_paid_receipt` appends to `rental-events.tsv`. A process death between those I/O operations can leave paid seconds visible without their corresponding durable receipt; the marker prevents blind ACK/retry but cannot reconcile automatically. Existing `tests/v060_rental_receipt_midwrite.sh` proves late EIO containment but did not prove *post-restart* state across process termination. This focused test fills that gap.

## Supported repair direction — gates before source replacement

1. Audit the existing `tests/fixtures/rental_v2_atomic.py` and `tests/v060_rental_v2_atomic_bridge.py`: they already demonstrate a **single-authority lease+receipt atomic replacement** in an explicitly mock state directory. Do **not** copy their Python fixture under production rootfs or enable `BP_RENTAL_V2_LAB` for real customers.
2. Plan reversible migration of v1 `rental-devices.tsv` and `rental-events.tsv` with frozen coin admission, an owner-reviewed protected backup and receipt reconciliation; refuse upgrade if marker exists, source is malformed or signer/witness is unavailable. Legacy controller nonce uniqueness, payment times, and old receipts must be preserved.
3. Define a target-supported durable transaction helper (file `fsync` + parent dir `fsync` and a validated monotonic/freshness witness), idempotent signed controller request and ACK. Test interruption **before rename**, **after rename before durability**, **after durable commit before ACK**, **during migration**, and **post-reboot retry**. Require no success response until whole lease+receipt transaction is durable.
4. Preserve the existing preflight revalidation, paid writer lock, replay identity/digest validation, rental HMAC/Device Owner security and fail-closed uncertain marker. A working atomic toy fixture is not evidence of independent rollback protection or physical flash integrity.
5. Move from expected-RED to genuine **GREEN** on unchanged test entrypoints only after a real correctly integrated runtime fix, then full exact-head CI, physical coin/supply interruption and 30-device soak. P0 #31/#32/#43/#34 and production release remain open until then.

**Next exact action:** implement an isolated supported-runtime lease+receipt journal with tests for all three crash boundaries and migrate/read-only shadow comparison; do not modify or publish production firmware without real hardware and signer acceptance.
