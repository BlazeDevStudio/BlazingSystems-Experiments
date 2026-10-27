#!/usr/bin/env python3
"""TEST ONLY. Compile verbatim production method bodies; refuse changed source blobs."""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "src" / "BlazePisonet.SoftTimer"
METHODS = (
    ("AppController.cs", "3d16d80c79b4dbe55d006c5453e5cc605cd84421",
     "private async Task HandleCoinPulse()", "AppController"),
    ("BlazePwifiClient.cs", "bf7e35023e8db51dde399b98464e10b99a31735a",
     "public async Task<bool> ForwardCoinAsync(int pulses = 1)", "BlazePwifiClient"),
)

def extract(content, signature):
    if content.count(signature) != 1:
        raise ValueError("expected one exact method signature: " + signature)
    start = content.index(signature)
    opening = content.find("{", start + len(signature))
    if opening < 0:
        raise ValueError("missing opening brace")
    depth = 0
    for i in range(opening, len(content)):
        if content[i] == "{":
            depth += 1
        elif content[i] == "}":
            depth -= 1
            if depth == 0:
                return content[start:i + 1]
    raise ValueError("unbalanced source method")

def main():
    chunks = [
        "// TEST ONLY. GENERATED from exact Git blobs; do not hand-edit.\n",
        "using System;\nusing System.Threading.Tasks;\nusing System.Text.Json;\n",
        "namespace BlazePisonet.SoftTimer {\n",
    ]
    for name, expected, signature, cls in METHODS:
        path = SOURCE / name
        actual = subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()
        if actual != expected:
            raise ValueError(f"INCONCLUSIVE_SOURCE_BLOB: {name} expected={expected} actual={actual}")
        method = extract(path.read_text(encoding="utf-8-sig"), signature)
        chunks.append(f"public sealed partial class {cls} {{\n{method}\n}}\n")
        print(f"EXACT_SOURCE_METHOD: {name} blob={actual} signature={signature}")
    chunks.append("}\n")
    (HERE / "GeneratedMethods.g.cs").write_text("".join(chunks), encoding="utf-8")
    print("EXACT_SOURCE_METHODS_READY: AppController.HandleCoinPulse + BlazePwifiClient.ForwardCoinAsync")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("INCONCLUSIVE_SOURCE_SETUP: " + str(exc), file=sys.stderr)
        sys.exit(3)
