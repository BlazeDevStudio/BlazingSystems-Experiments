

## 2026-11-28 UTC01 — PHX-HARDWARE PR #368 deny-latch cast-alias regression

- Role: PHX-HARDWARE; branch: `phoenix/hw-deny-latch-cast-alias-20261128-utc01`.
- PR: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/368 (OPEN / DRAFT / UNMERGED).
- Source/test commit: `b35072bfb2b74f3bc4bdca31381d178261d1ae35`; pre-ledger docs head: `d8bf447e176f49a70d9a0a5de0133b7fc77c10ac`.
- Focused exact-head run #46094498476, job `140822646418`: PASS. ESP8266 and ESP32 each rejected 14/14 alias mutations, including 4/4 C-style/reinterpret-cast cases.
- Append-only guard in that focused run passed against the active-v0.6 base ledger (base_bytes=1132798; previous appended_bytes=75077). This entry is appended only; the existing ledger prefix is preserved byte-for-byte.
- Full run #46094498502 validation job `140822787592` failed only the handover freshness gate because this ledger checkpoint was stale at `4e558a06`. This append records the missing exact evidence; a new Full run is required.
- No production `.ino` or financial/CORE/QA interface changes. Physical hardware acceptance remains NOT TESTED; production NO-GO.
