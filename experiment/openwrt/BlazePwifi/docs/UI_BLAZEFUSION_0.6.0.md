# BlazeFusion 0.6 — one visual system, separate trusted business engines

**Status: development preview, source integration complete on the Full web console, release blocked.** 2026-10-08, Asia/Manila. Owner-provided references: `coreui-react-v1.0.0.zip` and `metis-v1.0.0.zip`, inspected locally; uploads themselves are **not** committed.

## Uploaded source audit

| Source archive | Internal package and runtime | License/provenance | Intended use |
|---|---|---|---|
| `coreui-react-v1.0.0.zip` | `@coreui/coreui-free-react-admin-template` version `5.7.0`; React 19, Redux, React Router, CoreUI components, Chart.js, Vite | Included MIT `LICENSE`, copyright creativeLabs Łukasz Holeczek (2026); ThemeWagon distributor | CoreUI component/operations hierarchy **as inspiration**. The full React SPA is not deployed onto a low-RAM router |
| `metis-v1.0.0.zip` | `metis-admin-dashboard` version `3.6.0`; Bootstrap 5.3, Alpine.js, ApexCharts, Sass/Vite | Included MIT `LICENSE.md`, copyright 2014 Aigars Silkalns/Colorlib and contributors; ThemeWagon distributor | Calm forms, compact table density, native-feeling dashboards and contrast **as inspiration**; no Alpine/runtime duplication |
| Existing BlazePwifi console | BlazePwifi authenticated, CSRF-protected CGI + TailAdmin-inspired offline CSS | Keep existing `/vendor/tailadmin/LICENSE` and original attribution | **Only authoritative business UI/controller**, owner of paid session and security state |

The archive titles say `v1.0.0` but internal project versions are **5.7.0** and **3.6.0**, respectively. Neither archive is itself a PisoWiFi/coinslot/rental-engine replacement. No npm package install, sample admin credentials, demo sales, upstream login forms, third-party logos or promotional images were imported from the ZIPs. BlazeFusion styling and JS are authored independently. If a future build distributes actual upstream template assets/source, include both unmodified MIT notices and a precise attribution inventory.

## Architecture: one system of record, capability-targeted presenters

```text
   Authenticated operator (browser or native admin)
             |
   BlazeFusion design tokens + capability-aware UI
             |
    ┌────────┼─────────────┬────────────┐
 Full OpenWrt Lite/Standalone   PC/OrangePi    Native Android/Windows
  web shell   web shell          web/react?     launcher/EXE
    |             |                  |             |
    └─────────────┴───────────┬──────┴─────────────┘
                        BlazePwifi SERVER
                 CGI auth/CSRF/roles/accounting
                 prepaid event ID ledger, rentals
                 policies, vouchers, remote VPN
                             |
             ESP controllers / serial coin hardware
```

**Presentation components can be shared. Credentials, balances, permissions and coin events must remain server-owned.** Lite, Standalone and rental-only variants use feature detection and must not display controls unavailable on that device. Remote PC consoles are clients, not new authorities. Android BlazeRental Device Owner is a native Launcher3 app, not a WebView wrapper. Windows SoftTimer is a native EXE; do not change timer or COM selection for a CSS refresh.

## What was actually integrated in Full BlazePwifi

- Added lightweight, self-hosted `openwrt/rootfs/www/blazepwifi/vendor/blazefusion/blaze-fusion.css` on top of the existing local TailAdmin-inspired stylesheet.
- Added `blaze-fusion.js` — strictly UI preference selection, static nav symbols, no network calls or unauthenticated APIs, only non-sensitive `blazepwifi.console.appearance.v1` stored in browser localStorage with private-mode fallback.
- Added accessible **Appearance** selector in the existing authenticated topbar. `fusion` blends data-dense CoreUI card hierarchy with Metis smooth forms and spacing; `compact` reduces dashboard footprint; `comfort` gives larger touch targets. All modes keep actual data labels, metric sources, business API and established QR/actions unchanged.
- Added `tests/v060_ui_fusion.sh` with local-source-only and no-second-backend assertions; `simulation/browser_v04_audit.py` uses Playwright to verify mode switching, reload persistence, QR workflow continuity and layout accessibility basics.
- No CDN fetch, React/Redux/Alpine/ChartJS/ApexCharts bundle on router; the CPU/RAM and network footprint remains bounded. Avoid claiming benchmark superiority until measuring the same router/client workload.

## Subsystem rollout — implementation status

