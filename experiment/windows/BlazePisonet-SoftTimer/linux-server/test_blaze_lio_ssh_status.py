import contextlib
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import blaze_lio_ssh_status as ssh_status
from blaze_lio_prepare import Refused


class SshStatusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / "private"
        self.folder.mkdir(mode=0o700)
        self.config = self.folder / "ssh-status.json"
        self.data = {"spec": "/private/spec.json", "secret_file": "/private/chap.txt",
                     "state_dir": "/private/state"}
        self.write(self.data)

    def write(self, value):
        self.config.write_text(json.dumps(value))
        self.config.chmod(0o600)

    def test_exact_private_config_only(self):
        result = ssh_status.read_config(self.config, os.geteuid())
        self.assertEqual(result["spec"], Path("/private/spec.json"))
        for data in ({**self.data, "extra": "/bad"},
                     {**self.data, "spec": "relative/path"},
                     {**self.data, "state_dir": "/"}):
            self.write(data)
            with self.assertRaises(Refused):
                ssh_status.read_config(self.config, os.geteuid())
        self.config.write_text('{"spec":"/a","spec":"/b"}')
        with self.assertRaises(Refused):
            ssh_status.read_config(self.config, os.geteuid())
        self.write(self.data)
        self.config.chmod(0o644)
        with self.assertRaises(Refused):
            ssh_status.read_config(self.config, os.geteuid())
        self.config.unlink()
        self.config.symlink_to(self.folder / "other")
        with self.assertRaises(Refused):
            ssh_status.read_config(self.config, os.geteuid())

    def test_forced_command_refuses_unexpected_and_sanitizes_failure(self):
        stdout, stderr = StringIO(), StringIO()
        with mock.patch.object(ssh_status, "CONFIG", self.config), \
             mock.patch.object(ssh_status.sys, "argv", ["script"]), \
             mock.patch.object(ssh_status.sys, "platform", "linux"), \
             mock.patch.object(ssh_status.os, "geteuid", return_value=0), \
             mock.patch.dict(os.environ, {"SSH_ORIGINAL_COMMAND": "other"}), \
             mock.patch.object(ssh_status, "inspect") as inspect, \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(ssh_status.main(), 8)
            inspect.assert_not_called()
        self.assertEqual(stdout.getvalue(), "")
        self.assertNotIn("/private", stderr.getvalue())

    def test_forced_command_dispatches_only_fixed_paths(self):
        with mock.patch.object(ssh_status, "inspect", return_value="PREPARED_DISABLED") as inspect:
            result = ssh_status.inspect_configured(self.config, os.geteuid(), object())
            self.assertEqual(result, "PREPARED_DISABLED")
            self.assertEqual(inspect.call_args.args[:3],
                             (Path("/private/spec.json"), Path("/private/chap.txt"),
                              Path("/private/state")))


if __name__ == "__main__":
    unittest.main()
