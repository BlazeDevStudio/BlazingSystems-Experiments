#!/usr/bin/env python3
"""TEST ONLY: guard the two literal Git blobs, instrument a temporary C# copy.
Exit 3 = inconclusive precondition / checkout mismatch, never evidence of safety.
Never modify src/BlazePisonet.SoftTimer/SerialHardware.cs or the fake API.
"""
from pathlib import Path
import subprocess
import sys

SOURCE = Path("experiment/windows/BlazePisonet-SoftTimer/src/BlazePisonet.SoftTimer/SerialHardware.cs")
FAKE = Path("experiment/windows/BlazePisonet-SoftTimer/tests/NativeSerialPinFaultLab/FakeOsAndAppTypes.cs")
EXPECTED = {
    SOURCE: "3f049a1b1d94b5a5f61e825563580d797d65b9d0",
    FAKE: "8e6cc716c06388668bbf426053da8aa272cd5c47",
}
TARGET = Path("experiment/windows/BlazePisonet-SoftTimer/tests/NativeSerialReconnectGuard/Generated/ActualSerialHardware.cs")
ANCHOR = "        if (!TryReadCoinActive(cfg, out var active, source, epoch))"
REPLACEMENT = (
    "        var sampleOk = TryReadCoinActive(cfg, out var active, source, epoch);\n"
    "        TestOnlyHooks.ObserveSample(sampleOk, active);\n"
    "        if (!sampleOk)"
)
def inconclusive(detail):
    print("INCONCLUSIVE_EXIT_3: " + detail, file=sys.stderr)
    return 3

def main():
    if Path.cwd().joinpath(".git").exists() is False:
        return inconclusive("repository root not selected")
    for path, expected in EXPECTED.items():
        if not path.is_file():
            return inconclusive(f"missing guarded Git file: {path}")
        result = subprocess.run(["git", "hash-object", str(path)],
                                capture_output=True, text=True, check=False)
        actual = result.stdout.strip()
        if result.returncode != 0 or actual != expected:
            return inconclusive(f"exact blob guard failed {path} expected={expected} actual={actual}")
        print(f"EXACT_GIT_BLOB_GUARD_PASS {path} {actual}")
    source = SOURCE.read_text(encoding="utf-8")
    if source.count(ANCHOR) != 1 or "TestOnlyHooks.ObserveSample" in source:
        return inconclusive("instrumentation anchor missing/duplicate or source already modified")
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(source.replace(ANCHOR, REPLACEMENT, 1), encoding="utf-8")
    print("INSTRUMENTED_DISPOSABLE_COPY_ONLY: one C# CTS sample transition hook")
    return 0

if __name__ == "__main__":
    sys.exit(main())
