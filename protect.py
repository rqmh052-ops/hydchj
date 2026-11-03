#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from protector_core import protect_file

parser = argparse.ArgumentParser(description="Protect one Python source file as a self-running .py loader.")
parser.add_argument("input", type=Path)
parser.add_argument("-o", "--output", type=Path)
args = parser.parse_args()
try:
    result = protect_file(args.input, args.output)
except Exception as exc:
    parser.error(str(exc))
print(f"Created: {result}")
