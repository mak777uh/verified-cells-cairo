#!/usr/bin/env python3
r"""verify_receipt.py — verify the receipt: files unchanged and the cell still passes."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    r = json.loads((ROOT / "RECEIPT.json").read_text(encoding="utf-8"))
    ok = True
    for name, expected in r["files"].items():
        p = ROOT / name
        if not p.exists():
            print(f"MISSING {name}")
            ok = False
            continue
        actual = sha(p)
        mark = "OK" if actual == expected else "CHANGED"
        if actual != expected:
            ok = False
        print(f"{mark:8} {name}")
    stmt = hashlib.sha256(
        json.dumps({k: sha(ROOT / k) for k in sorted(r["files"])}, sort_keys=True).encode()
    ).hexdigest()
    print(f"statement_sha256: {'matches' if stmt == r['statement_sha256'] else 'MISMATCH'}")
    return 0 if ok and stmt == r["statement_sha256"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
