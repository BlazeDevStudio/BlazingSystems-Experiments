"""Portable preflight tests for Windows HWND smoke helper (NOT a Windows smoke)."""
import importlib.util
from pathlib import Path
import unittest

source = Path(__file__).with_name("smoke_windows_gui.py")
spec = importlib.util.spec_from_file_location("smoke_windows_gui", source)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class SmokeHelperTests(unittest.TestCase):
    def test_exact_window_title(self):
        self.assertTrue(mod.title_is_expected(mod.TITLE_MARKER))

    def test_reject_lookalike_title(self):
        self.assertFalse(mod.title_is_expected(mod.TITLE_MARKER + " (fake)"))

    def test_reject_other_application(self):
        self.assertFalse(mod.title_is_expected("BlazeHackintosh-Toolkit.exe"))

    def test_normalized_case_executable(self):
        self.assertTrue(mod.executable_is_expected("C:/Test/Blaze.exe", "c:\\test\\BLAZE.EXE"))

    def test_reject_different_executable(self):
        self.assertFalse(mod.executable_is_expected("C:/Test/Other.exe", "C:/Test/Blaze.exe"))

    def test_ancestry_accepts_root_and_child(self):
        parents = {10: 1, 20: 10, 30: 20}
        self.assertTrue(mod.pid_is_descendant(10, 10, parents))
        self.assertTrue(mod.pid_is_descendant(30, 10, parents))

    def test_ancestry_rejects_unrelated_same_exe(self):
        parents = {10: 1, 20: 10, 40: 1, 50: 40}
        self.assertFalse(mod.pid_is_descendant(50, 10, parents))

    def test_ancestry_rejects_cycles_and_gaps(self):
        self.assertFalse(mod.pid_is_descendant(20, 10, {20: 30, 30: 20}))
        self.assertFalse(mod.pid_is_descendant(20, 10, {20: 999}))
        self.assertFalse(mod.pid_is_descendant(0, 10, {}))
        self.assertFalse(mod.pid_is_descendant(20, 0, {}))

    def test_ancestry_rejects_excessive_depth(self):
        parents = {i: i - 1 for i in range(2, 100)}
        self.assertFalse(mod.pid_is_descendant(99, 1, parents))

    def test_windows_snapshot_fails_closed_on_linux(self):
        import sys
        if sys.platform == "win32":
            self.skipTest("Non-Windows only")
        with self.assertRaises(RuntimeError):
            mod._windows_process_parents()

    def test_refuse_non_windows_execution(self):
        import sys
        if sys.platform == "win32":
            self.skipTest("Requires non-Windows platform")
        with self.assertRaises(RuntimeError):
            mod.run_smoke(Path("dummy.exe"))


if __name__ == "__main__":
    unittest.main()
