#!/usr/bin/env python3
"""Fail closed if an Android build is not API 36 / Android 16."""
import argparse
import json
from pathlib import Path
from urllib.request import urlopen
from xml.etree import ElementTree as ET


def parse_props(path):
    return dict(line.split("=", 1) for line in path.read_text().splitlines()
                if "=" in line and not line.lstrip().startswith("#"))


def validate_android_version(props):
    """Validate the parsed Android build properties once."""
    if props.get("ro.build.version.release") != "16":
        raise ValueError("Android release must be exactly 16")
    if props.get("ro.build.version.sdk") != "36":
        raise ValueError("Android API level must be exactly 36")


def validate_props(path):
    validate_android_version(parse_props(path))


def validate_blazedroid_props(path):
    """Require Android 16 plus downstream system properties from the built product."""
    props = parse_props(path)
    validate_android_version(props)
    if props.get("ro.blazedroid.version") != "16.0.0":
        raise ValueError("output does not identify BlazeDroid 16.0.0")
    if props.get("ro.blazedroid.channel") != "preview":
        raise ValueError("output is not an explicitly untested BlazeDroid preview")


def validate_lock(path):
    lock = json.loads(path.read_text())
    if (lock.get("android_major"), lock.get("android_api")) != (16, 36):
        raise ValueError("foundation lock is not Android 16/API 36")
    if lock.get("android_base_tag") != "android-16.0.0_r4":
        raise ValueError("unexpected AOSP base")
    if lock.get("device_product") != "lineage_x86_64_tablet":
        raise ValueError("unexpected Android target")
    if lock.get("gapps") != "not-included":
        raise ValueError("GApps are not licensed for distribution")
    if len(lock.get("manifest_commit", "")) != 40 or len(lock.get("installer_commit", "")) != 40:
        raise ValueError("missing full pinned upstream commits")



def verify_upstream_xml(default_xml, x86_xml, lock):
    default = ET.fromstring(default_xml)
    aosp = default.find("./remote[@name='aosp']")
    if aosp is None or aosp.get("revision") != "refs/tags/" + lock["android_base_tag"]:
        raise ValueError("upstream manifest is not pinned to Android 16")
    x86 = ET.fromstring(x86_xml)
    installer = x86.find("./project[@path='bootable/aaropa']")
    if installer is None or installer.get("revision") != lock["installer_commit"]:
        raise ValueError("upstream Āropa installer commit differs from foundation lock")


def verify_upstream(lock):
    url = ("https://raw.githubusercontent.com/los-tv-x86/lineage_bass_android/"
           + lock["manifest_commit"] + "/")
    with urlopen(url + "default.xml", timeout=25) as response:
        default_xml = response.read()
    with urlopen(url + "android-x86/04-custom.xml", timeout=25) as response:
        installer_xml = response.read()
    verify_upstream_xml(default_xml, installer_xml, lock)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path)
    parser.add_argument("--build-prop", type=Path)
    parser.add_argument("--verify-upstream", action="store_true")
    parser.add_argument("--require-blazedroid", action="store_true")
    args = parser.parse_args()
    if not (args.lock or args.build_prop):
        parser.error("provide --lock and/or --build-prop")
    if args.lock:
        validate_lock(args.lock)
        if args.verify_upstream:
            verify_upstream(json.loads(args.lock.read_text()))
    if args.require_blazedroid and not args.build_prop:
        parser.error("--require-blazedroid requires --build-prop")
    if args.build_prop:
        if args.require_blazedroid:
            validate_blazedroid_props(args.build_prop)
        else:
            validate_props(args.build_prop)


if __name__ == "__main__":
    main()
