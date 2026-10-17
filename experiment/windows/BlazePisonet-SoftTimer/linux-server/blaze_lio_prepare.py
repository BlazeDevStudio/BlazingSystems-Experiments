#!/usr/bin/env python3
"""Prepare one disabled, CHAP guarded LIO disk on a dedicated Linux host.

This command never enables the target. A prepared target needs separate live
authentication, isolation, persistence and Windows boot acceptance before use.
"""

import argparse
import fcntl
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import stat
import sys


class Refused(Exception):
    pass


IQN = re.compile(r"iqn\.[0-9]{4}-[0-9]{2}\.[a-z0-9.-]+:[a-z0-9._:-]{1,80}\Z")
NAME = re.compile(r"blaze_[a-z0-9_]{1,40}\Z")
FIELDS = {"target_iqn", "initiator_iqn", "portal_ipv4", "image_path", "storage_name"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Refused("duplicate JSON field")
        result[key] = value
    return result


def private_regular(path, owner, mode=0o600):
    s = path.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1 or s.st_uid != owner or stat.S_IMODE(s.st_mode) != mode:
        raise Refused("file is not a single-link private regular file")
    return s


def private_directory(path, owner):
    s = path.lstat()
    if not stat.S_ISDIR(s.st_mode) or s.st_uid != owner or stat.S_IMODE(s.st_mode) != 0o700:
        raise Refused("directory is not private")


def image_identity(file_stat):
    return (file_stat.st_dev, file_stat.st_ino, file_stat.st_size,
            file_stat.st_ctime_ns, file_stat.st_mtime_ns)


def read_spec(path, owner):
    private_directory(path.parent, owner)
    private_regular(path, owner)
    raw = path.read_bytes()
    if len(raw) > 4096:
        raise Refused("spec too large")
    try:
        spec = json.loads(raw, object_pairs_hook=unique_object)
    except (UnicodeError, ValueError) as error:
        raise Refused("invalid spec") from error
    if not isinstance(spec, dict) or set(spec) != FIELDS or any(not isinstance(v, str) for v in spec.values()):
        raise Refused("incomplete or unexpected spec fields")
    if not IQN.fullmatch(spec["target_iqn"]) or not IQN.fullmatch(spec["initiator_iqn"]):
        raise Refused("invalid iSCSI identity")
    if spec["target_iqn"] == spec["initiator_iqn"] or not NAME.fullmatch(spec["storage_name"]):
        raise Refused("ambiguous target or storage identity")
    try:
        ip = ipaddress.IPv4Address(spec["portal_ipv4"])
    except ipaddress.AddressValueError as error:
        raise Refused("invalid portal") from error
    if not ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified:
        raise Refused("portal must be a dedicated private IPv4 address")
    image = Path(spec["image_path"])
    if not image.is_absolute() or image == Path("/") or image.parent == Path("/"):
        raise Refused("image path must be absolute and within a private directory")
    private_directory(image.parent, owner)
    file_stat = private_regular(image, owner)
    if file_stat.st_size < 16 * 1024**3 or file_stat.st_size % 4096:
        raise Refused("Windows image size must be at least 16 GiB and block aligned")
    return spec, file_stat


def read_secret(path, owner):
    private_directory(path.parent, owner)
    private_regular(path, owner)
    value = path.read_bytes()
    if len(value) != 17 or value[-1:] != b"\n" or any(c < 33 or c > 126 for c in value[:-1]):
        raise Refused("CHAP secret must be 16 printable ASCII bytes plus newline")
    return value[:-1].decode("ascii")


def write_record(path, record):
    data = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        position = 0
        while position < len(data):
            written = os.write(fd, data[position:])
            if written <= 0:
                raise OSError("short intent write")
            position += written
        os.fsync(fd)
    finally:
        os.close(fd)
    dfd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


class LioBackend:
    def __init__(self, save_path):
        self.save_path = save_path
        self.api = None

    def load_api(self):
        if self.api is not None:
            return
        from rtslib import FabricModule, FileIOStorageObject, LUN, MappedLUN
        from rtslib import NetworkPortal, NodeACL, RTSRoot, TPG, Target
        self.api = (FabricModule, FileIOStorageObject, LUN, MappedLUN,
                    NetworkPortal, NodeACL, RTSRoot, TPG, Target)

    def preflight(self):
        # Import only after all filesystem/identity admission checks. The
        # library itself requires Linux configfs and does not run on Windows.
        self.load_api()
        RTSRoot = self.api[6]
        root = RTSRoot()
        if list(root.targets) or list(root.storage_objects) or list(root.sessions):
            raise Refused("LIO host already has targets, storage or sessions")
        if self.save_path.exists() or self.save_path.is_symlink():
            raise Refused("persistent LIO configuration already exists")

    def prepare(self, spec, secret):
        (FabricModule, FileIOStorageObject, LUN, MappedLUN,
         NetworkPortal, NodeACL, RTSRoot, TPG, Target) = self.api
        image = spec["image_path"]
        size = os.stat(image, follow_symlinks=False).st_size
        so = FileIOStorageObject(spec["storage_name"], dev=image,
                                 size=size, write_back=False)
        target = Target(FabricModule("iscsi"), spec["target_iqn"], mode="create")
        tpg = TPG(target, tag=1, mode="create")
        # No portal exists until after this assignment. Any later exception
        # leaves a disabled TPG and an indeterminate intent record.
        tpg.enable = False
        if tpg.enable:
            raise Refused("target did not disable")
        tpg.set_attribute("generate_node_acls", "0")
        tpg.set_attribute("cache_dynamic_acls", "0")
        tpg.set_attribute("authentication", "1")
        tpg.set_attribute("demo_mode_write_protect", "1")
        lun = LUN(tpg, lun=0, storage_object=so)
        acl = NodeACL(tpg, spec["initiator_iqn"], mode="create")
        acl.chap_userid = spec["initiator_iqn"]
        acl.chap_password = secret
        MappedLUN(acl, mapped_lun=0, tpg_lun=lun, write_protect=False)
        NetworkPortal(tpg, spec["portal_ipv4"], port=3260, mode="create")
        if (tpg.enable or tpg.get_attribute("generate_node_acls").strip() != "0" or
                tpg.get_attribute("authentication").strip() != "1" or
                len(list(tpg.node_acls)) != 1 or
                len(list(acl.mapped_luns)) != 1 or
                len(list(tpg.luns)) != 1 or
                len(list(tpg.network_portals)) != 1 or
                Path(so.udev_path) != Path(image)):
            raise Refused("prepared LIO state does not match the requested identity")
        RTSRoot().save_to_file(self.save_path)
        private_regular(self.save_path, os.geteuid())
        dfd = os.open(self.save_path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)

    def inspect_prepared(self, spec, secret, expected_image=None):
        self.load_api()
        image_stat = private_regular(Path(spec["image_path"]), os.geteuid())
        if expected_image is not None and image_identity(image_stat) != image_identity(expected_image):
            raise Refused("backing image changed since preparation")
        root = self.api[6]()
        targets = list(root.targets)
        stores = list(root.storage_objects)
        if len(targets) != 1 or len(stores) != 1 or list(root.sessions):
            raise Refused("LIO target/storage/session count changed")
        target, store = targets[0], stores[0]
        if target.wwn != spec["target_iqn"] or target.fabric_module.name != "iscsi":
            raise Refused("target identity changed")
        if (store.plugin != "fileio" or store.name != spec["storage_name"] or
                store.udev_path != spec["image_path"] or store.write_back or
                store.is_block or store.size != image_stat.st_size):
            raise Refused("backing image identity or write-through mode changed")
        tpgs = list(target.tpgs)
        if len(tpgs) != 1 or tpgs[0].tag != 1 or tpgs[0].enable:
            raise Refused("target portal group is not uniquely disabled")
        tpg = tpgs[0]
        expected_attributes = {"generate_node_acls": "0", "cache_dynamic_acls": "0",
                               "authentication": "1", "demo_mode_write_protect": "1"}
        if any(tpg.get_attribute(key).strip() != value for key, value in expected_attributes.items()):
            raise Refused("ACL or CHAP policy changed")
        luns = list(tpg.luns)
        acls = list(tpg.node_acls)
        portals = list(tpg.network_portals)
        if len(luns) != 1 or luns[0].lun != 0 or luns[0].storage_object.path != store.path:
            raise Refused("target LUN mapping changed")
        if len(acls) != 1 or acls[0].node_wwn != spec["initiator_iqn"]:
            raise Refused("initiator ACL changed")
        acl = acls[0]
        if acl.chap_userid != spec["initiator_iqn"] or acl.chap_password != secret:
            raise Refused("initiator CHAP identity changed")
        mapped = list(acl.mapped_luns)
        if (len(mapped) != 1 or mapped[0].mapped_lun != 0 or
                mapped[0].tpg_lun.lun != 0 or mapped[0].write_protect):
            raise Refused("initiator LUN access changed")
        if (len(portals) != 1 or portals[0].ip_address != spec["portal_ipv4"] or
                portals[0].port != 3260):
            raise Refused("network portal changed")
        private_regular(self.save_path, os.geteuid())
        if self.save_path.stat().st_size > 1024 * 1024:
            raise Refused("saved LIO configuration too large")
        try:
            saved = json.loads(self.save_path.read_bytes(), object_pairs_hook=unique_object)
            # save_to_file serializes RTSRoot.dump(). Compare the entire saved
            # restore state, including storage, portals, ACLs and CHAP. A
            # disabled flag alone cannot make a reboot safe.
            if saved != root.dump():
                raise Refused("saved LIO configuration differs from live target")
        except (KeyError, TypeError, ValueError, UnicodeError) as error:
            raise Refused("saved LIO configuration malformed") from error
        return root, tpg

    def activate(self, spec, secret, expected_image):
        root, tpg = self.inspect_prepared(spec, secret, expected_image)
        tpg.enable = True
        if not tpg.enable:
            raise Refused("target enable did not take effect")
        root.save_to_file(self.save_path)
        private_regular(self.save_path, os.geteuid())
        saved = json.loads(self.save_path.read_bytes(), object_pairs_hook=unique_object)
        if saved != root.dump():
            raise Refused("enabled LIO configuration was not persisted")
        dfd = os.open(self.save_path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)

    def quarantine(self, spec):
        self.load_api()
        root = self.api[6]()
        targets = list(root.targets)
        if len(targets) != 1 or targets[0].wwn != spec["target_iqn"]:
            raise Refused("cannot identify target for quarantine")
        tpgs = list(targets[0].tpgs)
        if len(tpgs) != 1 or tpgs[0].tag != 1:
            raise Refused("cannot identify TPG for quarantine")
        tpgs[0].enable = False
        if tpgs[0].enable:
            raise Refused("quarantine disable did not take effect")
        root.save_to_file(self.save_path)
        private_regular(self.save_path, os.geteuid())
        dfd = os.open(self.save_path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)


def prepare(spec_path, secret_path, state_dir, backend, *, require_root=True):
    if require_root and (sys.platform != "linux" or os.geteuid() != 0):
        raise Refused("Linux root is required")
    owner = os.geteuid()
    private_directory(state_dir, owner)
    spec, before = read_spec(spec_path, owner)
    secret = read_secret(secret_path, owner)
    key = hashlib.sha256(spec["target_iqn"].encode("ascii")).hexdigest()
    marker = state_dir / (key + ".json")
    lockfd = os.open(state_dir / ".lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        lock_stat = os.fstat(lockfd)
        if (not stat.S_ISREG(lock_stat.st_mode) or lock_stat.st_nlink != 1 or
                lock_stat.st_uid != owner or stat.S_IMODE(lock_stat.st_mode) != 0o600):
            raise Refused("unsafe preparation lock")
        fcntl.flock(lockfd, fcntl.LOCK_EX)
        if marker.exists() or marker.is_symlink():
            raise Refused("prior or incomplete preparation; inspect before retry")
        backend.preflight()
        after = private_regular(Path(spec["image_path"]), owner)
        if image_identity(before) != image_identity(after):
            raise Refused("image changed during preflight")
        record = {"status": "started", "target_iqn": spec["target_iqn"],
                  "initiator_iqn": spec["initiator_iqn"], "image_path": spec["image_path"],
                  "image_dev": before.st_dev, "image_ino": before.st_ino,
                  "image_size": before.st_size, "image_ctime_ns": before.st_ctime_ns,
                  "image_mtime_ns": before.st_mtime_ns}
        write_record(marker, record)
        backend.prepare(spec, secret)
        after = private_regular(Path(spec["image_path"]), owner)
        if image_identity(before) != image_identity(after):
            raise Refused("image changed during LIO preparation")
        # A successful configfs write is not proof that the persisted restore
        # state matches it. Keep the durable intent uncertain until both agree.
        backend.inspect_prepared(spec, secret, before)
        record["status"] = "prepared_disabled"
        replacement = state_dir / ("." + key + ".next")
        write_record(replacement, record)
        os.replace(replacement, marker)
        dfd = os.open(state_dir, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        os.close(lockfd)
    return "PREPARED_DISABLED"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--secret-file", required=True, type=Path)
    parser.add_argument("--state-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = prepare(args.spec, args.secret_file, args.state_dir,
                         LioBackend(Path("/etc/target/saveconfig.json")))
    except Exception as error:
        # Never print an exception: some library errors may include secrets.
        print("LIO preparation refused or uncertain; inspect disabled target and intent", file=sys.stderr)
        return 8
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
