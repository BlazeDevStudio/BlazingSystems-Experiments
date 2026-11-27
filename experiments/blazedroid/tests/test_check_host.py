"""Fail before a multi-hour Android source sync when the build host is too small."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_host import validate_capacity, gib


class HostPreflightTests(unittest.TestCase):
    def test_accepts_full_build_host(self):
        validate_capacity(total_ram=32*gib, free_disk=400*gib)

    def test_refuses_chat_container_ram(self):
        with self.assertRaisesRegex(RuntimeError, "RAM"):
            validate_capacity(total_ram=6*gib, free_disk=400*gib)

    def test_refuses_chat_container_disk(self):
        with self.assertRaisesRegex(RuntimeError, "disk"):
            validate_capacity(total_ram=32*gib, free_disk=30*gib)

    def test_warning_values_are_in_gib(self):
        with self.assertRaisesRegex(RuntimeError, "GiB"):
            validate_capacity(total_ram=16*gib, free_disk=400*gib)

    def test_build_script_preflight_precedes_source_sync(self):
        script = (Path(__file__).resolve().parents[1] / "scripts" / "build-iso.sh").read_text()
        self.assertIn('"$HERE/scripts/check_host.py" "$SRC"', script)
        self.assertLess(script.index('check_host.py" "$SRC"'), script.index('repo sync -c'))


if __name__ == "__main__":
    unittest.main()
