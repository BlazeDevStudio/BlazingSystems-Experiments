# HANDOFF — Optional MCU-free coin-slot input via Windows COM and OpenWrt USB serial
Date: 2026-10-24 (Asia/Manila)  
Status: **specified only / implementation + physical acceptance still pending**  
Owning work item: [Project Phoenix issue #164](https://github.com/BlazingSystems/BlazingSystems-Experiments/issues/164)

## Operator intent

Permit a coin acceptor to serve BlazePisonet SoftTimer directly from a PC's built-in RS-232 / USB-to-RS232 COM port, **or** directly from a USB-host-capable BlazePwifi OpenWrt router using a supported USB serial converter, without needing a separate programmable ESP8266/ESP32 controller. Continue supporting all existing ESP, Windows coordinator and standalone deployments. This request does **not** authorize deploying an unsafe passive 12V-to-serial cable or activating commercial payments with unverified pulse counting.

## Reconcile the existing system before implementing

- **Windows partially implemented already:** `experiment/windows/BlazePisonet-SoftTimer/README.md` describes `InternalPcTimer`, `ExternalTimerBoard`, `BlazePisonetTimer`, `StandardOneToOne` and `CentralizedCoordinator`. `src/BlazePisonet.SoftTimer/SerialHardware.cs` enumerates native/USB COM, monitors CTS/DSR/DCD/RI, filters pulse width/debounce, and rebinds named hardware. Retain this code and perform a fault/reliability audit, not an unnecessary rewrite. Observe that a status-pin event is not a hardware pulse FIFO and exact-device fallback must never silently switch to another cash input.
- **OpenWrt not yet implemented:** `experiment/openwrt/BlazePwifi/docs/ARCHITECTURE.md` describes the ESP signed controller -> durable target/accounting path, not a router-attached coin reader. Add a feature-gated, lightweight local USB serial adapter as another trusted input *into the current* Vendo/accounting contract. Do not duplicate money/session authority.
- Leave existing standalone rental/R281, router WAN/LAN/VLAN config, firmware signing, live money stores, installed units, and production tags unchanged.
- Existing open P0 blockers (#31, #32, #43, #34) and guarded release requirements remain **open**. No product v0.6.0 release claim from this document.

## Wiring and capability rules

**Two coin acceptor types are distinct:**

1. Native RS-232 **data-protocol** model: read and validate the documented serial frames/checksums and unique sequence when supplied by the device.
2. Common 12V power + ground + pulse model: add a model-specific isolated, level-correct conditioner (e.g. optical isolation + verified RS-232-compatible interface) **before** CTS/DSR/DCD/RI. Do not connect a raw 12V pulse, raw TTL, or coin supply to DB9 signals or router USB serial input. Externally power the acceptor to its rating; design isolation, returns, transient and reversal protection. A USB-to-TTL board is not automatically equivalent to a USB-to-RS232 DB9 adapter.

**OpenWrt eligibility:** check real USB host mode; USB power budget; installed USB serial core + matching FTDI / CP210x / Prolific / CH34x driver or CDC-ACM; enumerated compatible `/dev/ttyUSB*` or `/dev/ttyACM*`; actual modem-input capabilities if using control-line pulses; persistent hardware identity or explicit operator binding; memory/flash budget and correct permissions. A router's unused console UART/debug header is **not** a substitute for a dedicated external coin interface. Do not expose cash-input ports to arbitrary LAN clients.

Useful source references:
- [OpenWrt serial interface guidance](https://openwrt.org/docs/techref/hardware/port.serial)
- [Linux USB serial device nodes and drivers](https://cdn.kernel.org/doc/html/latest/usb/usb-serial.html)
- [Microsoft serial signal pin changes](https://learn.microsoft.com/en-us/dotnet/api/system.io.ports.serialpinchange)
- [FTDI DB9 signal directions](https://www.ftdichip.com/Support/Documents/DataSheets/Cables/DS_UT232R-500.pdf)

## Functional contract

1. One configuration selector: `Disabled | ESP Controller | Local Serial (PC) | Local Serial (OpenWrt)` (show only relevant platform modes); auto-probe is informative **only**, never auto-enables cash acceptance.
2. Serial device selection: native COM or VID/PID/USB serial on Windows; device path + verified USB identity on Linux. Pin or protocol selection, input active polarity, pulse min/max, debounce, inter-pulse gap, grouped pulses/denomination, max transaction size, signal-health and optional acceptor inhibit.
3. Transport drivers emit normalized capture data to **one** accounting owner: stable source identity, event ID from a verifiable capture/journal, target/window nonce, pulses/value, timestamp, sequence when provided, integrity mode and input status. Never credit two clients from one pulse/burst; never fall back to 'last active client' on stale/ambiguous targets.
4. Reuse BlazePwifi replay protection, target binding, durable receipt/credit and signed controller semantics. Native router input must enter through an internal restricted handler; it must not be allowed to forge external controller credentials or bypass storage durability.
5. Windows timer/central coordinator use the already existing station and member authority; centrally managed banked time remains BlazePwifi authoritative when chosen. Keep local 1:1 and centralized modes operational even when serial input is disabled.
6. Dedicated diagnostic mode shows pulse edges, duration, source and rejection reason without adding time. Normal paid admission is disabled until the actual port/interface has passed self-test, operator calibration and an approved hardware profile.
7. On missing device, unexpected reboot, stuck pin, noise, duplicate sequence, queue overrun, ambiguous short burst or driver fault: **stop acceptance/inhibit when available**, expose service health, preserve durable in-flight state, avoid invented payment/ACK. Never silently change to another device with the same COM name or `ttyUSB0` number.
8. Define the *power-loss boundary*: host software cannot acknowledge/count pulses that disappear while it is off. An unbuffered status pin cannot meet lossless accounting alone. Commercial acceptance therefore requires a vetted acceptor inhibit/escrow scheme, or a dedicated counter/latch that preserves and reports a verifiable event through power failure, or equivalent physical evidence-backed mitigation.

## Implementation tasks and acceptance evidence

### Windows SoftTimer
- Audit current `SerialHardware.cs` and UI: COM device binding fallback, `SerialPinChanged` fidelity, polarity, pin support, hotplug/reconnect and pulse grouping. Treat apparent successful compilation as separate from hardware validation.
- Build a simulated-input regression for noise, pulse bursts, duplicate edges and hot-unplug; ensure station credit is idempotent and the EXE still builds.
- Preserve existing ESP integration and all current 1:1 / centralized behaviors.

### OpenWrt BlazePwifi
- Add **disabled-by-default** USB-serial capability probe, suitable procd service/UCI settings, small binary/portable input backend, package dependencies only on eligible target profiles.
- Verify native framed-data mode first where possible; for CTS/DSR/DCD/RI read path, test actual adapter + Linux ioctl/driver support (no assumptions about support across chipsets). Test reboots, device enumeration shifts and USB restarts.
- Adapt normalized accepted events to current coin targeting and accounting with a single authority (not a second ledger or duplicate transaction writer). Add an admin Hardware → Coin Input Source / diagnostics / supported chipsets / acceptance-warning control.

### Required tests before operator-paid deployment
- Trace and document each exact coin acceptor / conditioned circuit / RS-232 dongle / PC or router combination.
- Test no false/duplicate/lost events over supported pulse patterns; multi-pulse denomination grouping; accepted coin in a selected target window; unauthorized and replay attempts; simultaneous clients; unplug/replug during payment; service crash; bad power and stuck inputs.
- Perform >=150 **real hardware** power interruptions and a 24-hour / 30-device load soak within the wider Project Phoenix acceptance program. Compare physical coins, captured events and durable receipts. Any unexplained loss/extra credit is a blocker; where the capture method cannot preserve pulses across shutdown, **mark it noncommercial** rather than invent a passing result.
- Each slice must have a source-level test, evidence, fresh exact-head CI, independent review and guarded PR. Record actual hardware-tested device/adapter model, not a generic "all USB routers" claim.

## Delivery order / delegation

**Slice 1 — Windows SoftTimer owner:** inspect existing COM implementation, eliminate unsafe rebinding/pulse assumptions and add tests.  
**Slice 2 — OpenWrt BlazePwifi owner:** implement capability probe + optional hardware reader with cash acceptance disabled.  
**Slice 3 — Accounting/protocol owner:** map both backends into existing controller/target transaction model and test duplicate/reboot boundaries.  
**Slice 4 — Acceptance owner:** assemble safe interfaces, measure actual coin pulses and pass physical/regression matrix before turning on production paid admission.

Cross-subsystem edits only for interface/contract consistency; do not use this feature to expand scope into unrelated rentals, OTA or styling. Update canonical project handovers upon guarded integration, preserving active concurrent branches and evidence.

**Next actionable step:** Assign issue #164 to the relevant Windows/OpenWrt maintainers, then start isolated Slice 1 with a reproducible failing test of a real pulse failure mode. No unverified release or payment enablement.