| Target | Planned integration | Status / release gate |
|---|---|---|
| Full OpenWrt Ruijie, x86, Orange Pi | BlazeFusion CSS + selector + existing authorized CGI | **Development implementation; exact CI and browser regression pending** |
| Lite/EasyMode (other OpenWrt devices) | Share Fusion/Compact/Comfort visual tokens while retaining EasyMode's native UBus, R281 light/dark and per-device networking controls | **EasyMode R281 v4.2.3 opt-in offline PREVIEW builder/test implemented; NOT installed or published.** Other five editions and BlazePwifi Lite remain unmodified |
| Standalone Rental / R281 firmware | Self-contained BlazeFusion themes in `profiles/standalone-rental/openwrt/rental-standalone.html`; separate rental CGI and installer unchanged | **Implemented on development source, CI pending**. Published RC9 remains frozen; Device Owner versus standard QR workflows unchanged and require separate security work |
| PC/Orange Pi advanced console | Optional CoreUI React build generated in CI and served as immutable static assets; secure same-origin API/role adapter, CSP, bundle size budget, and safe fallback to low-resource local console | **Design candidate, not yet built/shipped**; do not deploy raw ZIP `node_modules` onto firmware |
| BlazeRental Android APK | Translate theme colors, typography, cards and spacing into native Java resources/screens; retain Launcher3 Device Owner security, same permanent signing cert and higher-code rescue | **Visual design handoff only**; existing Android v0.5.3-dev candidate unchanged by this frontend integration |
| Windows BlazePisonet SoftTimer | Native WinForms/WPF visual design tokens, accessible layout, COM device selectors, money/timer state unchanged | **Visual design handoff only**, protect existing EXE and signed publisher chain |
| ESP8266/ESP32 portal / tiny AP | Very small CSS variables, no React, Alpine or Chart.js; hardware web endpoints remain coin authority | **Visual design handoff only**, optimize AP captive UX and heap use later |
| Public WiFi vendo / phone rental captive pages | Keep child-friendly purchase/credit UI separated from operator dashboard; no admin links, token or device keys exposed | **No behavioral or UI change in this integration** |

## Standalone Rental UI source rollout

- **One-file/offline requirement:** the Standalone installer copies `rental-standalone.html` directly to `/rental/index.html` and provides only the separate local QR library. Therefore the development branch implements Fusion/Compact/Comfort via **inlined styles and inlined appearance-only JS**; it does not depend on Full's `/vendor/blazefusion` assets, React, Alpine or Vite.
- **Unified choice:** the appearance selector uses the same nonsecret `blazepwifi.console.appearance.v1` key as Full when accessed on the same origin, with safe default Fusion, plus failure-tolerant private browsing handling. No client-session, QR enrollment token, device credential or money is saved in localStorage.
- **Trust boundaries intact:** Standalone `/cgi-bin/blaze-rental-admin`, `blaze-rental-profile`, login/session/CSRF and rental event ledger remain unchanged. This is not permission to use the Full CGI on rental-only appliances. No upgrade-to-Full event, network mutation or rent extension is performed by a theme change.
- **Evidence:** `tests/v060_standalone_fusion.sh` asserts local installation, JS syntax, authorized CGI routes and style mode existence; `simulation/standalone_fusion_browser.py` runs a real Chromium test on a **mocked HTTPS origin**, uses only read-only rental-list/controller-list responses, checks mobile 360/390px overflow, operator sign-out visibility and generated desktop/mobile screenshots. The full existing authenticated Playwright QR test stays in CI.
- **Deployment status:** source development only. Real Standalone UI/Android provisioning, multi-device rental operations, installer and enrollment security must be tested independently before issuing a new published Standalone release. Frozen RC9 assets are unchanged.

## EasyMode R281 staged preview — no deployed upgrade

The independent project [EasyMode](../../easymode-project/) contains a preserved R281 v4.2.3 web snapshot and a separate 5.0.0 alpha installer. Modifying either directly would make historical release comparisons unreliable or risk installed WAN, modem, repeater and SMS functions. This integration therefore stays **under** `experiment/openwrt/easymode-project/integrations/blazefusion/` as an off-device overlay build.

- `blazefusion.css` uses EasyMode's own CSS variables, respects its server-owned `data-theme` light/dark and `--accent` controls. `blazefusion.js` shares the same appearance-only preference key used by Full and Standalone, with no UBus access or credentials.
- `build-preview.py --output NEW_DIRECTORY` copies only the R281 v4.2.3 static `root/www` tree and inserts appearance controls alongside the unchanged Logout button. It rejects unknown anchors and existing output; **it is not a router installer**.
- `tests/v060_easymode_fusion.sh` verifies source immutability, no new API authority, staged local assets and fail-closed destination safety. `simulation/easymode_fusion_browser.py` uses Chromium on a loopback-only preview; it reveals the operator shell **without actually logging in** to check theme modes and mobile responsiveness.
- No 4.2.4 firmware, 5.0 alpha runtime, OpenWrt network configuration, credentials, modem/SMS controls or billing features are updated. Source and tests must pass exact-head CI before contemplating separately authorized hardware rollout.

## Security, accessibility and performance gates

1. Appearance controls must be inert with respect to CSRF tokens, session cookies, user roles, coinslot operations, member accounts, rental credentials, Device Owner QR generation and banked seconds.
2. Do not mount an upstream sample login page or embed mock graphs/sales and declare the data real.
3. No remote JS/CSS/fonts; respect CSP, screen reader labels, tab/focus states, low-power reduced-motion and narrow 360px screens.
4. No stored credit amounts or access tokens in localStorage, even under the appearance namespace; themes are non-sensitive only.
5. Preserve the original TailAdmin license. If source from MIT CoreUI/Metis is **copied** later, keep each corresponding full copyright/license notice.
6. CI must pass `v060_ui_fusion.sh`, static/admin security, real Playwright style and QR flows, Android native and target hardware matrices, and ensure signed release migration/recovery gates are independently satisfied.

## Next exact work after safe checkpoint

Inspect exact-head CI for BlazeFusion smoke/Playwright failures. Once green, freeze the verified source SHA, update root/current/ledger handovers **after** source edits, and keep PR #30 draft. Next, implement one reused token specification and roll it out in stages: Lite/EasyMode first, then Standalone Rental and native Windows/Android surfaces, using each subsystem's separate release and security tests. A 0.6.0 production release must still solve transaction-aware migration and physical data backup/restore; this UI integration does not waive those P0 blocks.
