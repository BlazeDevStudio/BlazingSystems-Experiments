#!/usr/bin/env python3
"""BlazeHackintosh v0.1.0 - read-only hardware discovery and research-only evaluation.

This module does NOT install macOS, generate OpenCore EFI, or write disks.
The CPU lookup is an explicit reference map, never a nearest-neighbour guess.
"""
from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))  # bundled PyInstaller data
CATALOG = ROOT / "Hardware-Database" / "families.json"
STATUS = "Research Only"
# Exact CPU SKU names to known CPU family. These are not compatibility or boot claims.
KNOWN_MODELS = (
    (r"\bi5-4570\b", "intel-haswell"),
    (r"\bi7-4770\b", "intel-haswell"),
    (r"\bi5-6500\b", "intel-skylake"),
    (r"\bi7-6700\b", "intel-skylake"),
    (r"\bi5-8500\b", "intel-coffee-lake"),
    (r"\bi7-8700\b", "intel-coffee-lake"),
    (r"\bRyzen 5 3600\b", "amd-zen-2"),
    (r"\bRyzen 7 3700X\b", "amd-zen-2"),
)


def load_catalog(path: Path = CATALOG) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("families"), list):
        raise ValueError("Unsupported hardware catalog schema")
    families = data["families"]
    if len(families) < 25:
        raise ValueError("Catalog must include at least 25 distinct families")
    ids = [f.get("id") for f in families]
    if len(ids) != len(set(ids)) or any(not isinstance(i, str) or not i for i in ids):
        raise ValueError("Family identifiers must be unique non-empty strings")
    for f in families:
        if f.get("vendor") not in ("Intel", "AMD"):
            raise ValueError("Invalid vendor for " + str(f.get("id")))
        if f.get("classification") != STATUS:
            raise ValueError("Unverified catalog family must remain Research Only")
        if not isinstance(f.get("references"), list) or not f["references"]:
            raise ValueError("Missing source for " + f["id"])
    return data


def lookup_cpu(cpu_name: str, catalog: dict) -> dict:
    """Return documented exact-model reference or explain no match.

    Matching a SKU identifies a family only; does not establish GPU, firmware,
    macOS version, chipset or OpenCore compatibility.
    """
    name = cpu_name.strip()
    if not name:
        return {"family_id": None, "classification": "Unknown", "reason": "CPU model was not provided"}
    matches = [family for expr, family in KNOWN_MODELS if re.search(expr, name, re.IGNORECASE)]
    family_ids = {f["id"] for f in catalog["families"]}
    if len(matches) != 1 or matches[0] not in family_ids:
        return {"family_id": None, "classification": "Unknown",
                "reason": "No explicit reference mapping; no automatic family substitution"}
    return {"family_id": matches[0], "classification": STATUS,
            "reason": "CPU SKU identified; macOS boot suitability is NOT established"}


def _run(args: list[str]) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=15, check=False)
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _powershell(command: str):
    raw = _run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command])
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _first(value):
    return value[0] if isinstance(value, list) and value else (value or {})


def _device_code(value: str) -> str | None:
    """Keep vendor/device PCI IDs; discard potentially unique PnP instance tails."""
    ven = re.search(r"VEN[_:]([0-9A-F]{4})", value or "", re.IGNORECASE)
    dev = re.search(r"DEV[_:]([0-9A-F]{4})", value or "", re.IGNORECASE)
    return f"{ven.group(1).upper()}:{dev.group(1).upper()}" if ven and dev else None


def _linux_pci_id(value: str) -> str | None:
    """Extract PCI numeric device ID from lspci -nn's [...] field."""
    matches = re.findall(r"\[([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\]", value or "")
    if not matches:
        return None
    vendor, device = matches[-1]
    return f"{vendor.upper()}:{device.upper()}"


def _win_firmware_type() -> str:
    """Windows 8+ GetFirmwareType. Report Unknown on failure, never infer BIOS."""
    try:
        import ctypes
        value = ctypes.c_uint32()
        ok = ctypes.windll.kernel32.GetFirmwareType(ctypes.byref(value))
        return {1: "Legacy BIOS", 2: "UEFI"}.get(value.value, "Unknown") if ok else "Unknown"
    except (AttributeError, OSError, TypeError, ValueError):
        return "Unknown"


