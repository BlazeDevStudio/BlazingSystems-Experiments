# PHX-HARDWARE UTC01 — PR #367 exact-head final evidence

Repository: BlazeDevStudio/BlazingSystems-Experiments  
Role: PHX-HARDWARE  
PR: #367 (OPEN / DRAFT / UNMERGED)  
Branch: phoenix/hw-deny-latch-monotonicity-20261127-utc21  
Docs/PR HEAD: 4e558a06ff558dffef8a966a6e412029e7340119  
Source/test SHA: 985a54c289b8e3c796c2bcc977f652b178b293c0

## Terminal exact-head results

- Focused #46089846162, job 140807946248: PASS.
- Mbed #46089846114: 3/3 PASS — source contract, ESP32 core 3.3.13, ESP32 core 4.0.0.
- Full #46089846111: terminal FAILURE at validation job 140808002601, QA-owned tests/controllers.sh:21 config_revision presence assertion. All 14 target/platform jobs including Android passed; downstream simulation/update/sign/publication stages skipped.

## Ownership / next action

PHX-QA replaces the stale positive marker assertion with source-linked deny-only vectors. PHX-CORE owns the authenticated register/poll/receipt/disposition contract. PHX-HARDWARE keeps coin and relay admission denied and does not add a fake config_revision or response_sig. P0 #177 remains open.

Child #368 is separate and based on this exact #367 head; its evidence is tracked in its own PR and handover. Do not transfer results between PRs.

Physical GPIO/relay, LittleFS power-loss, 150 power cuts, 30-device/24-hour soak and electrical pulse/recovery remain NOT TESTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
