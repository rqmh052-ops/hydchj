"""Offline Python-script protector. See README for honest security limits."""
from __future__ import annotations

import ast
import base64
import marshal
import secrets
import sys
import zlib
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

MAX_SOURCE_BYTES = 32 * 1024 * 1024


def _strip_docstrings(tree: ast.AST) -> ast.AST:
    containers = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for node in ast.walk(tree):
        if not isinstance(node, containers) or not getattr(node, "body", None):
            continue
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            node.body.pop(0)
            if not node.body:
                node.body.append(ast.Pass())
    return ast.fix_missing_locations(tree)


def compile_source(source: bytes, filename: str = "<protected>") -> bytes:
    tree = _strip_docstrings(ast.parse(source, filename=filename, type_comments=True))
    return marshal.dumps(compile(tree, filename, "exec", dont_inherit=True, optimize=0))


def _loader(payload: str, salt: str, nonce: str, shares: list[tuple[str, str]], pyver: str, source_name: str) -> str:
    # Base85 is merely a printable binary representation. AES-GCM provides encryption and authentication.
    return f'''#!/usr/bin/env python3
"""Protected Python program; requires CPython {pyver} and cryptography."""
import base64 as _b, marshal as _m, sys as _s, zlib as _z
from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _A
from cryptography.hazmat.primitives.kdf.hkdf import HKDF as _K
from cryptography.hazmat.primitives import hashes as _H
_P={payload!r}; _S={salt!r}; _N={nonce!r}; _Q={shares!r}; _V={pyver!r}; _F={source_name!r}
def _d(v): return _b.b85decode(v.encode("ascii"))
def _fail():
 print("[PyVault] Payload authentication failed or file is damaged.",file=_s.stderr); raise SystemExit(4)
def _run():
 v="{{}}.{{}}".format(_s.version_info.major,_s.version_info.minor)
 if v != _V:
  print("[PyVault] Requires CPython {{}}; found {{}}.".format(_V,v),file=_s.stderr); raise SystemExit(3)
 try:
  master=b"".join(bytes(a^b for a,b in zip(_d(x),_d(y))) for x,y in _Q)
  salt=_d(_S); nonce=_d(_N)
  key=_K(algorithm=_H.SHA256(),length=32,salt=salt,info=b"PyVault|payload|v1").derive(master)
  packed=_A(key).decrypt(nonce,_d(_P),b"PYVAULT|payload|v1|"+_V.encode())
  del key,master
  code=_m.loads(_z.decompress(packed))
  if not isinstance(code,type((lambda:None).__code__)): raise ValueError("invalid code object")
 except Exception: _fail()
 ns={{"__name__":"__main__","__file__":globals().get("__file__",_F),"__package__":None,"__cached__":None,"__spec__":None}}
 exec(code,ns,ns)
if __name__=="__main__": _run()
'''


def protect_bytes(source: bytes, filename: str = "script.py", layers: int = 1) -> bytes:
    """Return a self-running protected .py. Exactly one AEAD layer is used intentionally."""
    if not isinstance(source, (bytes, bytearray, memoryview)):
        raise TypeError("source must be bytes")
    source = bytes(source)
    if len(source) > MAX_SOURCE_BYTES:
        raise ValueError(f"Source exceeds {MAX_SOURCE_BYTES} byte limit")
    if not filename.lower().endswith(".py"):
        raise ValueError("Input must be a .py file")
    if int(layers) != 1:
        raise ValueError("Format v1 uses one authenticated AES-256-GCM layer; redundant layers are intentionally unsupported")
    packed = zlib.compress(compile_source(source, filename), level=9)
    master = secrets.token_bytes(32)
    salt, nonce = secrets.token_bytes(16), secrets.token_bytes(12)
    key = HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=b"PyVault|payload|v1").derive(master)
    pyver = f"{sys.version_info.major}.{sys.version_info.minor}"
    ciphertext = AESGCM(key).encrypt(nonce, packed, b"PYVAULT|payload|v1|" + pyver.encode())
    # Split key material into independently randomized shares to avoid a contiguous obvious key literal.
    # This is obfuscation only: all shares ship inside this file and do not provide secrecy against extraction.
    parts = [master[i:i+8] for i in range(0, 32, 8)]
    pads = [secrets.token_bytes(len(p)) for p in parts]
    pairs = list(zip(parts, pads))
    shares = [(base64.b85encode(bytes(a ^ b for a,b in zip(part,pad))).decode(),
               base64.b85encode(pad).decode()) for part,pad in pairs]
    text = _loader(base64.b85encode(ciphertext).decode(), base64.b85encode(salt).decode(),
                   base64.b85encode(nonce).decode(), shares, pyver, Path(filename).name)
    return text.encode("utf-8")


def protect_file(input_path: str | Path, output_path: str | Path | None = None) -> Path:
    src = Path(input_path)
    if src.suffix.lower() != ".py":
        raise ValueError("Input must be a .py file")
    if src.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError(f"Source exceeds {MAX_SOURCE_BYTES} byte limit")
    dest = Path(output_path) if output_path else src.with_name(src.stem + "_protected.py")
    if src.resolve() == dest.resolve():
        raise ValueError("Input and output must be different files")
    if dest.exists():
        raise FileExistsError(dest)
    output = protect_bytes(src.read_bytes(), src.name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("xb") as f:
        f.write(output)
    return dest
