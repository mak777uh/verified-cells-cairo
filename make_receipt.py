#!/usr/bin/env python3
r"""make_receipt.py — собрать детерминированную квитанцию для ячейки.

Квитанция связывает утверждение с каноническим хешем: версия инструментов, хеши файлов,
точная команда и точный вывод. Любой может перезапустить и сравнить.

    python make_receipt.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).parent
SCARB = r"C:\111\env\bin\scarb\scarb-v2.21.0-x86_64-pc-windows-msvc\bin\scarb.exe"


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    files = sorted((ROOT / "src").rglob("*.cairo")) + [ROOT / "Scarb.toml"]
    version = subprocess.run([SCARB, "--version"], capture_output=True, text=True).stdout.strip()
    run = subprocess.run([SCARB, "execute", "--print-program-output"], capture_output=True,
                         text=True, cwd=str(ROOT), timeout=300)
    out = (run.stdout or "") + (run.stderr or "")
    verdict = "PASS" if "CELL accounting_conservation: PASS" in out else "FAIL"
    file_hashes = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in files}
    receipt = {
        "cell": "accounting_conservation",
        "what_it_claims": "sum(balances) == total survives the stated deposit/withdraw sequence",
        "what_it_does_not_claim": [
            "does not verify deployed bytecode",
            "does not replace an audit",
            "does not prove the sequence is exhaustive",
        ],
        "toolchain": [v for v in version.splitlines() if v.strip()],
        "command": "scarb execute --print-program-output",
        "verdict": verdict,
        "stdout_tail": out.strip().splitlines()[-3:],
        "files": file_hashes,
        "statement_sha256": hashlib.sha256(
            json.dumps(file_hashes, sort_keys=True).encode()
        ).hexdigest(),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scarb_exit": run.returncode,
    }
    (ROOT / "RECEIPT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"вердикт: {verdict} | квитанция: RECEIPT.json | statement_sha256: {receipt['statement_sha256'][:16]}…")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
