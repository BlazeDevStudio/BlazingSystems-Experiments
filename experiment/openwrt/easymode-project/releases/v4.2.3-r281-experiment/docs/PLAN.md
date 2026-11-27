# Easy Mode reconciliation, October 2026

Preserve the user's live 4.1.4 source and settings. Audit actual browser actions against LuCI/UCI, repair scanning, add an upstream-address repeater option with captive-network handling, and verify the existing load-balancing control. Publish source only to Experiments; this is not a finished firmware release.

1. Capture live source/config privately and inventory every visible control.
2. Reproduce scan failure; replace synchronous nested rpcd scans with a bounded asynchronous worker. Compare results with native LuCI.
3. Add explicit routed versus IPv4 relay mode. Relay clients obtain DHCP from upstream; preserve a separate management network. Use relayd where upstream WDS support is unknown. Do not claim full layer-2 transparency or seamless address-preserving cellular failover. Provide routed backup access separately.
4. Add captive/Piso link-only policy. Never infer a captive portal solely from a 10.0.0.1 address. In captive mode, association and an assigned IPv4 address suffice; internet failure must not disconnect or revert the uplink.
5. Audit failover/load balance route behavior, source selection, rollback, and error reporting. Keep actual upstream availability visible.
6. Run browser control inventory, reversible save/readback comparisons, validation paths, native LuCI reference checks, and bounded live diagnostics. Validate destructive controls through navigation/confirmation only, preserving user messages and configuration.
7. Publish reviewed source, tests, and an honest coverage matrix. Hardware-dependent tests remain explicitly pending if no suitable upstream exists.

Ruling: proceed under the user's explicit autonomous-work and publication authorization; do not repeat design approval questions. Keep unchanged live source as the baseline, not the old October 1 working copy.
Ruling: topology changes must retain management and rollback; a captive portal is a working local network even before internet authentication.

Ruling: add dedicated SSID scope per latest user steering; preserve home DHCP, routing and DNS. Upstream IPv4 relay is separate from home internet policy.
Ruling: preserve TTL-1 captive replies only within the relay client subnet; evidence came from packet traces, and the fix passed an HTTP portal test. No authentication bypass is performed.
Ruling: publish the tested source revision with explicit pending firmware/physical-client/dual-uplink limits. Do not mark the broader project successful.

4.2.2: investigate the physical-client portal failure on the newly selected upstream; add independent repeater AP name/password/open settings. Preserve earlier version snapshots. Continue USSD, LEDs, build/reset defaults and installer validation; no success claim until evidence supports it.

4.2.2 evidence: captive upstream requires shared source identity; retain explicit user choice and label the shared-login tradeoff. Preserve newer open AP security. Candidate immutable root is independently validated but not flashed.

4.2.3: signal LEDs implemented and live-tested; native fresh-key read verified. Remaining hardware gate is wired flash/boot/reset validation. USSD remains unresponsive after an independent forty-second capture.
