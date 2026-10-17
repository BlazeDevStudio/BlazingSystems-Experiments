import hashlib
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

import blaze_lio_activate as activation
import blaze_lio_prepare as preparation


class Backend:
    def __init__(self, fail_inspect=False, fail_activate=False):
        self.fail_inspect = fail_inspect
        self.fail_activate = fail_activate
        self.calls = []

    def preflight(self):
        self.calls.append("preflight")

    def prepare(self, spec, secret):
        self.calls.append("prepare")

    def inspect_prepared(self, spec, secret, expected_image=None):
        self.calls.append("inspect")
        if self.fail_inspect:
            raise preparation.Refused("live ACL drift")

    def activate(self, spec, secret, expected_image=None):
        self.calls.append("activate")
        if self.fail_activate:
            raise RuntimeError("lost configfs completion")

    def quarantine(self, spec):
        self.calls.append("quarantine")


class ActivationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        self.state = self.root / "state"
        self.state.mkdir(mode=0o700)
        self.images = self.root / "images"
        self.images.mkdir(mode=0o700)
        self.image = self.images / "windows.img"
        with self.image.open("wb") as out:
            out.truncate(16 * 1024**3)
        self.image.chmod(0o600)
        self.data = {"target_iqn": "iqn.2026-10.example.test:target-01",
                     "initiator_iqn": "iqn.2026-10.example.test:client-01",
                     "portal_ipv4": "192.168.77.2",
                     "image_path": str(self.image),
                     "storage_name": "blaze_client_01"}
        self.spec = self.root / "spec.json"
        self.spec.write_text(json.dumps(self.data))
        self.spec.chmod(0o600)
        self.secret = self.root / "chap.txt"
        self.secret.write_text("0123456789ABCDEF\n")
        self.secret.chmod(0o600)
        self.marker = self.state / (hashlib.sha256(self.data["target_iqn"].encode()).hexdigest() + ".json")
        self.backend = Backend()
        preparation.prepare(self.spec, self.secret, self.state, self.backend,
                            require_root=False)

    def run_activation(self, backend=None):
        return activation.activate(self.spec, self.secret, self.state,
                                   backend or self.backend, require_root=False)

    def test_activation_commits_intent_and_refuses_replay(self):
        self.assertEqual(self.run_activation(), "ACTIVE_LAB_TARGET")
        self.assertEqual(json.loads(self.marker.read_text())["status"], "active")
        self.assertEqual(self.backend.calls[-2:], ["inspect", "activate"])
        with self.assertRaisesRegex(preparation.Refused, "intent or image"):
            self.run_activation()

    def test_changed_image_refused_before_live_inspection(self):
        previous = self.image.stat()
        self.image.unlink()
        with self.image.open("wb") as out:
            out.truncate(previous.st_size)
        self.image.chmod(0o600)
        os.utime(self.image, ns=(previous.st_atime_ns,
                                 previous.st_mtime_ns + 1_000_000_000))
        with self.assertRaisesRegex(preparation.Refused, "image identity"):
            self.run_activation()
        self.assertEqual(json.loads(self.marker.read_text())["status"], "prepared_disabled")
        self.assertEqual(self.backend.calls, ["preflight", "prepare", "inspect"])

    def test_corrupt_intent_refused_without_backend_call(self):
        self.marker.write_text("{bad")
        self.marker.chmod(0o600)
        with self.assertRaisesRegex(preparation.Refused, "malformed"):
            self.run_activation()
        self.assertEqual(self.backend.calls, ["preflight", "prepare", "inspect"])

    def test_acl_or_chap_inspection_failure_does_not_start(self):
        backend = Backend(fail_inspect=True)
        with self.assertRaisesRegex(preparation.Refused, "ACL drift"):
            self.run_activation(backend)
        self.assertEqual(json.loads(self.marker.read_text())["status"], "prepared_disabled")
        self.assertEqual(backend.calls, ["inspect"])

    def test_partial_configfs_activation_is_quarantined_and_not_retried(self):
        backend = Backend(fail_activate=True)
        with self.assertRaisesRegex(RuntimeError, "lost configfs"):
            self.run_activation(backend)
        self.assertEqual(json.loads(self.marker.read_text())["status"], "activating")
        self.assertEqual(backend.calls, ["inspect", "activate", "quarantine"])
        with self.assertRaises(preparation.Refused):
            self.run_activation(Backend())

    def test_lost_success_record_quarantines_live_target(self):
        real_replace = activation.replace_record

        def fail_success(marker, record):
            if record["status"] == "active":
                raise OSError("lost activation result")
            real_replace(marker, record)

        with mock.patch.object(activation, "replace_record", side_effect=fail_success):
            with self.assertRaisesRegex(OSError, "lost activation"):
                self.run_activation()
        self.assertEqual(json.loads(self.marker.read_text())["status"], "activating")
        self.assertEqual(self.backend.calls[-3:], ["inspect", "activate", "quarantine"])
        with self.assertRaises(preparation.Refused):
            self.run_activation()

    def test_lio_adapter_rejects_acl_chap_storage_portal_and_session_drift(self):
        image_stat = self.image.stat()
        store = types.SimpleNamespace(plugin="fileio", name=self.data["storage_name"],
                                      udev_path=str(self.image), write_back=False,
                                      is_block=False, size=image_stat.st_size,
                                      path="/sys/kernel/config/target/core/fileio_0/blaze_client_01")
        lun = types.SimpleNamespace(lun=0, storage_object=store)
        mapped = types.SimpleNamespace(mapped_lun=0, tpg_lun=lun, write_protect=False)
        acl = types.SimpleNamespace(node_wwn=self.data["initiator_iqn"],
                                    chap_userid=self.data["initiator_iqn"],
                                    chap_password="0123456789ABCDEF", mapped_luns=[mapped])
        portal = types.SimpleNamespace(ip_address=self.data["portal_ipv4"], port=3260)

        class TPG:
            tag = 1
            enable = False
            luns = [lun]
            node_acls = [acl]
            network_portals = [portal]
            attributes = {"generate_node_acls": "0", "cache_dynamic_acls": "0",
                          "authentication": "1", "demo_mode_write_protect": "1"}

            def get_attribute(self, key):
                return self.attributes[key]

        tpg = TPG()
        target = types.SimpleNamespace(wwn=self.data["target_iqn"],
                                       fabric_module=types.SimpleNamespace(name="iscsi"),
                                       tpgs=[tpg])

        class Root:
            targets = [target]
            storage_objects = [store]
            sessions = []

            def dump(self):
                return {"storage_objects": [{"plugin": store.plugin,
                                             "name": store.name,
                                             "dev": store.udev_path,
                                             "write_back": store.write_back}],
                        "targets": [{"wwn": target.wwn,
                                     "tpgs": [{"enable": tpg.enable,
                                               "attributes": dict(tpg.attributes),
                                               "luns": [{"storage_object": store.path}],
                                               "portals": [{"ip_address": portal.ip_address,
                                                            "port": portal.port}],
                                               "node_acls": [{"node_wwn": acl.node_wwn,
                                                              "chap_userid": acl.chap_userid,
                                                              "chap_password": acl.chap_password}]}]}]}

            def save_to_file(self, path):
                path.write_text(json.dumps(self.dump()))
                path.chmod(0o600)

        root = Root()
        saved = self.root / "saveconfig.json"
        root.save_to_file(saved)
        backend = preparation.LioBackend(saved)
        api = [None] * 9
        api[6] = lambda: root
        backend.api = tuple(api)
        secret = "0123456789ABCDEF"
        self.assertIs(backend.inspect_prepared(self.data, secret)[1], tpg)
        mutations = ((store, "udev_path", "/different.img"),
                     (store, "write_back", True),
                     (acl, "chap_password", "wrong"),
                     (portal, "ip_address", "192.168.77.3"),
                     (root, "sessions", [object()]),
                     (tpg, "enable", True))
        for obj, field, changed in mutations:
            original = getattr(obj, field)
            setattr(obj, field, changed)
            with self.assertRaises(preparation.Refused, msg=field):
                backend.inspect_prepared(self.data, secret)
            setattr(obj, field, original)
        tpg.attributes["authentication"] = "0"
        with self.assertRaises(preparation.Refused):
            backend.inspect_prepared(self.data, secret)
        tpg.attributes["authentication"] = "1"
        tpg.node_acls.append(types.SimpleNamespace(node_wwn="unknown"))
        with self.assertRaises(preparation.Refused):
            backend.inspect_prepared(self.data, secret)
        tpg.node_acls.pop()
        pristine = saved.read_text()
        for path, changed in ((("storage_objects", 0, "dev"), "/other.img"),
                              (("targets", 0, "tpgs", 0, "attributes", "authentication"), "0"),
                              (("targets", 0, "tpgs", 0, "portals", 0, "ip_address"), "192.168.77.3"),
                              (("targets", 0, "tpgs", 0, "node_acls", 0, "chap_password"), "wrong")):
            corrupt = json.loads(pristine)
            node = corrupt
            for part in path[:-1]:
                node = node[part]
            node[path[-1]] = changed
            saved.write_text(json.dumps(corrupt))
            with self.assertRaisesRegex(preparation.Refused, "saved LIO configuration differs"):
                backend.inspect_prepared(self.data, secret)
        saved.write_text('{"targets": [')
        with self.assertRaisesRegex(preparation.Refused, "malformed"):
            backend.inspect_prepared(self.data, secret)
        saved.write_text(pristine)
        backend.activate(self.data, secret, image_stat)
        self.assertTrue(tpg.enable)
        self.assertTrue(json.loads(saved.read_text())["targets"][0]["tpgs"][0]["enable"])
        backend.quarantine(self.data)
        self.assertFalse(tpg.enable)
        self.assertFalse(json.loads(saved.read_text())["targets"][0]["tpgs"][0]["enable"])
        complete_save = root.save_to_file

        def partial_active_save(path):
            complete_save(path)
            record = json.loads(path.read_text())
            record["targets"][0]["tpgs"][0]["node_acls"][0]["chap_password"] = "wrong"
            path.write_text(json.dumps(record))

        with mock.patch.object(root, "save_to_file", side_effect=partial_active_save):
            with self.assertRaisesRegex(preparation.Refused, "not persisted"):
                backend.activate(self.data, secret, image_stat)


if __name__ == "__main__":
    unittest.main()
