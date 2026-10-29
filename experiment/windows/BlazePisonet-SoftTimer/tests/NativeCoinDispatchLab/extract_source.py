#!/usr/bin/env python3
"""TEST ONLY. Extract guarded verbatim current production methods for native .NET 8.
Exit 3: mismatch/invalid setup; never silently substitute a hand-authored method.
"""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "src" / "BlazePisonet.SoftTimer"
EXPECTED = {
    "AppController.cs": "dd9e02ef6ca28f7ec48cef2c61489fcbf783b30d",
    "BlazePwifiClient.cs": "44f2866e6c351fe763f7e4aa2663c26fb563263a",
}
METHODS = (
    ("AppController.cs", "private async Task HandleCoinPulse(SerialCoinAcceptance accepted)", "AppController"),
    ("BlazePwifiClient.cs", "internal CoinWindowSnapshot? CaptureCoinWindow()", "BlazePwifiClient"),
    ("BlazePwifiClient.cs", "private bool CoinWindowStillOwned(CoinWindowSnapshot captured)", "BlazePwifiClient"),
    ("BlazePwifiClient.cs", "public Task<bool> ForwardCoinAsync(int pulses = 1)", "BlazePwifiClient"),
    ("BlazePwifiClient.cs", "internal async Task<bool> ForwardCoinAsync(CoinWindowSnapshot captured, int pulses = 1)", "BlazePwifiClient"),
)

def extract(text, signature):
    if text.count(signature) != 1:
        raise ValueError("exact signature not unique: " + signature)
    begin = text.index(signature)
    opening = text.find("{", begin + len(signature))
    if opening == -1:
        raise ValueError("missing opening brace")
    level = 0
    for pos in range(opening, len(text)):
        if text[pos] == "{":
            level += 1
        elif text[pos] == "}":
            level -= 1
            if level == 0:
                return text[begin:pos + 1]
    raise ValueError("unbalanced method: " + signature)

def main():
    sources = {}
    for name, expected in EXPECTED.items():
        path = SOURCE / name
        actual = subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()
        if actual != expected:
            raise ValueError(f"INCONCLUSIVE_SOURCE_BLOB: {name} expected={expected} actual={actual}")
        sources[name] = path.read_text(encoding="utf-8-sig")
        print(f"EXACT_SOURCE_BLOB_PASS {name} {actual}")
    declaration = "internal sealed record CoinWindowSnapshot("
    client = sources["BlazePwifiClient.cs"]
    if client.count(declaration) != 1:
        raise ValueError("immutable window declaration missing/duplicated")
    at = client.index(declaration)
    ending = client.find(");", at)
    if ending < 0:
        raise ValueError("window record unterminated")
    chunks = [
        "// TEST ONLY: exact source methods; never edit this generated file.\n",
        "#nullable enable\n",
        "using System;\nusing System.Collections.Generic;\n",
        "using System.Security.Cryptography;\nusing System.Net.Http;\n",
        "using System.Threading.Tasks;\nusing System.Text.Json;\n",
        "namespace BlazePisonet.SoftTimer {\n",
        client[at:ending + 2] + "\n",
    ]
    for name, signature, cls in METHODS:
        method = extract(sources[name], signature)
        chunks.append(f"public sealed partial class {cls} {{\n{method}\n}}\n")
        print("EXACT_SOURCE_METHOD " + name + ": " + signature)
    chunks.append("}\n")
    (HERE / "GeneratedMethods.g.cs").write_text("".join(chunks), encoding="utf-8")
    print("EXACT_SOURCE_ASYNC_ATTRIBUTION_METHODS_READY")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("INCONCLUSIVE_SOURCE_SETUP: " + str(exc), file=sys.stderr)
        sys.exit(3)
