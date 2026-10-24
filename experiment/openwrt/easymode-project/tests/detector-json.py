"""Exercise the shipped serializer only: no hardware probes or host sysinfo writes."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile


def check(shell, awk=None):
    source = (Path(__file__).resolve().parents[1] / "core/detect.sh").read_text(encoding="utf-8")
    boundary = '\nboard="unknown";'
    assert source.count(boundary) == 1, "detector initialization boundary changed"
    prefix = source.split(boundary, 1)[0] + "\n"
    assert "json_escape()" in prefix, "shipped escape function missing"
    writers = [line for line in source.splitlines() if line.startswith("printf '{\"board\":")]
    assert len(writers) == 1, "detector JSON writer boundary changed"

    cases = [("empty", ""), ("plain", "Router 123"),
             ("quotes-backslash", 'Router "Pro" \\ share')]
    # NUL cannot be represented in a POSIX shell variable; every other JSON control can.
    cases += [(f"control-{n:02x}", "before" + chr(n) + "after") for n in range(1, 32)]
    cases += [
        ("all-controls", "".join(chr(n) for n in range(1, 32))),
        ("leading-lf", "\nrouter"), ("trailing-lf", "router\n"),
        ("trailing-two-lf", "router\n\n"), ("only-lf", "\n\n"),
        ("unicode", "Blaze \U0001f525 \u2013 \u8def\u7531\u5668 caf\u00e9"),
        ("mixed", 'a\\"\t\r\nb'), ("shell-literals", '$(false); `false` $HOME')
    ]
    env = dict(os.environ, LC_ALL="C")
    script = [prefix]
    for index, (_, value) in enumerate(cases):
        env[f"EASYMODE_JSON_VALUE_{index}"] = value
        script.append(f'printf \'%s\\000\' "$(json_escape "$EASYMODE_JSON_VALUE_{index}")"\n')

    records = [
        ("all-fields-controls", "".join(chr(n) for n in range(1, 32))),
        ("all-fields-unicode", "Blaze \U0001f525 \u8def\u7531\u5668"),
        ("all-fields-quotes-trailing-lf", 'Router "Pro" \\ share\n\n')
    ]
    for index, (_, value) in enumerate(records):
        env[f"EASYMODE_JSON_RECORD_{index}"] = value
        script += [f'board="$EASYMODE_JSON_RECORD_{index}"\n',
                   'model="$board"; release="$board"; arch="$board"\n',
                   'manager=none; wifi=0; cellular=0; nics=0; profile=generic\n',
                   writers[0] + "\nprintf '\\000'\n"]

    with tempfile.TemporaryDirectory(prefix="easymode-json-") as temporary:
        if awk:
            # Select a second real awk implementation without changing product code.
            executable = shutil.which(awk[0])
            assert executable, "requested awk executable is required"
            shim = Path(temporary) / "awk"
            shim.write_text("#!/bin/sh\nexec " + " ".join(shlex.quote(arg) for arg in [executable, *awk[1:]]) +
                            ' "$@"\n', encoding="utf-8", newline="\n")
            shim.chmod(0o755)
            env["PATH"] = temporary + os.pathsep + env["PATH"]
        # Stdin and environment avoid Windows/MSYS argv and CR quoting artifacts.
        result = subprocess.run(shell + ["-s"], input="".join(script).encode("utf-8"),
                                env=env, capture_output=True, timeout=60, check=True)
    assert not result.stderr, result.stderr.decode("utf-8", errors="replace")
    parts = result.stdout.split(b"\0")
    assert parts.pop() == b"", "missing final fixture separator"
    assert len(parts) == len(cases) + len(records), "unexpected serializer output"
    failures = []
    for (name, expected), raw in zip(cases, parts):
        try:
            assert json.loads(b'"' + raw + b'"') == expected, "value did not round-trip"
        except (ValueError, AssertionError) as error:
            failures.append((name, str(error)))
    for (name, value), raw in zip(records, parts[len(cases):]):
        try:
            assert json.loads(raw) == dict(board=value, model=value, release=value, arch=value,
                                           package_manager="none", wifi=0, cellular=0,
                                           netdev_count=0, recommended="generic"), "schema/value changed"
        except (ValueError, AssertionError) as error:
            failures.append((name, str(error)))
    for name, error in failures:
        print(f"FAIL {name}: {error}")
    print(f"detector JSON: {len(cases) + len(records)} cases, {len(failures)} failures; no probes/sysinfo writes")
    return not failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shell", default="sh")
    parser.add_argument("--awk", help="test a particular awk executable")
    parser.add_argument("--busybox", help="test BusyBox sh and awk")
    args = parser.parse_args()
    if args.busybox:
        busybox = shutil.which(args.busybox)
        assert busybox, "BusyBox is required when requested"
        shell, awk = [busybox, "sh"], [busybox, "awk"]
    else:
        shell, awk = [args.shell], [args.awk] if args.awk else None
    raise SystemExit(0 if check(shell, awk) else 1)
