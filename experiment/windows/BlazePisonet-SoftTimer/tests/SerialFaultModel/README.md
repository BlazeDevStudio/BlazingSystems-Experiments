# SoftTimer serial pin-change fault model (PHX-L-APPS #164)

**Status: SOURCE-DERIVED MODEL, NOT PRODUCT CODE / NOT PHYSICAL ACCEPTANCE.** This test models the preexisting `SerialHardware.cs` behavior in the actual active Phoenix development branch (source blob `0362e027ae98fad52e55396de63ac7b3f312be40`, development commit `9df0a7e7cae31fc06d098d5a0ea7ae27f56a75ed`). The earlier identity guard in PR #175 was **closed without merge** by repo owner. Do not relabel its green CI as installed.

Run without hardware, secrets, paid ledgers or packages:

```sh
python3 experiment/windows/BlazePisonet-SoftTimer/tests/SerialFaultModel/serial_fault_repro.py
```

Expected exact output on the current modeled source (four checks):

```text
REPRODUCED normal active-high 60ms input: 1 accepted pulse(s)
REPRODUCED ACTIVE-LOW false coin after transient serial read failure: 1 accepted pulse(s)
REPRODUCED completed 50ms real pulse lost to delayed callback: 0 accepted pulse(s)
REPRODUCED two RI notifications accepted without measuring width: 2 accepted pulse(s)
MODEL RESULT: 4/4 deterministic traces reproduced. NOT native CLR or physical-device acceptance.
```

This fixture mirrors four source rules, **not C# execution**: `GetSignal` returns `false` when a serial read throws; `IsSignalActive` inverts that return for active-low; `OnPinChanged` samples the *current* signal for any pin-change notification and estimates pulse width from callback delivery times; Ring notifications bypass measured-width filtering. The first trace is a control; the next three are potential unsafe/failure paths. A production patch requires a separate C# Windows regression with injected status-read errors and a defined protocol/capture device, not just rewriting this model to pass.

## Realistic test progression / hard stops

1. Unit contract: a fresh port generation, attached-device identity and healthy signal sample must be required before a paid pulse can be emitted. Fail closed for exceptions/hotplug/reconfigure.
2. Isolated Windows virtual-port test with com0com or a serial mock supporting modem-line changes. Confirm actual API callbacks, flow control, erroneous pin notifications and actual elapsed-time capture. The virtual driver must be compatible with current Windows runner policies and signed where required. Do not disable Secure Boot / driver-signing protections to make testing pass.
3. Bench electrical: exact coin acceptor and RS-232/USB adapter, documented level shifter/optoisolation, pulse width/spacing, active polarity, 12 V boundaries and safe DTR/RTS output configuration.
4. Financial/replay: never equate delivered callback with an irreversibly accepted coin; use authenticated transaction authority and durable idempotency from CORE. No money credits or migration in this test.
5. Real 150 power cuts plus 30-device/24-hour soak are outside the model and must be independently evidenced before customer use.

## Public reference ledger (inspection only, nothing copied)

- [Microsoft .NET SerialPort.PinChanged](https://learn.microsoft.com/en-us/dotnet/api/system.io.ports.serialport.pinchanged): warns callback ordering/delay and secondary-thread execution.
- [RJCP.DLL.SerialPortStream](https://github.com/jcurl/RJCP.DLL.SerialPortStream): reference discussion of driver/chipset limitations; not a drop-in guarantee of lossless coin pulse capture.
- [com0com](https://github.com/tanvir-ahmed-m4/com0com): open-source GPL virtual COM pair and modem lines; no kernel driver included, bundled or installed by this repository change.
- [Ki0xk/Coinslot](https://github.com/Ki0xk/Coinslot): coin burst-to-framed-event example; MCU-based, not an MCU-free substitute.
- [OpenPisoWiFi](https://github.com/haliknihudas666/open-piso-wifi) and [IntraFi/PisoWiFiVendo](https://github.com/IntraFi/PisoWiFiVendo): architecture comparison only, not software imported into Windows SoftTimer.

No reverse-engineered proprietary binary, competitive artwork, third-party library, driver or secret was imported. Forensic results are limited to source-level analysis and the named model runs.
