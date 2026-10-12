# EasyMode 7.0 validation record

## 2026-10-10 checkpoint
- 17 pure accounting/attribution assertions PASS on the R281 OpenWrt 24.10.8 ucode runtime, using only `/tmp/emti-test` files.
- 5 executable Node tests PASS: aggregation, date filters, billing boundaries, escaping/CSV injection, unavailable values.
- Collector, DNS controller and rpcd plugin compile on that runtime.
- Isolated read-only collector detected 2 deduplicated upstream devices, 4 wireless interfaces and 2 observed clients. No installed application, network configuration or firmware changed. Initial CPU conversion defect was found and corrected.
- Generated observer rules pass `nft --check` on R281; rules were NOT installed there.
- Deterministic package builder produced core plus six edition IPKs and six offline archives. These await clean-install validation.
- GitHub Linux validation environment established successfully at de0189ddd58e609b525c03eb0b3aa46f982a87b4.

## Pending acceptance evidence
GitHub VM installation/upgrade/uninstall; private RPC/CSRF tests; real forwarded counters; DNS lifecycle; corruption recovery; BIOS/UEFI boot; UI mobile/live/error behavior; uploaded checksum verification. Physical hardware deployment remains NOT HARDWARE VERIFIED. No v7 release is published at this checkpoint.


## 2026-10-12 physical preview checkpoint (supersedes earlier deployment status)
- R281 OpenWrt 24.10.8: real Core/Cellular IPK installation succeeded after fixing missing tar directory entries. Management UI retained; monitoring /traffic/ returns its assets with correct MIME types.
- Real HTTP API: unauthenticated snapshot denied; administrator authentication returns fresh data. Service enabled and running; no current collector error.
- Real browser: signed in; Overview, WiFi, Internet Data, Devices, Websites, Apps, Reports and Settings render; no console errors observed. Destructive settings actions were not exercised on the user's live network.
- Real forwarded per-device counters and domain estimates populated. Laptop counters increased during actual traffic. Controlled 1 MiB test endpoint returned HTTP 403; a smaller OpenWrt download succeeded, but background traffic prevents exact-byte attribution validation. Do not describe this as an isolated throughput accuracy test.
- 29 accounting assertions pass in R281 ucode; modified collector compiles; JS syntax check passes.
- Physical reboot, factory reset, exact byte accuracy, exhaustive IPv6/VLAN/offload testing and long-term memory stability are still NOT VERIFIED.
- GitHub run 38079512294: package/image builds pass; VM SSH connection fails before integration tests. Production release gate remains failed. No v7 release is published.


## 2026-10-13 activity timestamps
- 34 ucode assertions PASS including separate per-device DNS timestamps and opt-out cleanup; 8 Node tests PASS including ten-row expansion, identity isolation, timestamp ordering and stale/recent classification.
- Installed backend/UI on R281, collector compile passes, live API returns fresh activity for two identities with no collector error.
- Timestamps reflect sample observation time; not precise request time. Historical per-device timestamps are not reconstructed.

- Live browser verification: site table showed 10 rows, Show all expanded to 132 retained rows, Show 10 restored 10. Per-device page displayed 7 identity-specific timestamped domains. Apps displayed timestamp columns and 3 rows. No browser console errors. Browser cache version fix verified.
