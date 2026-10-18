"""Expert-only Haswell desktop EFI candidate builder. No disks touched.

Requires verified upstream OpenCore, individually provided hardware evidence,
kext/ACPI/HFS dependencies and user-generated SMBIOS identity. An ocvalidate
success checks schema, NOT hardware bootability or trust in supplied kexts.
"""
from __future__ import annotations

import hashlib
import json
import os
import plistlib
import re
import shutil
import stat
import tempfile
import uuid
import zipfile
from pathlib import Path

from official_ocvalidate import verify_archive, run_official_ocvalidate
from efi_validator import validate_efi

KEXTS = ("Lilu.kext", "VirtualSMC.kext", "WhateverGreen.kext")
ACPIS = ("SSDT-PLUG.aml", "SSDT-EC.aml")
ARCHIVE_MEMBERS = (
    "X64/EFI/BOOT/BOOTx64.efi",
    "X64/EFI/OC/OpenCore.efi",
    "X64/EFI/OC/Drivers/OpenRuntime.efi",
    "Docs/Sample.plist",
)
MAX_MEMBER = 24 * 1024 * 1024
MAX_SOURCE_FILE = 32 * 1024 * 1024
MAX_KEXT_TOTAL = 128 * 1024 * 1024
RESEARCH_NOTICE = (
    "STRUCTURALLY CHECKED RESEARCH CANDIDATE ONLY. NOT VERIFIED BOOTABLE. "
    "Never migrate to internal ESP before real hardware testing and backups."
)


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_file(path: Path) -> None:
    """Regular file, no symlinks; never dereference attacker-provided links."""
    if path.is_symlink() or not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("Required local dependency is not a regular file: " + path.name)
    if not 0 < path.stat().st_size <= MAX_SOURCE_FILE:
        raise ValueError("Required dependency has invalid size: " + path.name)


