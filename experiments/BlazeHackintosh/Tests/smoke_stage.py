"""Windows CI only: assemble a non-bootable fixture with the *real* 1.0.8 Sample.plist.

Uses deliberately fake kext/AML/HFS content; no produced files are uploaded,
installed, signed, put on a USB disk or claimed compatible with real hardware.
"""
import json
import plistlib
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from component_manifest import input_files, sha256
if len(sys.argv) not in (2, 3):
    raise SystemExit("Usage: smoke_stage.py OpenCore-1.0.8-RELEASE.zip [Toolkit.exe]")
official_zip = Path(sys.argv[1]).resolve()
command = [sys.executable, str(PROJECT / "blazehackintosh.py")]
if len(sys.argv) == 3:
    command = [str(Path(sys.argv[2]).resolve())]

with tempfile.TemporaryDirectory(prefix="BlazeResearchNoBoot-") as temp:
    base = Path(temp)
    kexts, acpi = base / "kexts", base / "acpi"
    kexts.mkdir()
    acpi.mkdir()
    for name in ("Lilu", "VirtualSMC", "WhateverGreen"):
        contents = kexts / (name + ".kext") / "Contents"
        (contents / "MacOS").mkdir(parents=True)
        with (contents / "Info.plist").open("wb") as f:
            plistlib.dump({"CFBundleIdentifier": "org.example." + name,
                           "CFBundleExecutable": name}, f)
        (contents / "MacOS" / name).write_bytes(b"TEST_FIXTURE_NOT_INSTALLABLE")
    for name in ("SSDT-PLUG.aml", "SSDT-EC.aml"):
        (acpi / name).write_bytes(b"FAKE-AMLS-ONLY")
    (base / "HfsPlus.efi").write_bytes(b"FAKE-HFSPLUS")
    (base / "report.json").write_text(json.dumps({
        "format_version": 2, "read_only": True, "hardware": {
            "cpu": {"name": "Intel Core i5-4570"}, "motherboard": {"model": "FICTIONAL TEST MOTHERBOARD"},
            "firmware": "UEFI", "gpus": [{"name": "HD4600", "pci_id": "8086:0412"}]}}), encoding="utf-8")
    (base / "smbios.json").write_text(json.dumps({
        "SystemProductName": "iMac14,2", "SystemSerialNumber": "TEST12345678",
        "MLB": "EXPERIMENTAL00001", "SystemUUID": "be01ea11-abcd-4f29-b65d-118ee1d92c51",
        "ROM": "000000000002"}), encoding="utf-8")
    items = input_files(kexts, acpi, base / "HfsPlus.efi")
    entries = [{"path": path, "sha256": sha256(file),
                "source_url": "https://example.org/fictional-ci-fixtures",
                "license_id": "MIT", "release": "test-only"}
               for path, file in sorted(items.items())]
    (base / "components.json").write_text(json.dumps(
        {"schema_version": 1, "files": entries}), encoding="utf-8")
    output = base / "BlazeEFI-NonBootable-CI"
    args = command + [
        "stage-haswell-efi", "--zip", str(official_zip),
        "--kext-dir", str(kexts), "--acpi-dir", str(acpi),
        "--hfs-driver", str(base / "HfsPlus.efi"), "--smbios-json", str(base / "smbios.json"),
        "--component-manifest", str(base / "components.json"),
        "--report", str(base / "report.json"), "--output-dir", str(output),
        "--macos", "12", "--acknowledge-research-only"
    ]
    p = subprocess.run(args, capture_output=True, text=True, timeout=100, check=False)
    if p.returncode != 0:
        raise AssertionError(f"Research candidate staging failed (code {p.returncode}): {p.stderr[-2200:]} {p.stdout[-2200:]}")
    data = json.loads(p.stdout)
    assert data["ocvalidate_passed"] and not data["boot_verified"]
    assert (output / "EFI/OC/config.plist").is_file()
    audit = subprocess.run([sys.executable, str(PROJECT / "stage_audit.py"), "--folder", str(output)],
                           capture_output=True, text=True, timeout=30, check=False)
    assert audit.returncode == 0, (audit.returncode, audit.stdout, audit.stderr)
    assert json.loads(audit.stdout)["integrity_passed"]
    with (output / "EFI/OC/config.plist").open("ab") as fp:
        fp.write(b"CI-MODIFIED")
    audit_bad = subprocess.run([sys.executable, str(PROJECT / "stage_audit.py"), "--folder", str(output)],
                               capture_output=True, text=True, timeout=30, check=False)
    assert audit_bad.returncode == 2, (audit_bad.returncode, audit_bad.stdout, audit_bad.stderr)
    assert not json.loads(audit_bad.stdout)["integrity_passed"]
    print("Actual OpenCore 1.0.8 EFI reference staging passed official ocvalidate on synthetic CI fixtures; NOT boot-tested.")