def _items(value) -> list[dict]:
    """Win32 CIM emits an object for one item and a list for several."""
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _safe_size(value) -> int | None:
    """Reject negative, zero, bogus and floating-point storage capacities."""
    try:
        if value is None or isinstance(value, bool):
            return None
        size = int(value)
        return size if 0 < size < 2**70 else None
    except (ValueError, TypeError, OverflowError):
        return None


def scan_hardware() -> dict:
    """Read-only inventory. Never export serial/MAC/UUID, disk contents or PnP instance IDs."""
    host = platform.system()
    hardware = {"cpu": {"name": None, "vendor": None, "physical_cores": None},
                "motherboard": {"manufacturer": None, "model": None},
                "gpus": [], "firmware": "Unknown", "memory_bytes": None,
                "storage": [], "network_adapters": []}
    if host == "Windows":
        cpu = _first(_powershell(
            "Get-CimInstance Win32_Processor | Select-Object -First 1 Name,Manufacturer,NumberOfCores | ConvertTo-Json -Compress"))
        board = _first(_powershell(
            "Get-CimInstance Win32_BaseBoard | Select-Object -First 1 Manufacturer,Product | ConvertTo-Json -Compress"))
        gpus = _powershell(
            "Get-CimInstance Win32_VideoController | Select-Object Name,PNPDeviceID | ConvertTo-Json -Compress")
        nics = _powershell(
            "Get-CimInstance Win32_NetworkAdapter | Where-Object { $_.PhysicalAdapter -eq $true } | Select-Object ProductName,PNPDeviceID | ConvertTo-Json -Compress")
        disks = _powershell(
            "Get-CimInstance Win32_DiskDrive | Select-Object Model,Size,InterfaceType | ConvertTo-Json -Compress")
        memory = _first(_powershell(
            "Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory | ConvertTo-Json -Compress"))
        hardware["cpu"] = {"name": cpu.get("Name"), "vendor": cpu.get("Manufacturer"),
                           "physical_cores": cpu.get("NumberOfCores")}
        hardware["motherboard"] = {"manufacturer": board.get("Manufacturer"), "model": board.get("Product")}
        hardware["memory_bytes"] = _safe_size(memory.get("TotalPhysicalMemory"))
        hardware["firmware"] = _win_firmware_type()
        for gpu in _items(gpus):
            hardware["gpus"].append({"name": gpu.get("Name"),
                                     "pci_id": _device_code(gpu.get("PNPDeviceID", ""))})
        for nic in _items(nics):
            hardware["network_adapters"].append({
                "name": nic.get("ProductName"),
                "pci_id": _device_code(nic.get("PNPDeviceID", ""))})
        for disk in _items(disks):
            hardware["storage"].append({
                "model": disk.get("Model"), "bytes": _safe_size(disk.get("Size")),
                "interface": disk.get("InterfaceType")})
    elif host == "Linux":
        info = Path("/proc/cpuinfo")
        if info.is_file():
            raw = info.read_text(encoding="utf-8", errors="replace")
            name = re.search(r"^model name\s*:\s*(.+)$", raw, re.MULTILINE)
            vendor = re.search(r"^vendor_id\s*:\s*(.+)$", raw, re.MULTILINE)
            hardware["cpu"]["name"] = name.group(1).strip() if name else None
            hardware["cpu"]["vendor"] = vendor.group(1).strip() if vendor else None
        meminfo = Path("/proc/meminfo")
        if meminfo.is_file():
            mem = re.search(r"^MemTotal:\s+(\d+)\s+kB", meminfo.read_text(errors="replace"), re.MULTILINE)
            if mem:
                hardware["memory_bytes"] = int(mem.group(1)) * 1024
        hardware["firmware"] = "UEFI" if Path("/sys/firmware/efi").exists() else "Not detected (possibly legacy BIOS)"
        pci = _run(["lspci", "-nn"])
        for line in pci.splitlines():
            name = re.sub(r"^[0-9a-fA-F:.]+\s+", "", line.strip())
            entry = {"name": name, "pci_id": _linux_pci_id(line)}
            if re.search(r"VGA compatible controller|3D controller|Display controller", name, re.I):
                hardware["gpus"].append(entry)
            elif re.search(r"Ethernet controller|Network controller|Wireless controller", name, re.I):
                hardware["network_adapters"].append(entry)
        raw_disks = _run(["lsblk", "-J", "-b", "-d", "-o", "MODEL,SIZE,TRAN,TYPE"])
        if raw_disks:
            try:
                disks = json.loads(raw_disks)
                for item in _items(disks.get("blockdevices")):
                    if item.get("type") == "disk":
                        hardware["storage"].append({
                            "model": item.get("model"),
                            "bytes": _safe_size(item.get("size")),
                            "interface": item.get("tran")})
            except (ValueError, TypeError, AttributeError):
                pass
    elif host == "Darwin":
        hardware["cpu"]["name"] = _run(["sysctl", "-n", "machdep.cpu.brand_string"]) or None
        hardware["firmware"] = "Not assessed"
    return {"format_version": 2, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "host_os": host, "hardware": hardware, "read_only": True,
            "privacy": "No serial numbers, UUIDs, MAC addresses, PnP instance IDs, network addresses or partition contents collected"}


