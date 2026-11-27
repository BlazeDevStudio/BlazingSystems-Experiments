#!/usr/bin/env python3
"""Package a real, structurally verified upstream ISO for an explicitly untested preview.

This does not test boot, installation, or hardware compatibility.
The caller MUST run build-iso.sh first to verify Android 16 and ISO structure.
"""
import argparse
import hashlib
from pathlib import Path
import shutil

ISO_NAME = "BlazeDroid-16.0.0-x86_64-PREVIEW.iso"
# Split large owner-test artifacts into portable 1.9 GB parts for download.
MAX_ASSET_BYTES = 1_900_000_000
BUFFER_BYTES = 1024 * 1024


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(BUFFER_BYTES):
            h.update(block)
    return h.hexdigest()


def stage_iso(iso, destination, max_asset_bytes):
    """Copy an ISO or split it into bounded parts without loading it into RAM."""
    size = iso.stat().st_size
    if size <= max_asset_bytes:
        target = destination / ISO_NAME
        shutil.copyfile(iso, target)
        return [target]

    parts = []
    with iso.open("rb") as source:
        for index, offset in enumerate(range(0, size, max_asset_bytes), start=1):
            target = destination / f"{ISO_NAME}.part{index:03d}"
            remaining = min(max_asset_bytes, size - offset)
            with target.open("wb") as output:
                while remaining:
                    block = source.read(min(BUFFER_BYTES, remaining))
                    if not block:
                        raise OSError("source ISO changed during packaging")
                    output.write(block)
                    remaining -= len(block)
            parts.append(target)
    return parts


def prepare_preview(iso, destination, manifest, max_asset_bytes=MAX_ASSET_BYTES):
    iso, destination, manifest = map(Path, (iso, destination, manifest))
    if iso.name != ISO_NAME:
        raise ValueError(f"expected {ISO_NAME}, not {iso.name}")
    if not iso.is_file() or iso.stat().st_size == 0:
        raise FileNotFoundError(f"missing or empty ISO: {iso}")
    if not manifest.is_file() or manifest.stat().st_size == 0:
        raise FileNotFoundError(f"missing resolved manifest: {manifest}")
    overlay_provenance = manifest.parent / "blazedroid-overlay-SHA256SUMS"
    if not overlay_provenance.is_file() or overlay_provenance.stat().st_size == 0:
        raise FileNotFoundError(f"missing BlazeDroid product provenance: {overlay_provenance}")
    if max_asset_bytes <= 0:
        raise ValueError("asset size limit must be positive")
    if iso.parent.resolve() == destination.resolve():
        raise ValueError("release assets must be separate from build outputs")
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("refusing nonempty release directory (stale asset risk)")
    destination.mkdir(parents=True, exist_ok=True)
    assets = stage_iso(iso, destination, max_asset_bytes)
    shutil.copyfile(manifest, destination / "resolved-manifest.xml")
    shutil.copyfile(overlay_provenance, destination / "blazedroid-overlay-SHA256SUMS")
    checksums = [f"{digest(iso)}  {ISO_NAME}"]
    checksums.extend(f"{digest(asset)}  {asset.name}" for asset in assets if asset.name != ISO_NAME)
    (destination / "SHA256SUMS").write_text("\n".join(checksums) + "\n")

    if len(assets) > 1:
        names = [x.name for x in assets]
        command = "copy /b " + "+".join(f'"{name}"' for name in names) + f' "{ISO_NAME}"'
        (destination / "REASSEMBLE_WINDOWS.cmd").write_text(
            "@echo off\r\n"
            "cd /d \"%~dp0\"\r\n"
            + command + "\r\n"
            "if errorlevel 1 exit /b 1\r\n"
            f'certutil -hashfile "{ISO_NAME}" SHA256\r\n'
            "echo Compare this hash to the full-ISO entry in SHA256SUMS.\r\n"
            "pause\r\n"
        )

    notes = [
        "# BlazeDroid 16.0.0 — PREVIEW (UNTESTED)",
        "",
        "**EARLY TEST IMAGE. NO VM, INSTALLATION, DUAL-BOOT OR PHYSICAL HARDWARE ACCEPTANCE TESTS HAVE BEEN PERFORMED BY THE MAINTAINER.**",
        "",
        "This is an Android 16/API 36 x86-64 candidate built from a pinned upstream manifest.",
        "An ISO filesystem and EFI boot catalog check passed, but bootability and Windows compatibility are not proven.",
        "Google Play Store / GApps are **not included**. No Play Protect certification is claimed.",
        "",
        "## Safety and testing",
        "",
        "- Try a disposable or spare PC and backed-up **entirely expendable** disk first.",
        "- Do not select **Erase Disk** or attempt installation alongside irreplaceable Windows data.",
        "- Partitioning, bootloaders, BitLocker, Secure Boot, graphics, hardware support and recovery are untested.",
        "- Rufus/YUMI compatibility, UEFI/BIOS boot, installer launch and desktop window resizing are unverified.",
        "- Report findings and hardware details to the GitHub project; use at your own risk.",
        "",
        "## Download and integrity",
        "",
    ]
    if len(assets) > 1:
        notes.extend([
            "This large test image is split into downloadable parts. Download **every** `.partNNN` file.",
            "On Windows, put all parts in one folder and run `REASSEMBLE_WINDOWS.cmd`.",
            f"On Linux: `cat {ISO_NAME}.part* > {ISO_NAME}`.",
            "Compare the reconstructed ISO SHA-256 against `SHA256SUMS` before flashing.",
        ])
    else:
        notes.append(f"Download `{ISO_NAME}` and verify its hash using `SHA256SUMS`.")
    notes.extend([
        "",
        "`resolved-manifest.xml` records the upstream Git revisions; `blazedroid-overlay-SHA256SUMS` identifies downstream BlazeDroid source files.",
        "This is a preview release, **not** a production-ready or certified Windows alternative.",
        "",
    ])
    (destination / "PREVIEW_NOTES.md").write_text("\n".join(notes))
    return assets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--iso", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    files = prepare_preview(args.iso, args.output, args.manifest)
    print(f"PREVIEW assets prepared: {len(files)} ISO file(s)/parts; boot untested.")


if __name__ == "__main__":
    main()
