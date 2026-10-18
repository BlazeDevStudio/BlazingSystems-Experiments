#!/usr/bin/env python3
"""Read-only OpenCore EFI structural inspector.

Inspection is NOT OpenCore version-schema validation and does not verify bootability.
Does not copy, create, repair, download or execute any EFI binary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
import re
from pathlib import Path, PurePosixPath


SECTIONS = ("ACPI", "Booter", "DeviceProperties", "Kernel",
            "Misc", "NVRAM", "PlatformInfo", "UEFI")
MAX_CONFIG_BYTES = 10 * 1024 * 1024


def _safe_path(base: Path, value: str, label: str, errors: list[str]) -> Path | None:
    """Prevent absolute, parent traversal and external symlink escapes."""
    if not isinstance(value, str) or not value or "\x00" in value:
        errors.append(f"{label}: reference must be nonempty text")
        return None
    if value.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", value):
        errors.append(f"{label}: absolute path rejected")
        return None
    components = value.replace("\\", "/").split("/")
    if any(item in ("", ".", "..") for item in components):
        errors.append(f"{label}: unsafe path component rejected")
        return None
    rel = PurePosixPath(*components)
    target = base.joinpath(*rel.parts)
    # Refuse links that resolve outside the explicitly selected EFI/OC root.
    try:
        if not target.resolve().is_relative_to(base.resolve()):
            errors.append(f"{label}: path resolves outside component folder")
            return None
    except (OSError, RuntimeError):
        errors.append(f"{label}: cannot resolve path safely")
        return None
    return target


def _existing_file(base: Path, value: str, label: str, errors: list[str], checked: list[str]) -> None:
    path = _safe_path(base, value, label, errors)
    if path is None:
        return
    if not path.is_file():
        errors.append(f"{label}: referenced file not found: {value}")
    else:
        checked.append(f"{label}:{value}")


def _enabled_entries(config: dict, section: str, key: str, errors: list[str]):
    parent = config.get(section)
    if not isinstance(parent, dict):
        return []
    value = parent.get(key, [])
    if not isinstance(value, list):
        errors.append(f"{section}->{key}: expected array")
        return []
    results = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"{section}->{key}[{index}]: expected dictionary")
        elif not isinstance(item.get("Enabled"), bool):
            errors.append(f"{section}->{key}[{index}]: Enabled must be boolean")
        elif item["Enabled"]:
            results.append((index, item))
    return results


def _validate_references(oc: Path, data: dict, errors: list[str], checked: list[str]) -> None:
    references = [
        ("ACPI", "Add", "Path", "ACPI", (".aml", ".bin")),
        ("UEFI", "Drivers", "Path", "Drivers", (".efi",)),
        ("Misc", "Tools", "Path", "Tools", (".efi",)),
    ]
    for section, array, key, folder, extensions in references:
        seen = set()
        for index, item in _enabled_entries(data, section, array, errors):
            label = f"{section}->{array}[{index}]"
            value = item.get(key)
            if not isinstance(value, str) or not value.lower().endswith(extensions):
                errors.append(f"{label}: unexpected or missing {key} extension")
                continue
            norm = value.lower()
            if norm in seen:
                errors.append(f"{label}: duplicate enabled file reference")
            seen.add(norm)
            _existing_file(oc / folder, value, label, errors, checked)

    seen_kexts = set()
    for index, item in _enabled_entries(data, "Kernel", "Add", errors):
        label = f"Kernel->Add[{index}]"
        bundle_name = item.get("BundlePath")
        if not isinstance(bundle_name, str) or not bundle_name.lower().endswith(".kext"):
            errors.append(f"{label}: BundlePath must end in .kext")
            continue
        bundle = _safe_path(oc / "Kexts", bundle_name, label, errors)
        if bundle is None:
            continue
        if bundle_name.lower() in seen_kexts:
            errors.append(f"{label}: duplicate enabled bundle")
        seen_kexts.add(bundle_name.lower())
        if not bundle.is_dir():
            errors.append(f"{label}: bundle directory not found: {bundle_name}")
            continue
        checked.append(f"{label}:{bundle_name}")
        plist_path = item.get("PlistPath")
        if not isinstance(plist_path, str) or not plist_path.lower().endswith(".plist"):
            errors.append(f"{label}: PlistPath must end in .plist")
        else:
            _existing_file(bundle, plist_path, label + " plist", errors, checked)
        executable = item.get("ExecutablePath")
        if executable is None or not isinstance(executable, str):
            errors.append(f"{label}: ExecutablePath must be a string (empty for codeless kext)")
        elif executable:
            _existing_file(bundle, executable, label + " binary", errors, checked)


def _oc_directory(root: Path) -> Path:
    if root.name.lower() == "oc":
        return root
    if (root / "EFI" / "OC").is_dir():
        return root / "EFI" / "OC"
    if (root / "OC").is_dir():
        return root / "OC"
    return root / "EFI" / "OC"


def validate_efi(path: str | Path) -> dict:
    """Inspect local EFI references; never imply successful ocvalidate or boot."""
    root = Path(path).expanduser()
    oc = _oc_directory(root)
    errors: list[str] = []
    warnings: list[str] = []
    checked: list[str] = []
    config_sha256 = None

    if not oc.is_dir():
        errors.append("EFI/OC directory not found")
    else:
        _existing_file(oc, "OpenCore.efi", "OpenCore loader", errors, checked)
        if not (oc.parent / "BOOT" / "BOOTx64.efi").is_file():
            warnings.append("BOOT/BOOTx64.efi not found; USB fallback boot path not confirmed")
        config = oc / "config.plist"
        if config.is_symlink():
            errors.append("EFI/OC/config.plist is a symbolic link and is not inspected")
        elif not config.is_file():
            errors.append("EFI/OC/config.plist not found")
        elif config.stat().st_size > MAX_CONFIG_BYTES:
            errors.append("config.plist exceeds 10 MiB inspection limit")
        else:
            try:
                raw = config.read_bytes()
                config_sha256 = hashlib.sha256(raw).hexdigest()
                parsed = plistlib.loads(raw)
                if not isinstance(parsed, dict):
                    errors.append("config.plist must contain a root dictionary")
                else:
                    for key in SECTIONS:
                        if not isinstance(parsed.get(key), dict):
                            errors.append(f"config.plist missing or invalid section: {key}")
                    if not errors:
                        _validate_references(oc, parsed, errors, checked)
            except (OSError, ValueError, TypeError, OverflowError, plistlib.InvalidFileException) as exc:
                errors.append("config.plist cannot be parsed safely: " + type(exc).__name__)

    return {
        "tool_version": "0.1.3-experimental",
        "scope": "read-only file reference inspection",
        "structural_checks_passed": not errors,
        "ocvalidate_passed": False,
        "ocvalidate_required": True,
        "boot_verified": False,
        "efi_generated": False,
        "checked_references": checked,
        "config_sha256": config_sha256,
        "errors": errors,
        "warnings": warnings,
        "next_action": "Run matching official OpenCore ocvalidate and complete hardware-specific verification; do NOT consider this output proof of a bootable EFI",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="BlazeHackintosh read-only EFI structural inspector")
    parser.add_argument("--efi", required=True, help="Existing EFI root, EFI folder or OC folder to inspect")
    parser.add_argument("--output", help="Optional JSON output; no other writes are performed")
    args = parser.parse_args(argv)
    result = validate_efi(args.efi)
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if result["structural_checks_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
