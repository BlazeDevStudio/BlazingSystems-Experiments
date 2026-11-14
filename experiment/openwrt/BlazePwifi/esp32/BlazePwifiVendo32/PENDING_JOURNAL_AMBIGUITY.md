# Boot-time unpaid coin journal ambiguity — DENY / preserve

## Verified dangerous behavior (draft source of PR #283 / #293)
The previous `loadPending()` treated every failed `readPendingFile()`
as identical to “no journal.” If `pending.dat` was corrupt or unreadable,
or if `pending.new` and `pending.bak` coexisted after a power cut, the
controller could start accepting additional pulses, overwrite a journal,
or rename/delete a different unacknowledged coin record.
The fixed-size 17/33-byte nonce and target arrays were checked with
`strlen()` before proving either string had a terminating NUL byte.

## Implemented behavior (both ESP8266 and ESP32)
1. Empty journal (no `/pending.dat`, `/pending.new`, `/pending.bak`)
   retains the previous behavior, subject to all *other* enable/auth gates.
2. Exactly one journal is validated using the existing magic, checksum,
   pulse limit and now **bounded NUL terminator checks**. A valid
   record is loaded in memory as pending; it is not renamed or deleted
   during boot, so a separate uncredited record cannot be silently lost.
3. Corrupt/unreadable single journal, or any two/three candidates,
   sets `journalRecoveryRequired=true`. The firmware does **not**
   choose a candidate, format, rename or remove the original evidence.
   Boot relay/LED acceptance and the raw GPIO coin-edge handler
   explicitly deny intake; new pending saves and clear operations
   also refuse the ambiguous state.
4. The recovery flag does not auto-clear. An explicit authorized,
   independently reviewed reconciliation procedure is required before
   the device can safely resume receiving paid coins. A valid backed-up
   record is not permission to discard an unknown newer one.

## Reproducible source-linked tests
```sh
python3 experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/pending_journal_recovery_lab.py
```
This compiles the real sketch `pendingChecksum`, `readPendingFile`,
`loadPending` and `applyOutputs` implementations against fake LittleFS
and exercises 16 cases per board: empty/primary/new/bak; checksum,
truncation, missing NULs, short strings, pulse range, conflicting
journals, read/open failure and file-byte preservation.

These are **host-side synthetic tests**, not actual power cuts,
flash durability, authenticated receipts, safe firmware migrations, or
real GPIO verification. PHX-CORE must specify final receipt ACK and
journal reclamation rules, and PHX-QA must test interrupted writes and
electrical failure on designated noncustomer boards. Production stays NO-GO.
