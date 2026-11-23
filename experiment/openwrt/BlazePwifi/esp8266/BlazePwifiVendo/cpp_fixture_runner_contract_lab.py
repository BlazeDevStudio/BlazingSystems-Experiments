#!/usr/bin/env python3
"""Contract tests for the shared PHX-HARDWARE C++ fixture runner.

Uses mocked process results and timeout injection; it does not need g++ and
does not claim to compile or execute firmware.
"""
import subprocess
import unittest
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

    def test_compile_timeout_is_reported_with_context(self):
        timeout = subprocess.TimeoutExpired(cmd=["g++"], timeout=30)
        with patch("cpp_fixture_runner.subprocess.run", side_effect=timeout):
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

    def test_execution_timeout_is_reported_with_context(self):
        timeout = subprocess.TimeoutExpired(cmd=["fixture"], timeout=10)
        with patch(
            "cpp_fixture_runner.subprocess.run",
            side_effect=[completed(), timeout],
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
        with patch(
            "cpp_fixture_runner.subprocess.run",
            return_value=completed(returncode=1, stderr=diagnostic),
        ):
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


def verify():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        CppFixtureRunnerContractTests
    )
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("CPP_FIXTURE_RUNNER_CONTRACT_PASS 7/7")


if __name__ == "__main__":
    verify()
