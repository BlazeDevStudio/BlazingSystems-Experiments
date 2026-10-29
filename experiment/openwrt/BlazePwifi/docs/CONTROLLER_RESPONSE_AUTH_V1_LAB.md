# PHX-G controller response auth v1 — nonproduction integration contract

**Status: SOURCE-LEVEL LAB PROPOSAL, NOT A PROVISIONING OR PAID-ADMISSION AUTHORIZATION.**
The existing server uses `blazepwifi.main.vendo_key` for controller request authentication. It already provides OpenSSL HMAC-SHA256 for rental status. Reuse **that same existing test/installed secret** only to authenticate configuration *responses*; no new signing key, certificate, production wallet, or physical device workflow is created.

## Wire surface (compatible extension)

Real CGI `register` / `ping` / `poll` keep their original JSON fields. They append `config_auth`:
`version:1`, `action`, `controller_id`, `request_nonce`, `revision`, `policy_sha256`, `insert`, `target_nonce`, `expires`, `admission_allowed:false`, `signature`.

The server signs the UTF-8, no-trailing-newline message with **HMAC-SHA256** keyed by existing `vendo_key`:

```text
blazepwifi-controller-response-v1|action|controller_id|request_nonce|revision|policy_sha256|insert|target_nonce|expires|DENY
```

- `policy_sha256` is SHA-256 of the exact serialized legacy `controller` object bytes (compact JSON, field order as emitted). All existing settings are therefore covered. `target_nonce`, `expires`, original nonce, controller ID, action, and numeric revision are also covered.
- Only the signed `config_auth` fields are part of this v1 bound response. The old `insert` field remains for legacy parsing but **must not enable relays**. The signed `admission_allowed` value is unconditionally false until a separate protected device authority exists.
- Any malformed/absent key, OpenSSL failure, invalid revision, target or nonce returns a fail-closed `ok:false` CGI response, never unsigned fallback.

## Mandatory consumer acceptance (HARDWARE owner only)

Verify pinned local preprovisioned request secret, complete HMAC, controller identity and exact pending request nonce, policy digest, revision and target/window binding **before displaying/applying non-actuating configuration**. Reject malformed payload, tamper, nonce mismatch, missing config, changed key, timeout, and signed rollback. Preserve pending coin journals. Use no legacy plaintext `insert` as authority.

This response intentionally **does not** attest an independent authority or protected reboot highwater. Both the router and controller can share a rollbackable/extractable key; a legitimately signed **older** response could still be replayed after cold restart if local revision/history is rolled back. CORE and HARDWARE must keep coin/relay admission OFF until a separately authenticated monotonic controller-policy witness, protected signer, cold-start freshness and finance witness are implemented and independently accepted. PR #239 Phase A fail-closed behavior remains authoritative. These host fixtures are NOT hardware or crypto-provisioning acceptance.

Source evidence: `controller.sh` lab response helper, actual `cgi-bin/vendo` register/poll, and `tests/v060_controller_response_auth_v1.py` eight adversarial host cases. Historical signed CGI receipt replays remain unaffected.

## PHX-CORE Recovery I — confirmed v1 binding gap (2026-10-30)

**v1 is DENY-only, not a device/window authorization token.** The canonical HMAC omits target device/account owner identity and window kind (hotspot versus rental). Substituting those outside the HMAC leaves a valid v1 signature unchanged. The legacy insert bit is NOT an actuating instruction. The host negative case documents missing cryptographic binding, not rejection of those mutations.

Any separately reviewed versioned v2 proposal must bind unambiguously action, controller ID, pending request nonce, revision, complete policy digest, immutable target device/account owner ID, window kind, target nonce, window bounds/expiry, denial/admission decision, and protected freshness epoch/highwater. Strictly reject duplicate or ambiguous fields, unknown window kind, and cross-owner or cross-kind substitutions. This does not change v1 wire bytes, authorize paid intake, or establish protected freshness. Hardware coin and relay remain DENIED.
