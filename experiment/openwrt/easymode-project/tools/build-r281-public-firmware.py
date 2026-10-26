#!/usr/bin/env python3
"""Build a credential-free R281 sysupgrade candidate from a pinned clean base.

This assembles an unsigned OpenWrt sysupgrade tar. Append fwtool metadata
before offering the image to sysupgrade. It never flashes a device.
"""
import argparse
import copy
import datetime
import gzip
import hashlib
import io
import json
import pathlib
import stat
import subprocess
import sys
import tarfile

PROJECT = pathlib.Path(__file__).resolve().parents[1]
APP = PROJECT / "releases/v10.2.0-r281-candidate/root"
TRAFFIC = PROJECT / "traffic/root"
BASE_SHA256 = "dc39c985658dc959238c02cf09dba947b4c32e205165a0e4a4a138b4f9d66790"
ROOT_TAR_SHA256 = "2f772c623ff3b056e09eb228a455afbd da4e5446102949c30b18dda0c108b143".replace(" ", "")
KERNEL_SHA256 = "24c963f1af83756de4943a195ac95c4a4b7285c0097fbc985e8e00347f2e1973"
EPOCH = int(datetime.datetime(2026, 10, 26, 9, tzinfo=datetime.timezone.utc).timestamp())
BUILD = "2026.10.26-easymode-v10.2-public"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read_tar(path):
    result = {}
    with tarfile.open(path, "r:*") as archive:
        for member in archive:
            name = member.name.removeprefix("./").rstrip("/") or "."
            if name.startswith("/") or ".." in pathlib.PurePosixPath(name).parts:
                raise ValueError("unsafe root path: " + name)
            result[name] = (copy.copy(member), archive.extractfile(member).read() if member.isfile() else None)
    return result

