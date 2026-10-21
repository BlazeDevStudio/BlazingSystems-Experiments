#!/usr/bin/env python3
"""Stage the source and local Arduino libraries shipped with Vendo firmware."""
import argparse
from pathlib import Path
import shutil


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("target", choices=("esp8266", "esp32"))
parser.add_argument("output", type=Path)
args = parser.parse_args()

root = Path(__file__).resolve().parents[1]
sketch = "BlazePwifiVendo" if args.target == "esp8266" else "BlazePwifiVendo32"
source = args.output / "source"
args.output.mkdir(parents=True, exist_ok=True)
shutil.copytree(root / args.target / sketch, source / sketch)
shutil.copytree(root / "esp/libraries", source / "libraries")
shutil.copyfile(root / "esp/REBUILD.md", source / "README.md")
# Retain the existing top-level source filename for artifact consumers.
shutil.copyfile(source / sketch / (sketch + ".ino"), args.output / (sketch + ".ino"))
