# Tests

Run JavaScript tests with Node.js and Playwright installed. Set `PLAYWRIGHT_MODULE` to its module path if it is not on the normal module search path; `CHROME_PATH` may select an installed Chrome executable. Set `ROUTER_PASSWORD` privately in the process environment; `ROUTER_URL` defaults to `http://192.168.1.1` where supported. Create a local `work/` directory for reports. Never commit that directory.

- `wifi-security.mjs`: local security-classification cases.
- `subnets.uc`: run with ucode and the installed subnet helper.
- `uplink-config.uc CONFIG_DIRECTORY`: isolated UCI fixture, never point it at `/etc/config`. Supply fixture `network`, `wireless`, `firewall`, `dhcp`, `blaze` configs with radio0/radio1, two protected home APs, a LAN DHCP server, and the initial radio1 channel 36. No production passwords are needed.
- `probe-route.sh`: on a test OpenWrt host with ip-full and veth/network namespaces, reproduces the route-policy problem in a temporary namespace and checks the corrected gateway path.
- `scan-live.py`: live read-only scan/status responsiveness.
- `navigation-race.cjs`: delays a modem response and verifies that it cannot replace the newer Wi-Fi page.
- `browser-audit.cjs`: actual navigation, scan selections, invalid input, number formatting, inbox/native LuCI and logout. Sending is off unless `--send` and an explicitly authorized `SMS_TEST_NUMBER` are supplied.
- `button-saves.cjs`: **mutates and reloads live settings**. Requires an authorized test router and private backup. Default runs reversible saves/readbacks. `--ca-trial` enables a data-consuming speed/CA trial. `--diagnostics-only` runs only router diagnostics. Destructive confirmations are dismissed; user history is preserved.
- `diagnostics-live.py`: sequential API ping/diagnose/download checks (uses mobile data).

Tests report observed results, not guarantees of RF conditions or carrier support. The private packet-capture harness used for the repeater test is not distributed because it contains the owner's upstream network details.