def _safe_bundle(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        raise ValueError("Missing or symlinked kext bundle: " + path.name)
    total = 0
    for here, dirs, files in os.walk(path, followlinks=False):
        for name in [*dirs, *files]:
            p = Path(here) / name
            if p.is_symlink():
                raise ValueError("Symlink inside kext bundle forbidden: " + path.name)
            if p.is_file():
                _safe_file(p)
                total += p.stat().st_size
                if total > MAX_KEXT_TOTAL:
                    raise ValueError("Kext bundle exceeds size limit: " + path.name)
            elif not p.is_dir():
                raise ValueError("Special file in kext bundle forbidden: " + path.name)
    _safe_file(path / "Contents" / "Info.plist")
    try:
        info = plistlib.loads((path / "Contents" / "Info.plist").read_bytes())
        binary = info.get("CFBundleExecutable")
        identifier = info.get("CFBundleIdentifier")
        if not isinstance(identifier, str) or "." not in identifier:
            raise ValueError("Kext Info.plist lacks a bundle identifier")
        if not isinstance(binary, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", binary):
            raise ValueError("Kext Info.plist lacks a safe executable name")
        _safe_file(path / "Contents" / "MacOS" / binary)
    except (OSError, plistlib.InvalidFileException, TypeError) as error:
        raise ValueError("Invalid kext Info.plist: " + path.name) from error


def _read_json(path: str | Path, *, limit: int = 1048576) -> dict:
    target = Path(path)
    _safe_file(target)
    if target.stat().st_size > limit:
        raise ValueError("JSON input exceeds size limit")
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as e:
        raise ValueError("Invalid JSON report") from e
    if not isinstance(value, dict):
        raise ValueError("JSON input must be an object")
    return value


def _hardware(report: dict, macos: str) -> dict:
    from blazehackintosh import lookup_cpu, load_catalog
    h = report.get("hardware")
    if not isinstance(h, dict) or not report.get("read_only"):
        raise ValueError("Recognized read-only hardware scan report is required")
    cpu = h.get("cpu") or {}
    if not isinstance(cpu, dict) or not isinstance(cpu.get("name"), str):
        raise ValueError("Exact CPU model required")
    family = lookup_cpu(cpu["name"], load_catalog())
    if family["family_id"] != "intel-haswell" or not re.search(r"\bi[57]-(?:4570|4770)\b", cpu["name"], re.I):
        raise ValueError("Only explicitly mapped desktop Haswell i5-4570/i7-4770 research profiles allowed")
    if h.get("firmware") != "UEFI":
        raise ValueError("Confirmed UEFI firmware required; Unknown and Legacy BIOS refused")
    if not isinstance(h.get("motherboard"), dict) or not h["motherboard"].get("model"):
        raise ValueError("Exact motherboard model required; this is not a compatibility endorsement")
    gpus = h.get("gpus")
    if not isinstance(gpus, list) or len(gpus) != 1 or not isinstance(gpus[0], dict) or gpus[0].get("pci_id") != "8086:0412":
        raise ValueError("Research profile restricted to sole 8086:0412 Haswell HD 4600 iGPU; other graphics need separate evidence")
    if macos != "12":
        raise ValueError("Only macOS 12 research-target profile currently accepted")
    return {"cpu": cpu["name"], "cpu_family": "intel-haswell",
            "gpu_pci_id": "8086:0412", "motherboard": h["motherboard"]["model"],
            "firmware": "UEFI", "macos": "12", "confidence": "Research Only"}


def _identity(path: str | Path) -> dict:
    item = _read_json(path)
    keys = ("SystemProductName", "SystemSerialNumber", "MLB", "SystemUUID", "ROM")
    if any(k not in item or not isinstance(item[k], str) for k in keys):
        raise ValueError("SMBIOS JSON must have SystemProductName, SystemSerialNumber, MLB, SystemUUID and ROM")
    if item["SystemProductName"] != "iMac14,2":
        raise ValueError("Only explicitly selected iMac14,2 reference identity is permitted")
    if not re.fullmatch(r"[A-Z0-9]{11,17}", item["SystemSerialNumber"]):
        raise ValueError("Malformed local SystemSerialNumber")
    if not re.fullmatch(r"[A-Z0-9]{17}", item["MLB"]):
        raise ValueError("Malformed local MLB")
    if not re.fullmatch(r"[A-Fa-f0-9]{12}", item["ROM"]):
        raise ValueError("ROM must be 6-byte hex (never your MAC address)")
    try:
        identity = uuid.UUID(item["SystemUUID"])
    except (ValueError, AttributeError) as error:
        raise ValueError("Malformed SystemUUID") from error
    if identity.int == 0:
        raise ValueError("All-zero SystemUUID forbidden")
    return item


def _archive_payload(zf: zipfile.ZipFile, suffix: str) -> bytes:
    matches = []
    for entry in zf.infolist():
        name = entry.filename.replace("\\", "/")
        if name == suffix or name.endswith("/" + suffix):
            if (entry.is_dir() or stat.S_ISLNK(entry.external_attr >> 16) or
                    not 0 < entry.file_size <= MAX_MEMBER):
                raise ValueError("Unsafe or oversized official ZIP member: " + suffix)
            matches.append(entry)
    if len(matches) != 1:
        raise ValueError("Expected exactly one official archive member: " + suffix)
    payload = zf.read(matches[0])
    if len(payload) > MAX_MEMBER:
        raise ValueError("Extracted member exceeded maximum size")
    return payload


def _config(sample: bytes, identity: dict) -> bytes:
    if len(sample) > 1024 * 1024:
        raise ValueError("Official sample plist too large")
    config = plistlib.loads(sample)
    if not isinstance(config, dict):
        raise ValueError("Official sample is not a dictionary")
    mandatory = ("ACPI", "Booter", "DeviceProperties", "Kernel", "Misc", "NVRAM", "PlatformInfo", "UEFI")
    if any(not isinstance(config.get(k), dict) for k in mandatory):
        raise ValueError("Official Sample.plist has missing schema sections")
    config = {k: v for k, v in config.items() if not k.startswith("#")}
    kernel_add = config["Kernel"].get("Add", [])
    by_name = {v.get("BundlePath"): v for v in kernel_add if isinstance(v, dict)}
    if any(n not in by_name for n in KEXTS):
        raise ValueError("Official sample lacks required kext schema templates")
    config["Kernel"]["Add"] = [dict(by_name[n], Enabled=True) for n in KEXTS]
    config["ACPI"]["Add"] = [{"Comment": "User-provided: verify ACPI correspondence",
                               "Enabled": True, "Path": n} for n in ACPIS]
    # Remove sample placeholder patches/references; do not auto-guess unsafe quirks.
    config["ACPI"]["Delete"] = []
    config["ACPI"]["Patch"] = []
    config["Booter"]["Patch"] = []
    config["Kernel"]["Patch"] = []
    config["Kernel"]["Block"] = []
    config["Misc"]["Tools"] = []
    config["Misc"]["Entries"] = []
    config["DeviceProperties"]["Add"] = {
        "PciRoot(0x0)/Pci(0x2,0x0)": {"AAPL,ig-platform-id": bytes.fromhex("0300220D")}}
    config["DeviceProperties"]["Delete"] = {}
    config["UEFI"]["Drivers"] = [
        {"Arguments": "", "Comment": "Official OpenCore runtime", "Enabled": True,
         "HideVerbose": False, "LoadEarly": False, "Path": "OpenRuntime.efi"},
        {"Arguments": "", "Comment": "User-provided HFS driver", "Enabled": True,
         "HideVerbose": False, "LoadEarly": False, "Path": "HfsPlus.efi"},
    ]
    # A reference candidate has no vault signing material.
    config["Misc"]["Security"]["Vault"] = "Optional"
    generic = config["PlatformInfo"]["Generic"]
    for key in ("MLB", "SystemProductName", "SystemSerialNumber"):
        generic[key] = identity[key]
    generic["SystemUUID"] = str(uuid.UUID(identity["SystemUUID"])).upper()
    generic["ROM"] = bytes.fromhex(identity["ROM"])
    return plistlib.dumps(config, fmt=plistlib.FMT_XML, sort_keys=False)


def _output_path(path: str | Path) -> Path:
    out = Path(path).absolute()
    if out.name in ("", ".", "..", "EFI", "BOOT", "OC") or not out.name.startswith("BlazeEFI-"):
        raise ValueError("Destination must be a NEW directory named BlazeEFI-* (never EFI/OC or disk root)")
    if out.exists() or out.is_symlink():
        raise ValueError("Refusing to overwrite an existing output directory or link")
    parent = out.parent
    if not parent.is_dir() or parent.is_symlink() or parent.resolve() != parent:
        raise ValueError("Destination parent must be a real, already-existing directory")
    return out


def build_candidate(*, hardware_report: str | Path, official_zip: str | Path,
                    kext_dir: str | Path, acpi_dir: str | Path, hfs_driver: str | Path,
                    smbios_json: str | Path, output_dir: str | Path, macos: str,
                    consent: bool = False) -> dict:
    if not consent:
        raise ValueError("Expert must explicitly acknowledge research-only EFI and official binary execution")
    out = _output_path(output_dir)
    facts = _hardware(_read_json(hardware_report), macos)
    identity = _identity(smbios_json)
    kext_dir, acpi_dir, hfs_driver = Path(kext_dir), Path(acpi_dir), Path(hfs_driver)
    for k in KEXTS:
        _safe_bundle(kext_dir / k)
    for a in ACPIS:
        _safe_file(acpi_dir / a)
    _safe_file(hfs_driver)
    check = verify_archive(official_zip)
    if not check["verified"]:
        raise ValueError("Official OpenCore release SHA-256 gate failed: " + str(check["error"]))
    with zipfile.ZipFile(official_zip) as zf:
        official = {n: _archive_payload(zf, n) for n in ARCHIVE_MEMBERS}
    plist = _config(official["Docs/Sample.plist"], identity)
    stage = Path(tempfile.mkdtemp(prefix=".blazehackintosh-stage-", dir=out.parent))
    try:
        oc = stage / "EFI" / "OC"
        (stage / "EFI" / "BOOT").mkdir(parents=True)
        for sub in ("Drivers", "Kexts", "ACPI"):
            (oc / sub).mkdir(parents=True, exist_ok=True)
        (stage / "EFI" / "BOOT" / "BOOTx64.efi").write_bytes(official["X64/EFI/BOOT/BOOTx64.efi"])
        (oc / "OpenCore.efi").write_bytes(official["X64/EFI/OC/OpenCore.efi"])
        (oc / "Drivers" / "OpenRuntime.efi").write_bytes(official["X64/EFI/OC/Drivers/OpenRuntime.efi"])
        shutil.copyfile(hfs_driver, oc / "Drivers" / "HfsPlus.efi")
        for a in ACPIS:
            shutil.copyfile(acpi_dir / a, oc / "ACPI" / a)
        for k in KEXTS:
            shutil.copytree(kext_dir / k, oc / "Kexts" / k, symlinks=False)
        (oc / "config.plist").write_bytes(plist)
        local = validate_efi(stage)
        if not local["structural_checks_passed"]:
            raise ValueError("Local EFI references failed: " + "; ".join(local["errors"][:3]))
        upstream = run_official_ocvalidate(stage, official_zip, consent=True)
        if not upstream["passed"]:
            raise ValueError("OpenCore 1.0.8 official ocvalidate did not pass: " + str(upstream["error"]) +
                             " " + upstream["checker_output"][:1200])
        files = sorted(p for p in stage.rglob("*") if p.is_file())
        manifest = {
            "generator": "BlazeHackintosh 0.1.4 experimental",
            "classification": "Structurally Validated Only",
            "hardware_evidence": facts,
            "ocvalidate_version": "1.0.8", "ocvalidate_passed": True,
            "hardware_boot_verified": False, "usable_installer": False,
            "notice": RESEARCH_NOTICE,
            "requirements_remaining": [
                "Physical device boot/USB acceptance", "Review motherboard-specific ACPI and firmware quirks",
                "Verify SMBIOS, GPU framebuffer, USB mapping, storage and supported Apple license",
                "Confirm downloaded kext versions, provenance, hashes and licensing",
            ],
            "files": [{"path": str(p.relative_to(stage)).replace("\\", "/"), "sha256": _hash(p)}
                      for p in files],
        }
        (stage / "RESEARCH-ONLY.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (stage / "DO-NOT-INSTALL.txt").write_text(RESEARCH_NOTICE + "\n", encoding="utf-8")
        if out.exists() or out.is_symlink():
            raise ValueError("Output location became occupied during preparation")
        os.rename(stage, out)
        return {"output_dir": str(out), "classification": "Structurally Validated Only",
                "ocvalidate_passed": True, "boot_verified": False, "ready_for_internal_esp": False,
                "file_count": len(files), "manifest": str(out / "RESEARCH-ONLY.json")}
    finally:
        if stage.exists():
            shutil.rmtree(stage)