def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--base-sysupgrade", type=pathlib.Path)
    source.add_argument("--base-kernel", type=pathlib.Path)
    parser.add_argument("--clean-root-tar", required=True, type=pathlib.Path)
    parser.add_argument("--mksquashfs", required=True)
    parser.add_argument("--output-dir", required=True, type=pathlib.Path)
    parser.add_argument("--dissect-path", type=pathlib.Path)
    parser.add_argument("--verify-squashfs", action="store_true")
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    base_hash = None
    if args.base_sysupgrade:
        base = args.base_sysupgrade.read_bytes()
        base_hash = digest(base)
        if base_hash != BASE_SHA256:
            raise ValueError("R281 base image hash mismatch")
        with tarfile.open(fileobj=io.BytesIO(base)) as source:
            kernel = source.extractfile("sysupgrade-notion_r281/kernel").read()
    else:
        kernel = args.base_kernel.read_bytes()
    root_tar_bytes = gzip.decompress(args.clean_root_tar.read_bytes()) if args.clean_root_tar.suffix == ".gz" else args.clean_root_tar.read_bytes()
    if digest(root_tar_bytes) != ROOT_TAR_SHA256:
        raise ValueError("clean root tar hash mismatch")
    if digest(kernel) != KERNEL_SHA256:
        raise ValueError("R281 kernel hash mismatch")
    entries = read_tar(args.clean_root_tar)

    def add_parent(path):
        for parent in reversed(pathlib.PurePosixPath(path).parents):
            name = str(parent)
            if name == "." or name in entries:
                continue
            item = tarfile.TarInfo(name)
            item.type = tarfile.DIRTYPE
            item.mode = 0o755
            item.mtime = EPOCH
            entries[name] = (item, None)

    def add_file(name, data, mode=0o644):
        add_parent(name)
        item = tarfile.TarInfo(name)
        item.mode = mode
        item.size = len(data)
        item.mtime = EPOCH
        entries[name] = (item, data)

    def add_link(name, target):
        add_parent(name)
        item = tarfile.TarInfo(name)
        item.type = tarfile.SYMTYPE
        item.linkname = target
        item.mode = 0o777
        item.mtime = EPOCH
        entries[name] = (item, None)

    manifest = json.loads((PROJECT / "releases/v10.2.0-r281-candidate/SOURCE-MANIFEST.json").read_text())
    app_modes = {record["path"].removeprefix("root/"): int(record["mode"], 8) for record in manifest["files"]}
    for source, root in ((APP, APP), (TRAFFIC, TRAFFIC)):
        for path in source.rglob("*"):
            if not path.is_file():
                continue
            name = path.relative_to(root).as_posix()
            if (name.startswith("etc/config/") and name != "etc/config/easymode_traffic") or name.startswith("etc/dropbear/"):
                raise ValueError("source contains device settings: " + name)
            mode = app_modes[name] if source == APP else (0o755 if any(marker in "/" + name for marker in ("/init.d/", "/libexec/", "/uci-defaults/")) or name.endswith(".sh") else 0o644)
            add_file(name, path.read_bytes(), mode)
    add_file("etc/blaze-release", f"BLAZE_BUILD_ID={BUILD}\nBLAZE_BASE=OpenWrt-24.10.8\nBLAZE_DEVICE=notion,r281\nEASYMODE=10.2.0\nTRAFFIC_INTELLIGENCE=7.0.2\n".encode())
    add_file("etc/uci-defaults/99-easymode-restore", b"""#!/bin/sh
[ "$(cat /tmp/sysinfo/board_name 2>/dev/null)" = notion,r281 ] || exit 0
. /etc/openwrt_release
[ "$DISTRIB_RELEASE" = 24.10.8 ] || exit 0
if ! uci -q get blaze.main >/dev/null 2>&1; then
 uci set blaze.main=main
 uci set blaze.main.watchdog_enabled=0
 uci set blaze.main.watchdog_reboot_enabled=0
 uci commit blaze
fi
if ! uci -q get easymode_traffic.main >/dev/null 2>&1; then
 uci set easymode_traffic.main=main
 uci set easymode_traffic.main.edition=cellular
 uci set easymode_traffic.main.enabled=1
 uci set easymode_traffic.main.devices=1
 uci set easymode_traffic.main.domains=0
 uci commit easymode_traffic
fi
for service in blaze-access blaze-health blaze-quality blaze-sites blaze-sms-archive easymode-traffic; do
 [ ! -x "/etc/init.d/$service" ] || "/etc/init.d/$service" enable
done
exit 0
""", 0o755)
    for name, target in (
        ("etc/rc.d/S95easymode-traffic", "../init.d/easymode-traffic"),
        ("etc/rc.d/S96blaze-access", "../init.d/blaze-access"),
        ("etc/rc.d/S97blaze-health", "../init.d/blaze-health"),
        ("etc/rc.d/S97blaze-quality", "../init.d/blaze-quality"),
        ("etc/rc.d/S97blaze-sites", "../init.d/blaze-sites"),
        ("etc/rc.d/S97blaze-sms-archive", "../init.d/blaze-sms-archive"),
    ):
        add_link(name, target)
    key_markers = (b"-----BEGIN OPENSSH PRIVATE KEY-----", b"-----BEGIN EC PRIVATE KEY-----", b"-----BEGIN RSA PRIVATE KEY-----")
    for name, (_, data) in entries.items():
        if data and b"\0" not in data[:4096] and any(token in data for token in key_markers):
            raise ValueError("private content detected in " + name)
    if entries["etc/shadow"][1].splitlines()[0] != b"root:::0:99999:7:::":
        raise ValueError("base image root identity differs from clean public baseline")
    if any(name.startswith("etc/dropbear/dropbear_") for name in entries):
        raise ValueError("base image contains SSH host identities")
    if "etc/uhttpd.key" in entries:
        raise ValueError("base image contains TLS identity")

    root_tar = out / "root-input.tar"
    expected = {}
    with tarfile.open(root_tar, "w", format=tarfile.GNU_FORMAT) as archive:
        for name, (item, data) in sorted(entries.items()):
            item.name = name
            item.mtime = EPOCH
            item.uid = item.gid = 0
            if data is not None:
                item.size = len(data)
            archive.addfile(item, io.BytesIO(data) if item.isfile() else None)
            expected[name] = {"type": item.type.decode(), "mode": item.mode, "sha256": digest(data) if data is not None else None, "link": item.linkname}
    # MSYS mksquashfs expects a different encoded major in tar input.
    tar_input = root_tar
    if sys.platform == "win32":
        tar_input = out / "root-msys-input.tar"
        with tarfile.open(root_tar) as src, tarfile.open(tar_input, "w", format=tarfile.GNU_FORMAT) as dst:
            for item in src:
                copy_item = copy.copy(item)
                if copy_item.isdev():
                    if copy_item.name != "dev/console" or (copy_item.devmajor, copy_item.devminor) != (5, 1):
                        raise ValueError("unexpected device node")
                    copy_item.devmajor = 1280
                dst.addfile(copy_item, src.extractfile(item) if item.isfile() else None)
    squash = out / "root.squashfs"
    command = [args.mksquashfs, "-", str(squash), "-tar", "-noappend", "-nopad", "-numeric-owner", "-default-mode", "0755", "-default-uid", "0", "-default-gid", "0", "-comp", "xz", "-b", "262144", "-no-xattrs", "-mkfs-time", str(EPOCH), "-all-time", str(EPOCH), "-processors", "2", "-no-progress"]
    with tar_input.open("rb") as stream:
        process = subprocess.run(command, stdin=stream, capture_output=True)
    (out / "mksquashfs.log").write_bytes(process.stdout + process.stderr)
    if process.returncode:
        raise RuntimeError("mksquashfs failed: " + process.stderr.decode(errors="replace")[-1200:])
    if args.verify_squashfs or args.dissect_path:
        if args.dissect_path:
            sys.path.insert(0, str(args.dissect_path))
        from dissect.squashfs import SquashFS
        with squash.open("rb") as stream:
            fs = SquashFS(stream)
            seen = {}
            def walk(node, name):
                seen[name] = node
                if node.is_dir():
                    for child in node.iterdir():
                        walk(child, child.name if name == "." else name + "/" + child.name)
            walk(fs.root, ".")
            if set(seen) != set(expected):
                raise ValueError("SquashFS path mismatch")
            for name, record in expected.items():
                node = seen[name]
                if stat.S_IMODE(node.mode) != record["mode"]:
                    raise ValueError("SquashFS mode mismatch " + name)
                if record["type"] == "0" and (not node.is_file() or digest(node.open().read()) != record["sha256"]):
                    raise ValueError("SquashFS content mismatch " + name)
                if record["type"] == "2" and (not node.is_symlink() or node.link != record["link"]):
                    raise ValueError("SquashFS link mismatch " + name)
    metadata = {
        "metadata_version": "1.1",
        "compat_version": "1.1",
        "compat_message": "Config cannot be migrated from swconfig to DSA",
        "new_supported_devices": ["notion,r281"],
        "supported_devices": ["notion,r281 - Image version mismatch: image 1.1, device 1.0. Please wipe config during upgrade (force required) or reinstall. Reason: Config cannot be migrated from swconfig to DSA"],
        "version": {"dist": "OpenWrt", "version": "24.10.8", "revision": "r29233-443ec4032a", "target": "ramips/mt7621", "board": "notion_r281"},
        "blaze_build": BUILD,
    }
    (out / "metadata.json").write_text(json.dumps(metadata, separators=(",", ":")), encoding="utf-8")
    image = out / "R281-EasyMode-v10.2.0-public-unsigned.bin"
    with tarfile.open(image, "w", format=tarfile.GNU_FORMAT) as archive:
        folder = tarfile.TarInfo("sysupgrade-notion_r281")
        folder.type = tarfile.DIRTYPE
        folder.mode = 0o755
        archive.addfile(folder)
        for name, data in (("CONTROL", b"BOARD=notion_r281\n"), ("kernel", kernel), ("root", squash.read_bytes() + b"\0" * ((-squash.stat().st_size) % 1024))):
            item = tarfile.TarInfo("sysupgrade-notion_r281/" + name)
            item.mode = 0o644
            item.size = len(data)
            archive.addfile(item, io.BytesIO(data))
    result = {"base_sha256": base_hash, "kernel_sha256": digest(kernel), "clean_root_tar_sha256": digest(root_tar_bytes), "root_entries": len(entries), "root_sha256": digest(squash.read_bytes()), "unsigned_sha256": digest(image.read_bytes()), "private_settings": False}
    (out / "build-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
