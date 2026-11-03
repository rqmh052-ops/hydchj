import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from protector_core import MAX_SOURCE_BYTES, protect_bytes


def run_script(tmp_path, content):
    source = tmp_path / "protected.py"
    source.write_bytes(content)
    return subprocess.run([sys.executable, str(source)], text=True, capture_output=True, timeout=20)


def test_protected_script_runs_with_arguments(tmp_path):
    source = b"import sys\nprint('OK', __name__, sys.argv[0].endswith('protected.py'))\n"
    result = run_script(tmp_path, protect_bytes(source, "example.py"))
    assert result.returncode == 0, result.stderr
    assert "OK __main__ True" in result.stdout


def test_docstrings_removed_and_compiled_payload_not_source(tmp_path):
    original = b'"TOP SECRET MARKER"\ndef f():\n    "INNER SECRET MARKER"\n    return 7\nprint(f())\n'
    output = protect_bytes(original, "sample.py").decode()
    assert "TOP SECRET MARKER" not in output
    assert "INNER SECRET MARKER" not in output
    assert "print(f())" not in output
    assert run_script(tmp_path, output.encode()).returncode == 0


def test_assert_statements_keep_their_normal_behavior(tmp_path):
    result = run_script(tmp_path, protect_bytes(b"assert False, 'assert preserved'\n", "assertion.py"))
    assert result.returncode != 0
    assert "assert preserved" in result.stderr


def test_ciphertext_tampering_is_rejected(tmp_path):
    output = protect_bytes(b"print('never run')\n", "sample.py").decode()
    match = re.search(r"_P='([^']+)'", output)
    assert match
    changed = match.group(1)
    replacement = ('0' if changed[-1] != '0' else '1')
    output = output[:match.start(1)] + changed[:-1] + replacement + output[match.end(1):]
    result = run_script(tmp_path, output.encode())
    assert result.returncode == 4
    assert "authentication failed" in result.stderr
    assert "never run" not in result.stdout


def test_requires_exact_python_minor(tmp_path):
    output = protect_bytes(b"print('no')\n", "sample.py").decode()
    match = re.search(r"_V='([^']+)'", output)
    assert match
    wrong = "0.0" if match.group(1) != "0.0" else "1.1"
    output = output[:match.start(1)] + wrong + output[match.end(1):]
    result = run_script(tmp_path, output.encode())
    assert result.returncode == 3
    assert "Requires CPython" in result.stderr


def test_rejects_non_python_or_oversize():
    with pytest.raises(ValueError):
        protect_bytes(b"", "payload.txt")
    with pytest.raises(ValueError):
        protect_bytes(b"x" * (MAX_SOURCE_BYTES + 1), "large.py")