def inventory_gaps(report: dict) -> list[str]:
    """Return missing evidence; never convert a missing field to 'incompatible'."""
    h = report.get("hardware")
    if not isinstance(h, dict):
        return ["hardware-report"]
    gaps = []
    if not isinstance(h.get("cpu"), dict) or not h["cpu"].get("name"):
        gaps.append("exact-cpu")
    if not isinstance(h.get("motherboard"), dict) or not h["motherboard"].get("model"):
        gaps.append("motherboard-model")
    if h.get("firmware") not in ("UEFI", "Legacy BIOS"):
        gaps.append("firmware-mode")
    if not isinstance(h.get("gpus"), list) or not any(
        isinstance(g, dict) and g.get("pci_id") for g in h["gpus"]):
        gaps.append("gpu-pci-id")
    if not isinstance(h.get("storage"), list) or not h["storage"]:
        gaps.append("storage-inventory")
    if not isinstance(h.get("network_adapters"), list) or not h["network_adapters"]:
        gaps.append("network-inventory")
    return gaps


def evaluate(report: dict, catalog: dict) -> dict:
    hardware = report.get("hardware", {})
    cpu_name = (hardware.get("cpu") or {}).get("name") or ""
    match = lookup_cpu(cpu_name, catalog)
    return {"tool_version": "0.1.1-experimental", "cpu_name": cpu_name,
            "cpu_family": match["family_id"], "classification": match["classification"],
            "reason": match["reason"], "can_generate_efi": False, "boot_verified": False,
            "missing_inventory_evidence": inventory_gaps(report),
            "checks_required": ["Exact CPU/CPUID and instruction set", "GPU model and acceleration",
                                "Chipset and firmware", "ACPI/SSDT", "Storage/USB controllers",
                                "Supported macOS version", "OpenCore version and ocvalidate"],
            "next_action": "Collect full target hardware details and follow version-matched OpenCore documentation"}


def emit(value: dict, output: str | None = None) -> None:
    payload = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if output:
        Path(output).write_text(payload, encoding="utf-8")
        print(f"Saved: {output}")
    else:
        print(payload, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BlazeHackintosh read-only scanner (NOT an EFI installer)")
    sub = parser.add_subparsers(dest="operation", required=True)
    scan = sub.add_parser("scan", help="Read-only local hardware scan; JSON output")
    scan.add_argument("--output", metavar="FILE")
    catalog_cmd = sub.add_parser("catalog", help="Print research-only CPU family catalog")
    catalog_cmd.add_argument("--output", metavar="FILE")
    evaluation = sub.add_parser("evaluate", help="Classify a JSON report without guessing compatibility")
    evaluation.add_argument("--report", metavar="FILE", help="Existing report from scan; omit to scan this PC")
    evaluation.add_argument("--output", metavar="FILE")
    args = parser.parse_args(argv)
    try:
        if args.operation == "scan":
            emit(scan_hardware(), args.output)
        elif args.operation == "catalog":
            emit(load_catalog(), args.output)
        else:
            report = json.loads(Path(args.report).read_text(encoding="utf-8")) if args.report else scan_hardware()
            emit(evaluate(report, load_catalog()), args.output)
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"BlazeHackintosh: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
