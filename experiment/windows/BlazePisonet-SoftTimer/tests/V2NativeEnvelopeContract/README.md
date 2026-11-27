# PAY-0715: off-device SoftTimer ↔ v2 native journal contract

**Test-only, not a customer protocol feature.** This console fixture is intentionally outside the SoftTimer `src/` project and excluded from installer/published EXE inputs. It signs canonical v2 HMAC-SHA256 envelopes for the already-existing, `BLAZE_FIXTURE_ONLY`-compiled native journal `experiment/openwrt/BlazePwifi/tools/v060_journal_authority_native.c`.

Canonical ASCII message (terminates in exactly one newline):

```text
BLAZE-V2-AUTH-FIXTURE/1\tCONTROLLER\tSEQ\tCONTROLLER:SEQ\tOP\tSUBJECT\tTARGET\tUNITS\tNOW\n
```

The 32-byte synthetic controller key is parsed as exactly 64 lowercase hex characters. The native v2 fixture independently authenticates with HMAC-SHA256, stores a monotonic per-controller sequence with the balance and receipt in the same fsync+rename snapshot, and only replays a matching signed receipt; it rejects a conflicting same-sequence event or stale/gapped sequence. Valid operations: AM add, SM subtract, TM transfer, LR lease extension. The transfer has an explicit distinct destination; all other operations use `-`. Identifiers are restricted to 1–32 ASCII characters beginning with a letter. The sequence is strictly positive and no larger than 100 million.

**Tests:** `dotnet run --project ... -- --selftest` compares independent fixed HMAC and SHA-256 fingerprint vectors and rejects invalid fields. The GitHub native-journal gate runs `tests/v060_softtimer_native_v2_roundtrip.sh` with the .NET CLI and the *compiled* C native binary, including two controller identities, 2 distinct keys, actual COMMIT/REPLAY, tamper/collision refusal, pre-rename failure, post-rename lost ACK and transfer conservation. The Windows workflow runs the .NET fixture under the pinned SDK. All inputs are disposable synthetic credentials and a private /tmp test root.

**NOT implemented/authorized:** a SoftTimer production v2 network sender, durable Windows monotonic sequence reservation, delivery/retry queue or key provisioning, OpenWrt customer v2 CGI, v1 migration, HMAC-key rotation, external antirollback monotonic freshness, physical flash durability or signing/release. The existing v1 `BlazePwifiClient` remains the ONLY shipped controller path and must not silently downgrade a future v2 request to its legacy SHA256 signature. P0 issues #31/#32/#43/#34 remain open.

Never pass real financial keys on command lines and never place this test project or native test binaries under OpenWrt rootfs or Windows installer packaging.
