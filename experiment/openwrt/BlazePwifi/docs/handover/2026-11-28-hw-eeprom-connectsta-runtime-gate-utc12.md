# PHX-HARDWARE UTC12 — EEPROM begin failure blocks station registration

- Repository: \`BlazeDevStudio/BlazingSystems-Experiments\`
- Role: \`PHX-HARDWARE\`
- PR: [#374](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/374), OPEN / DRAFT / UNMERGED
- Branch: \`phoenix/hw-eeprom-begin-failclosed-20261128-utc07\`
- Parent: #373 at \`3783654a3c9862598bbb714268c536fb8b34578b\`
- Source/test HEAD: \`4da5e7a8b8911538f2d3905e559f983b773e703d\`

## Implemented

\`config_storage_integrity_lab_harness.py\` now source-extracts the real ESP8266 \`connectSta()\` body and executes it in a C++11 fake-network harness. \`config_storage_integrity_lab.py\` runs four normal cases and two failure injections.

Normal cases:
1. \`configStoreReady=false\`: no station begin, register POST or remote-control transition.
2. Empty SSID: no network operation.
3. Wi-Fi disconnected through 12 seconds: no register POST.
4. Valid store and connected Wi-Fi: one station begin, one register POST, existing deny transition.

Mutations:
- Remove the config-store readiness guard: expected exit 10 after \`CONFIG_STORE_UNAVAILABLE_PRECONDITION_READY\`.
- Remove the connected-state guard: expected exit 20 after \`CONFIG_STORE_READY_DISCONNECTED_PRECONDITION_READY\`.

## Evidence and limitations

- Local g++ 14.2.0 / C++11 / ASan+UBSan smoke: 4/4 normal cases PASS; 2/2 mutations rejected with exact exits/markers.
- Full repository Python runner: NOT RUN locally (container could not resolve github.com).
- GitHub Actions at exact SHA: NOT RUN / no commit status exposed; connected GitHub tools provide no workflow-dispatch action. Do not classify this as CI VERIFIED.
- No production firmware, CORE contract, QA tests, finance, signer, witness, migration, COE or physical device changed.
- Physical EEPROM/NVS brown-out and all physical hardware acceptance remain NOT TESTED. Coin/relay remains denied.

**Next:** obtain exact-head Poll/Full Actions evidence and QA review before further work.
