"""CI acceptance: verify actual upstream ocvalidate from pinned archive on Windows.

The fixture is intentionally NOT a usable EFI. Expect official schema rejection,
not success, with an authentic 1.0.8 checker version. No disk modifications.
"""
import json
import plistlib
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
if len(sys.argv) not in (2, 3):
    raise SystemExit("Usage: smoke_official.py APPROVED-OPENCORE-ZIP [PACKAGED-TOOLKIT-EXE]")
package = Path(sys.argv[1]).resolve()
command = [sys.executable, str(PROJECT / "blazehackintosh.py")]
if len(sys.argv) == 3:
    command = [str(Path(sys.argv[2]).resolve())]

with tempfile.TemporaryDirectory(prefix="blaze-verified-ci-") as tmp:
    root = Path(tmp) / "EFI" / "OC"
    root.mkdir(parents=True)
    (root / "OpenCore.efi").write_bytes(b"test-fixture-not-real-opencore-efi")
    names = ("ACPI", "Booter", "DeviceProperties", "Kernel", "Misc", "NVRAM", "PlatformInfo", "UEFI")
    with (root / "config.plist").open("wb") as stream:
        plistlib.dump({name: {} for name in names}, stream)
    outcome = Path(tmp) / "inspection.json"
    p = subprocess.run(command + [
        "validate-efi", "--efi", str(root), "--ocvalidate-package", str(package),
        "--run-official-ocvalidate", "--output", str(outcome)],
        capture_output=True, text=True, timeout=75, check=False)
    if p.returncode != 2:
        raise AssertionError(f"Expected invalid EFI fixture error code 2: code={p.returncode}, stderr={p.stderr[:1000]}")
    data = json.loads(outcome.read_text(encoding="utf-8"))
    check = data.get("official_ocvalidate") or {}
    if not all([check.get("archive_verified"), check.get("version_matched"), check.get("attempted")]):
        raise AssertionError(f"Upstream binary was not truly executed and version-checked: {check}")
    if check.get("passed") or data.get("ocvalidate_passed") or check.get("boot_verified"):
        raise AssertionError("Invalid EFI fixture incorrectly passed")
    print("Pinned upstream OpenCore 1.0.8 ocvalidate executed; intentionally invalid EFI rejected.")
