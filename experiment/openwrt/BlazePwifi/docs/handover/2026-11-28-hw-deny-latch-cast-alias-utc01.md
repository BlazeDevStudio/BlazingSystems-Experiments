# PHX-HARDWARE UTC01 — C-style and reinterpret-cast alias regression

**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Parent:** [PR #367](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/367) at `4e558a06ff558dffef8a966a6e412029e7340119`  
**Child branch:** `phoenix/hw-deny-latch-cast-alias-20261128-utc01`  
**Status at commit:** source/test change committed; exact-head CI pending.

## Proven gap

Master's architecture contract explicitly limited the previous deny-latch regex evidence: C-style reference casts and `reinterpret_cast` reference aliases were not in the demonstrated mutation set. The prior lab rejected 10/10 alias mutations per board but did not exercise these two cast families.

## Change

- Extend the bounded reference-alias matcher to recognize `reinterpret_cast<T&>(protectedField)`.
- Recognize C-style reference aliases such as `(bool&)relayEnabled`.
- Extend direct wrapper checks so a reference cast used as an expression cannot bypass the alias-declaration matcher.
- Add four failure injections per board: two reinterpret-reference forms and two C-style reference forms.
- Extend comment/string decoys to ensure cast-looking text remains ignored.
- Update the expected mutation count from 10/10 to 14/14 per board.

This is a bounded source-contract improvement, not a complete C++ AST/dataflow proof. Opaque helper returns, arbitrary memory corruption and electrical faults remain outside the demonstrated matrix.

## Scope and safety

No production `.ino` sketch, GPIO runtime behavior, CORE API, finance, journal disposition, QA-owned assertion, migration, signer, witness or COE file changed. Coin/relay admission remains deny-only. No device operations or production actions were performed.

## Evidence

Exact-head Focused Hardware [run #46094348641](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46094348641), job `140822175939`, passed on branch head `d0439b62e678a94854498a47becef7f2c09ac3e9`. Both boards rejected 14/14 alias mutations, including 4/4 C-style/reinterpret-cast cases. Full [run #46094348644](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46094348644) failed its validation job at the stale root handover freshness gate before target jobs completed; this checkpoint refreshes the root handover and requires a fresh Full rerun. No terminal Full result is claimed.
