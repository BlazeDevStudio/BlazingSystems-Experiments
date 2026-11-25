#!/usr/bin/env python3
"""Contract tests for the shared PHX-HARDWARE C++ fixture runner.

Uses mocked process results and timeout injection; it does not need g++ and
does not claim to compile or execute firmware.
"""
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from cpp_fixture_runner import (
    DEFAULT_COMPILE_TIMEOUT_SECONDS,
    DEFAULT_RUN_TIMEOUT_SECONDS,
    MAX_DIAGNOSTIC_TAIL_CHARS,
    run_cpp_fixture,
)


def completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(
        args=["fixture"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


class CppFixtureRunnerContractTests(unittest.TestCase):
    def test_default_compile_and_run_timeouts_are_bounded(self):
        with patch(
            "cpp_fixture_runner.subprocess.run",
            side_effect=[
                completed(),
                completed(stdout="fixture-ok"),
            ],
        ) as run:
            result = run_cpp_fixture(
                "int main() { return 0; }",
                prefix="phx-runner-contract-",
                stem="fixture",
                context="default-bounds",
            )

        self.assertEqual(result.stdout, "fixture-ok")
        self.assertEqual(
            run.call_args_list[0].kwargs["timeout"],
            DEFAULT_COMPILE_TIMEOUT_SECONDS,
        )
        self.assertEqual(
            run.call_args_list[1].kwargs["timeout"],
            DEFAULT_RUN_TIMEOUT_SECONDS,
        )
        self.assertEqual(DEFAULT_COMPILE_TIMEOUT_SECONDS, 30)
        self.assertEqual(DEFAULT_RUN_TIMEOUT_SECONDS, 10)

    def test_explicit_timeout_overrides_are_preserved(self):
        with patch(
            "cpp_fixture_runner.subprocess.run",
            side_effect=[completed(), completed(returncode=23)],
        ) as run:
            result = run_cpp_fixture(
                "int main() { return 23; }",
                prefix="phx-runner-contract-",
                stem="fixture",
                compile_timeout=7,
                run_timeout=3,
                context="override",
            )

        self.assertEqual(result.returncode, 23)
        self.assertEqual(run.call_args_list[0].kwargs["timeout"], 7)
        self.assertEqual(run.call_args_list[1].kwargs["timeout"], 3)

    def test_invalid_timeout_overrides_are_rejected_before_process_launch(self):
        invalid_values = (
            None,
            0,
            -1,
            float("inf"),
            float("-inf"),
            float("nan"),
            True,
            "10",
        )
        for parameter in ("compile_timeout", "run_timeout"):
            for value in invalid_values:
                with self.subTest(parameter=parameter, value=value):
                    with patch("cpp_fixture_runner.subprocess.run") as run:
                        with self.assertRaisesRegex(
                            ValueError,
                            f"{parameter} must be a finite positive number of seconds",
                        ):
                            run_cpp_fixture(
                                "int main() { return 0; }",
                                prefix="phx-runner-contract-",
                                stem="fixture",
                                **{parameter: value},
                            )
                    run.assert_not_called()

    def test_stem_is_a_safe_filename_component_before_tempfile_creation(self):
        class FakeTemporaryDirectory:
            def __enter__(self):
                return "/tmp/phx-runner-contract-safe"

            def __exit__(self, *args):
                return False

        invalid_stems = ("", ".", "..", "../escape", "/tmp/escape", r"..\\escape", None, 7)
        for stem in invalid_stems:
            with self.subTest(stem=stem):
                with patch(
                    "cpp_fixture_runner.tempfile.TemporaryDirectory",
                    return_value=FakeTemporaryDirectory(),
                ) as temporary_directory, patch(
                    "cpp_fixture_runner.Path.write_text"
                ) as write_text, patch(
                    "cpp_fixture_runner.subprocess.run",
                    side_effect=[completed(), completed()],
                ) as process_run:
                    with self.assertRaisesRegex(
                        ValueError,
                        "stem must be a single safe filename component",
                    ):
                        run_cpp_fixture(
                            "int main() { return 0; }",
                            prefix="phx-runner-contract-",
                            stem=stem,
                        )

                    temporary_directory.assert_not_called()
                    write_text.assert_not_called()
                    process_run.assert_not_called()

    def test_unsafe_prefixes_are_rejected_before_tempfile_creation(self):
        class FakeTemporaryDirectory:
            def __enter__(self):
                return "/tmp/phx-runner-contract-safe"

            def __exit__(self, *args):
                return False

        invalid_prefixes = (
            None,
            7,
            "../escape",
            "/tmp/escape",
            r"..\\escape",
            r"C:\\escape",
            "C:relative",
            chr(0),
        )
        for prefix in invalid_prefixes:
            with self.subTest(prefix=prefix):
                with patch(
                    "cpp_fixture_runner.tempfile.TemporaryDirectory",
                    return_value=FakeTemporaryDirectory(),
                ) as temporary_directory, patch(
                    "cpp_fixture_runner.Path.write_text"
                ) as write_text, patch(
                    "cpp_fixture_runner.subprocess.run",
                    side_effect=[completed(), completed()],
                ) as process_run:
                    with self.assertRaisesRegex(
                        ValueError,
                        "prefix must be a safe filename prefix",
                    ):
                        run_cpp_fixture(
                            "int main() { return 0; }",
                            prefix=prefix,
                            stem="fixture",
                        )

                    temporary_directory.assert_not_called()
                    write_text.assert_not_called()
                    process_run.assert_not_called()

    def test_empty_prefix_is_allowed(self):
        class FakeTemporaryDirectory:
            def __enter__(self):
                return "/tmp/phx-runner-contract-safe"

            def __exit__(self, *args):
                return False

        with patch(
            "cpp_fixture_runner.tempfile.TemporaryDirectory",
            return_value=FakeTemporaryDirectory(),
        ) as temporary_directory, patch(
            "cpp_fixture_runner.Path.write_text"
        ) as write_text, patch(
            "cpp_fixture_runner.subprocess.run",
            side_effect=[completed(), completed(stdout="fixture-ok")],
        ) as process_run:
            result = run_cpp_fixture(
                "int main() { return 0; }",
                prefix="",
                stem="fixture",
            )

        self.assertEqual(result.stdout, "fixture-ok")
        temporary_directory.assert_called_once_with(prefix="")
        write_text.assert_called_once()
        self.assertEqual(process_run.call_count, 2)

    def test_compile_timeout_is_reported_with_context(self):
        timeout = subprocess.TimeoutExpired(cmd=["g++"], timeout=30)
        temp_dirs = []

        def fail_compile(command, **kwargs):
            temp_dirs.append(Path(command[-3]).parent)
            raise timeout

        with patch("cpp_fixture_runner.subprocess.run", side_effect=fail_compile):
            with self.assertRaisesRegex(
                RuntimeError,
                "compile-timeout-probe: compile timed out",
            ):
                run_cpp_fixture(
                    "int main() { return 0; }",
                    prefix="phx-runner-contract-",
                    stem="fixture",
                    context="compile-timeout-probe",
                )

        self.assertEqual(len(temp_dirs), 1)
        self.assertFalse(temp_dirs[0].exists())

    def test_execution_timeout_is_reported_with_context(self):
        timeout = subprocess.TimeoutExpired(cmd=["fixture"], timeout=10)
        temp_dirs = []

        def compile_then_timeout(command, **kwargs):
            if command[0] == "g++":
                temp_dirs.append(Path(command[-3]).parent)
                return completed()
            raise timeout

        with patch(
            "cpp_fixture_runner.subprocess.run",
            side_effect=compile_then_timeout,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "execution-timeout-probe: execution timed out",
            ):
                run_cpp_fixture(
                    "int main() { return 0; }",
                    prefix="phx-runner-contract-",
                    stem="fixture",
                    context="execution-timeout-probe",
                )

        self.assertEqual(len(temp_dirs), 1)
        self.assertFalse(temp_dirs[0].exists())

    def test_timeout_diagnostics_preserve_bounded_stdout_and_stderr(self):
        cases = (
            (
                "compile",
                subprocess.TimeoutExpired(
                    cmd=["g++"],
                    timeout=30,
                    output="COMPILE-STDOUT-HEAD" + ("x" * 3100) + "COMPILE-STDOUT-TAIL",
                    stderr=b"COMPILE-STDERR-HEAD" + (b"y" * 3100) + b"COMPILE-STDERR-TAIL",
                ),
                "compile-timeout-diagnostics",
            ),
            (
                "execution",
                subprocess.TimeoutExpired(
                    cmd=["fixture"],
                    timeout=10,
                    output=b"EXEC-STDOUT-HEAD" + (b"x" * 3100) + b"EXEC-STDOUT-TAIL",
                    stderr="EXEC-STDERR-HEAD" + ("y" * 3100) + "EXEC-STDERR-TAIL",
                ),
                "execution-timeout-diagnostics",
            ),
        )
        for phase, timeout, context in cases:
            with self.subTest(phase=phase):
                side_effect = (
                    [timeout] if phase == "compile" else [completed(), timeout]
                )
                with patch(
                    "cpp_fixture_runner.subprocess.run",
                    side_effect=side_effect,
                ):
                    with self.assertRaises(RuntimeError) as caught:
                        run_cpp_fixture(
                            "int main() { return 0; }",
                            prefix="phx-runner-contract-",
                            stem="fixture",
                            context=context,
                        )

                message = str(caught.exception)
                self.assertIn(f"{context}: {phase} timed out", message)
                for stream in ("stdout", "stderr"):
                    marker = f"{stream} tail:\n"
                    self.assertIn(marker, message)
                    tail = message.split(marker, 1)[1].split("\n", 1)[0]
                    self.assertLessEqual(
                        len(tail),
                        MAX_DIAGNOSTIC_TAIL_CHARS,
                    )

                prefix = "COMPILE" if phase == "compile" else "EXEC"
                for stream in ("STDOUT", "STDERR"):
                    self.assertNotIn(f"{prefix}-{stream}-HEAD", message)
                    self.assertIn(f"{prefix}-{stream}-TAIL", message)

    def test_compile_failure_keeps_context_and_bounded_diagnostic_tail(self):
        diagnostic = "EARLY-MARKER\n" + ("x" * 3500) + "\nTAIL-MARKER"
        temp_dirs = []

        def fail_compile(command, **kwargs):
            source_path = Path(command[-3])
            temp_dirs.append(source_path.parent)
            self.assertTrue(source_path.is_file())
            return completed(returncode=1, stderr=diagnostic)

        with patch(
            "cpp_fixture_runner.subprocess.run",
            side_effect=fail_compile,
        ) as run:
            with self.assertRaises(RuntimeError) as caught:
                run_cpp_fixture(
                    "int main() { return 0; }",
                    prefix="phx-runner-contract-",
                    stem="fixture",
                    context="compile-failure-probe",
                )

        message = str(caught.exception)
        self.assertIn("compile-failure-probe: compile failed", message)
        self.assertIn("TAIL-MARKER", message)
        self.assertNotIn("EARLY-MARKER", message)
        self.assertLessEqual(len(message.split("compile failed:\n", 1)[1]), MAX_DIAGNOSTIC_TAIL_CHARS)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(len(temp_dirs), 1)
        self.assertFalse(temp_dirs[0].exists())

    def test_success_keeps_temp_directory_until_execution_then_cleans(self):
        temp_dirs = []

        def successful_run(command, **kwargs):
            if command[0] == "g++":
                source_path = Path(command[-3])
                temp_dirs.append(source_path.parent)
                self.assertEqual(source_path.name, "fixture.cpp")
                self.assertTrue(source_path.is_file())
                for flag in ("-std=c++17", "-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter"):
                    self.assertIn(flag, command)
                self.assertEqual(kwargs["timeout"], DEFAULT_COMPILE_TIMEOUT_SECONDS)
                return completed()

            self.assertTrue(temp_dirs[0].exists())
            self.assertEqual(Path(command[0]).name, "fixture")
            self.assertEqual(kwargs["timeout"], DEFAULT_RUN_TIMEOUT_SECONDS)
            return completed(stdout="fixture-ok")

        with patch(
            "cpp_fixture_runner.subprocess.run",
            side_effect=successful_run,
        ) as run:
            result = run_cpp_fixture(
                "int main() { return 0; }",
                prefix="phx-runner-contract-",
                stem="fixture",
                extra_flags=("-Wno-unused-parameter",),
            )

        self.assertEqual(result.stdout, "fixture-ok")
        self.assertEqual(run.call_count, 2)
        self.assertEqual(len(temp_dirs), 1)
        self.assertFalse(temp_dirs[0].exists())



def verify_poll_fault_latch_lab_uses_shared_runner():
    """Keep the first-fault edge lab on the shared bounded C++ runner."""
    lab = Path(__file__).with_name("poll_fault_latch_edge_count_lab.py")
    source = lab.read_text(encoding="utf-8")
    forbidden = (
        "import subprocess",
        "import tempfile",
        "subprocess.run(",
        "tempfile.TemporaryDirectory(",
    )
    for token in forbidden:
        if token in source:
            raise AssertionError(
                "poll_fault_latch_edge_count_lab.py duplicates shared runner mechanics: "
                + token
            )
    required = (
        "from cpp_fixture_runner import run_cpp_fixture",
        "run_cpp_fixture(",
        'prefix="phx-second-isr-"',
        'extra_flags=("-pedantic", "-O2")',
        "compile_timeout=30",
        "run_timeout=10",
        "context=",
    )
    for token in required:
        if token not in source:
            raise AssertionError(
                "poll_fault_latch_edge_count_lab.py missing shared-runner contract: "
                + token
            )
    print("POLL_FAULT_LATCH_SHARED_RUNNER_GUARD_PASS")


def verify():
    verify_poll_fault_latch_lab_uses_shared_runner()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        CppFixtureRunnerContractTests
    )
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("CPP_FIXTURE_RUNNER_CONTRACT_PASS 11/11")


if __name__ == "__main__":
    verify()
