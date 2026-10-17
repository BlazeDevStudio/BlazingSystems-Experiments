import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

import blaze_lio_prepare as lio


class Backend:
    def __init__(self, fail_preflight=False, fail_prepare=False, change_image=False,
                 fail_inspect=False):
        self.fail_preflight = fail_preflight
        self.fail_prepare = fail_prepare
        self.change_image = change_image
        self.fail_inspect = fail_inspect
        self.calls = []

    def preflight(self):
        self.calls.append("preflight")
        if self.fail_preflight:
            raise lio.Refused("occupied LIO")

    def prepare(self, spec, secret):
        self.calls.append("prepare")
        if secret != "0123456789ABCDEF":
            raise AssertionError("unexpected CHAP secret")
        if self.change_image:
            image = Path(spec["image_path"])
            previous = image.stat()
            image.unlink()
            with image.open("wb") as out:
                out.truncate(previous.st_size)
            image.chmod(0o600)
            os.utime(image, ns=(previous.st_atime_ns,
                                previous.st_mtime_ns + 1_000_000_000))
        if self.fail_prepare:
            raise RuntimeError("partial configfs write")

    def inspect_prepared(self, spec, secret, expected_image=None):
        self.calls.append("inspect")
        if expected_image is None or secret != "0123456789ABCDEF":
            raise AssertionError("postwrite inspection lost the image or secret")
        if self.fail_inspect:
            raise lio.Refused("saved target differs from live target")


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        self.state = self.root / "state"
        self.state.mkdir(mode=0o700)
        self.image_dir = self.root / "images"
        self.image_dir.mkdir(mode=0o700)
        self.image = self.image_dir / "win.img"
        with self.image.open("wb") as out:
            out.truncate(16 * 1024**3)
        self.image.chmod(0o600)
        self.spec = self.root / "spec.json"
        self.data = {
            "target_iqn": "iqn.2026-10.test.example:blaze-win-01",
            "initiator_iqn": "iqn.2026-10.test.example:win-01",
            "portal_ipv4": "192.168.44.2",
            "image_path": str(self.image),
            "storage_name": "blaze_win_01",
        }
        self.save_spec()
        self.secret = self.root / "chap.txt"
        self.secret.write_text("0123456789ABCDEF\n", encoding="ascii")
        self.secret.chmod(0o600)

    def save_spec(self):
        self.spec.write_text(json.dumps(self.data), encoding="ascii")
        self.spec.chmod(0o600)

    def run_prepare(self, backend):
        return lio.prepare(self.spec, self.secret, self.state, backend, require_root=False)

    def markers(self):
        return [p for p in self.state.iterdir() if p.suffix == ".json"]

    def test_success_is_disabled_and_replay_is_refused(self):
        backend = Backend()
        self.assertEqual(self.run_prepare(backend), "PREPARED_DISABLED")
        self.assertEqual(backend.calls, ["preflight", "prepare", "inspect"])
        marker = self.markers()[0]
        self.assertEqual(json.loads(marker.read_text())["status"], "prepared_disabled")
        self.assertNotIn("0123456789ABCDEF", marker.read_text())
        with self.assertRaisesRegex(lio.Refused, "prior or incomplete"):
            self.run_prepare(Backend())

    def test_partial_write_keeps_intent_and_denies_retry(self):
        with self.assertRaisesRegex(RuntimeError, "partial"):
            self.run_prepare(Backend(fail_prepare=True))
        self.assertEqual(json.loads(self.markers()[0].read_text())["status"], "started")
        with self.assertRaisesRegex(lio.Refused, "prior or incomplete"):
            self.run_prepare(Backend())

    def test_saved_target_mismatch_keeps_uncertain_intent_and_denies_retry(self):
        backend = Backend(fail_inspect=True)
        with self.assertRaisesRegex(lio.Refused, "saved target differs"):
            self.run_prepare(backend)
        self.assertEqual(backend.calls, ["preflight", "prepare", "inspect"])
        self.assertEqual(json.loads(self.markers()[0].read_text())["status"], "started")
        with self.assertRaisesRegex(lio.Refused, "prior or incomplete"):
            self.run_prepare(Backend())

    def test_preflight_failure_does_not_create_intent(self):
        with self.assertRaises(lio.Refused):
            self.run_prepare(Backend(fail_preflight=True))
        self.assertEqual(self.markers(), [])

    def test_partial_intent_write_refuses_prepare_and_retry(self):
        backend = Backend()
        with mock.patch.object(lio.os, "write", return_value=0):
            with self.assertRaisesRegex(OSError, "short intent write"):
                self.run_prepare(backend)
        self.assertEqual(backend.calls, ["preflight"])
        self.assertEqual(len(self.markers()), 1)
        with self.assertRaisesRegex(lio.Refused, "prior or incomplete"):
            self.run_prepare(Backend())

    def test_lost_response_after_lio_write_denies_retry(self):
        real_write = lio.write_record

        def fail_completion(path, record):
            if path.name.endswith(".next"):
                raise OSError("lost completion write")
            return real_write(path, record)

        with mock.patch.object(lio, "write_record", side_effect=fail_completion):
            with self.assertRaisesRegex(OSError, "lost completion"):
                self.run_prepare(Backend())
        self.assertEqual(json.loads(self.markers()[0].read_text())["status"], "started")
        with self.assertRaises(lio.Refused):
            self.run_prepare(Backend())

    def test_image_replacement_after_preflight_is_refused(self):
        with self.assertRaisesRegex(lio.Refused, "image changed"):
            self.run_prepare(Backend(change_image=True))
        self.assertEqual(json.loads(self.markers()[0].read_text())["status"], "started")

    def test_rejects_untrusted_spec_and_secret_before_backend(self):
        for field, value in (("portal_ipv4", "0.0.0.0"),
                             ("portal_ipv4", "8.8.8.8"),
                             ("storage_name", "other"),
                             ("initiator_iqn", self.data["target_iqn"])):
            original = self.data[field]
            self.data[field] = value
            self.save_spec()
            with self.assertRaises(lio.Refused):
                self.run_prepare(Backend())
            self.data[field] = original
        self.save_spec()
        self.secret.write_text("short\n", encoding="ascii")
        with self.assertRaises(lio.Refused):
            self.run_prepare(Backend())
        self.assertEqual(self.markers(), [])

    def test_rejects_corrupt_existing_intent_without_mutation(self):
        marker = self.state / ("f" * 64 + ".json")
        marker.write_text("{", encoding="ascii")
        target_marker = self.state / (lio.hashlib.sha256(self.data["target_iqn"].encode()).hexdigest() + ".json")
        target_marker.write_text("{", encoding="ascii")
        with self.assertRaises(lio.Refused):
            self.run_prepare(Backend())
        self.assertEqual(target_marker.read_text(), "{")

    def test_real_adapter_orders_disabled_acl_chap_map_portal_save(self):
        operations = []
        save_path = self.root / "lio-save.json"

        class FakeRoot:
            targets = ()
            storage_objects = ()
            sessions = ()

            def save_to_file(self, path):
                operations.append("save")
                path.write_text("{}")
                path.chmod(0o600)

        class FakeStorage:
            def __init__(self, name, dev, size, write_back):
                self.udev_path = dev
                self.name = name
                self.size = size
                self.write_back = write_back
                operations.append("storage")

        class FakeTPG:
            def __init__(self, target, tag, mode):
                self._enabled = True
                self.attrs = {}
                self.node_acls = []
                self.luns = []
                self.network_portals = []
                operations.append("tpg")

            @property
            def enable(self):
                return self._enabled

            @enable.setter
            def enable(self, enabled):
                self._enabled = enabled
                operations.append("disable" if not enabled else "enable")

            def set_attribute(self, name, value):
                self.attrs[name] = value
                operations.append(name + "=" + value)

            def get_attribute(self, name):
                return self.attrs[name]

        class FakeLUN:
            def __init__(self, tpg, lun, storage_object):
                self.lun = lun
                tpg.luns.append(self)
                operations.append("lun")

        class FakeACL:
            def __init__(self, tpg, initiator, mode):
                self.chap_userid = None
                self.chap_password = None
                self.mapped_luns = []
                tpg.node_acls.append(self)
                operations.append("acl")

        class FakeMap:
            def __init__(self, acl, mapped_lun, tpg_lun, write_protect):
                self.write_protect = write_protect
                acl.mapped_luns.append(self)
                self.assertion = (acl.chap_userid is not None and
                                  acl.chap_password == "0123456789ABCDEF")
                if not self.assertion:
                    raise AssertionError("mapping preceded CHAP")
                operations.append("map")

        class FakePortal:
            def __init__(self, tpg, address, port, mode):
                if tpg.enable or tpg.attrs.get("authentication") != "1":
                    raise AssertionError("portal created before disabling or auth")
                tpg.network_portals.append(self)
                operations.append("portal")

        fake = types.SimpleNamespace(
            FabricModule=lambda kind: kind,
            FileIOStorageObject=FakeStorage,
            LUN=FakeLUN,
            MappedLUN=FakeMap,
            NetworkPortal=FakePortal,
            NodeACL=FakeACL,
            RTSRoot=FakeRoot,
            TPG=FakeTPG,
            Target=lambda fabric, iqn, mode: iqn,
        )
        with mock.patch.dict(sys.modules, {"rtslib": fake}):
            backend = lio.LioBackend(save_path)
            backend.preflight()
            backend.prepare(self.data, "0123456789ABCDEF")
        self.assertEqual(operations, ["storage", "tpg", "disable",
                                      "generate_node_acls=0", "cache_dynamic_acls=0",
                                      "authentication=1", "demo_mode_write_protect=1",
                                      "lun", "acl", "map", "portal", "save"])
        self.assertEqual(save_path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
