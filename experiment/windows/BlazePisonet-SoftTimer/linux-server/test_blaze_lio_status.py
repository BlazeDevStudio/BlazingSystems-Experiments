import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import blaze_lio_prepare as preparation
import blaze_lio_status as status


class Backend:
    def __init__(self, refuse=False):
        self.calls = []
        self.refuse = refuse

    def preflight(self):
        self.calls.append("preflight")

    def prepare(self, spec, secret):
        self.calls.append("prepare")

    def inspect_prepared(self, spec, secret, image_stat):
        self.calls.append("inspect")
        if self.refuse:
            raise preparation.Refused("CHAP or ACL drift")


class StatusTests(unittest.TestCase):
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
        key = hashlib.sha256(self.data["target_iqn"].encode()).hexdigest()
        self.marker = self.state / (key + ".json")
        self.backend = Backend()
        preparation.prepare(self.spec, self.secret, self.state, self.backend,
                            require_root=False)
        self.backend.calls.clear()

    def inspect(self, backend=None):
        return status.inspect(self.spec, self.secret, self.state,
                              backend or self.backend, require_root=False)

    def test_prepared_is_read_only_and_exactly_inspected(self):
        before = self.marker.read_bytes()
        before_stat = self.marker.stat()
        self.assertEqual(self.inspect(), "PREPARED_DISABLED")
        self.assertEqual(self.backend.calls, ["inspect"])
        self.assertEqual(self.marker.read_bytes(), before)
        self.assertEqual(self.marker.stat().st_mtime_ns, before_stat.st_mtime_ns)

    def test_started_active_and_activating_intents_never_claim_healthy(self):
        for state in ("started", "activating", "active"):
            with self.subTest(state=state):
                record = json.loads(self.marker.read_text())
                record["status"] = state
                self.marker.write_text(json.dumps(record))
                with self.assertRaisesRegex(preparation.Refused, "not safely verifiable"):
                    self.inspect()
                self.assertEqual(self.backend.calls, [])

    def test_corrupt_and_duplicate_intent_refused_before_backend(self):
        for bad in ("{bad", '{"status":"prepared_disabled","status":"active"}'):
            with self.subTest(bad=bad):
                self.marker.write_text(bad)
                with self.assertRaises(preparation.Refused):
                    self.inspect()
                self.assertEqual(self.backend.calls, [])

    def test_same_size_replaced_image_refused_before_backend(self):
        old = self.image.stat()
        self.image.unlink()
        with self.image.open("wb") as out:
            out.truncate(old.st_size)
        self.image.chmod(0o600)
        os.utime(self.image, ns=(old.st_atime_ns, old.st_mtime_ns + 1_000_000_000))
        with self.assertRaisesRegex(preparation.Refused, "image identity"):
            self.inspect()
        self.assertEqual(self.backend.calls, [])

    def test_live_acl_chap_refusal_is_not_healthy(self):
        backend = Backend(refuse=True)
        with self.assertRaisesRegex(preparation.Refused, "CHAP or ACL drift"):
            self.inspect(backend)
        self.assertEqual(backend.calls, ["inspect"])

    def test_unsafe_or_missing_lock_refused_before_backend(self):
        lock = self.state / ".lock"
        lock.chmod(0o644)
        with self.assertRaisesRegex(preparation.Refused, "unsafe preparation lock"):
            self.inspect()
        lock.unlink()
        with self.assertRaises(FileNotFoundError):
            self.inspect()
        self.assertEqual(self.backend.calls, [])

    def test_cli_refusal_has_no_success_or_secret_output(self):
        out, err = io.StringIO(), io.StringIO()
        argv = ["blaze_lio_status.py", str(self.spec), "--secret-file",
                str(self.secret), "--state-dir", str(self.state)]
        with mock.patch.object(status.sys, "argv", argv), \
             mock.patch.object(status, "inspect", side_effect=RuntimeError("0123456789ABCDEF")), \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(status.main(), 8)
        self.assertEqual(out.getvalue(), "")
        self.assertNotIn("0123456789ABCDEF", err.getvalue())


if __name__ == "__main__":
    unittest.main()
