import contextlib
from io import StringIO
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import blaze_lio_configure_ssh_status as setup
from blaze_lio_prepare import Refused
from blaze_lio_ssh_status import read_config


class ConfigureSshStatusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / "private"
        self.folder.mkdir(mode=0o700)
        self.config = self.folder / "ssh-status.json"
        self.spec = self.folder / "spec.json"
        self.secret = self.folder / "chap.txt"
        self.state = self.folder / "state"
        self.backend = object()
        self.owner = os.geteuid()

    def provision(self, inspection="PREPARED_DISABLED"):
        with mock.patch.object(setup, "secure_ancestors"), \
             mock.patch.object(setup, "inspect", return_value=inspection) as check:
            result = setup.provision(self.config, self.spec, self.secret,
                                     self.state, self.backend, owner=self.owner)
        check.assert_called_once_with(self.spec, self.secret, self.state,
                                      self.backend)
        return result

    def test_only_disabled_target_creates_exact_private_config(self):
        self.assertEqual(self.provision(), "STATUS_CONFIGURED")
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o600)
        self.assertEqual(read_config(self.config, self.owner), {
            "spec": self.spec, "secret_file": self.secret, "state_dir": self.state})
        before = self.config.read_bytes()
        with mock.patch.object(setup, "secure_ancestors"), \
             mock.patch.object(setup, "inspect") as check:
            with self.assertRaises(Refused):
                setup.provision(self.config, self.spec, self.secret,
                                self.state, self.backend, owner=self.owner)
        check.assert_not_called()
        self.assertEqual(self.config.read_bytes(), before)

    def test_refuses_active_or_uncertain_before_write(self):
        with self.assertRaises(Refused):
            self.provision("ACTIVE_LAB_TARGET")
        self.assertFalse(self.config.exists())
        with mock.patch.object(setup, "secure_ancestors"), \
             mock.patch.object(setup, "inspect", side_effect=Refused("changed image")):
            with self.assertRaises(Refused):
                setup.provision(self.config, self.spec, self.secret,
                                self.state, self.backend, owner=self.owner)
        self.assertFalse(self.config.exists())

    def test_partial_write_is_preserved_and_retry_refused(self):
        original_write = os.write
        calls = 0

        def partial(fd, data):
            nonlocal calls
            calls += 1
            return original_write(fd, data[:3]) if calls == 1 else 0

        with mock.patch.object(setup, "secure_ancestors"), \
             mock.patch.object(setup, "inspect", return_value="PREPARED_DISABLED"), \
             mock.patch.object(setup.os, "write", side_effect=partial):
            with self.assertRaises(OSError):
                setup.provision(self.config, self.spec, self.secret,
                                self.state, self.backend, owner=self.owner)
        self.assertEqual(self.config.stat().st_size, 3)
        with mock.patch.object(setup, "secure_ancestors"), \
             mock.patch.object(setup, "inspect") as check:
            with self.assertRaises(Refused):
                setup.provision(self.config, self.spec, self.secret,
                                self.state, self.backend, owner=self.owner)
        check.assert_not_called()
        self.assertEqual(self.config.stat().st_size, 3)

    def test_symlink_existing_config_and_unsafe_ancestors_refused(self):
        self.config.symlink_to(self.folder / "elsewhere")
        with mock.patch.object(setup, "secure_ancestors"), \
             mock.patch.object(setup, "inspect") as check:
            with self.assertRaises(Refused):
                setup.provision(self.config, self.spec, self.secret,
                                self.state, self.backend, owner=self.owner)
        check.assert_not_called()
        self.assertTrue(self.config.is_symlink())
        with self.assertRaises(Refused):
            setup.secure_ancestors(Path("relative/spec.json"), self.owner)
        with self.assertRaises(Refused):
            setup.secure_ancestors(Path("/private/../spec.json"), self.owner)
        with self.assertRaises(Refused):
            setup.secure_ancestors(self.spec, self.owner)

    def test_cli_refusal_does_not_print_secret_or_success(self):
        stdout, stderr = StringIO(), StringIO()
        argv = ["setup", "--spec", "/private/spec.json", "--secret-file",
                "/private/chap.txt", "--state-dir", "/private/state"]
        with mock.patch.object(setup.sys, "argv", argv), \
             mock.patch.object(setup.sys, "platform", "linux"), \
             mock.patch.object(setup.os, "geteuid", return_value=0), \
             mock.patch.object(setup, "provision") as provision, \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(setup.main(), 8)
        provision.assert_not_called()
        self.assertEqual(stdout.getvalue(), "")
        self.assertNotIn("/private", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
