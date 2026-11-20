# PHX-HARDWARE handover — quarantine log field encoding

Date: 2026-11-15 UTC  
Role: PHX-HARDWARE  
Task: #266 cleanup-first, bounded evidence-integrity repair  
Branch: `phoenix/hardware-quarantine-log-encoding-20261115`  
Base: `phoenix/hardware-journal-clear-verify-20261115@657cfce54008ccf1c431c4d5d323471cabebb649`

## Proven defect

ESP32 and ESP8266 wrote the raw server rejection body and target directly into
the line-oriented `/quarantine.log`. Embedded CR, LF, tab, backslash, or other
control bytes could create extra-looking records or ambiguous evidence during
manual recovery. This does not require a valid financial ACK: the rejection
body is recorded precisely on the negative path.

## Change

- Add one parity-checked `quarantineLogField()` helper to both sketches.
- Encode CR, LF, tab and backslash using visible escape sequences.
- Replace other C0/DEL control bytes with `?`.
- Bound nonce, target and reason fields to 40, 80 and 128 output bytes.
- Mark truncation with `...` while retaining the single physical record line.
- Keep the journal/quarantine file names, append/readback behavior, network
  response handling and shared ACK schema unchanged.
- Add an exact-source ASan/UBSan host regression covering normal text, hostile
  CR/LF/tab/backslash input, nonprinting control bytes, truncation, a tight
  boundary and a zero-length boundary for both sketches.

No server, finance, migration, shared API/schema, GPIO, journal record, release
or destination-repository files changed.

## Evidence classification

CI status is pending at handover creation. Control-byte injection is SIMULATED.
Physical LittleFS persistence, flash wear, reboot behavior, electrical pulses,
150 power cuts and 30-device/24-hour soak remain NOT TESTED.

## Review request

PHX-QA should independently inspect the exact-source encoder and confirm every
quarantine append remains one physical line under hostile inputs. PHX-CORE
still owns the separate signed durable ACK contract; this change does not make
the current coin `"ok":true` response sufficient for production acceptance.

Standing PRODUCTION NO-GO remains. No merge, flash, reset, migration, customer
deployment, real money, signer, release or promotion is authorized.
