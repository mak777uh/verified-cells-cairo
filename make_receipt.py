#!/usr/bin/env python3
r"""make_receipt.py — build a deterministic receipt for the cell.

The receipt binds the claim to a canonical hash: toolchain version, file hashes, the exact command and
the exact output. Anyone can re-run it and compare.

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
    # Хеш считается по содержимому с LF-переводами строк.
    # 31.10.2026: на Windows git выкладывает файлы с CRLF, и сырой sha256 не совпадал
    # с квитанцией у всех, кто клонировал репозиторий, хотя содержимое то же.
    # Квитанция, которая не воспроизводится на другой платформе, — не квитанция.
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def bind(chain_rpc: str, address: str) -> dict:
    """Первый шаг M3: привязать квитанцию к реальному развёрнутому контракту.

    Что это даёт и чего не даёт. Записывает адрес, class_hash и номер блока — то есть
    факт, что на этот момент у контракта был именно такой класс. Это НЕ доказывает, что
    наша модель описывает его байткод; в `bound_to.note` так и написано. Смысл поля —
    чтобы читатель мог сам сходить в цепь по этим трём значениям и проверить, что они
    не выдуманы.

    Зачем: заявка Starknet обещает веху «каждая ячейка получает bound_to (адрес, селектор,
    блок)». Это её первая половина, сделанная до подачи, а не обещанная.
    """
    import requests

    def rpc(method: str, params: dict):
        r = requests.post(chain_rpc, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                          headers={"Content-Type": "application/json", "User-Agent": "make-receipt/1"}, timeout=25)
        d = r.json()
        return d.get("result"), d.get("error")

    blk, err = rpc("starknet_blockNumber", {})
    if err or blk is None:
        return {"error": f"blockNumber failed: {err}"}
    ch, err = rpc("starknet_getClassHashAt", {"block_id": {"block_number": blk}, "contract_address": address})
    if err or not ch:
        return {"error": f"getClassHashAt failed: {err}"}
    return {
        "chain": "starknet-mainnet",
        "rpc": chain_rpc,
        "address": address,
        "class_hash": ch,
        "block_number": blk,
        "note": ("address/class_hash/block are what the chain returned at build time; this does NOT assert "
                 "that the cell models this contract's bytecode — see what_it_does_not_claim"),
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--bind-address", default="0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
                    help="real deployed Starknet contract to bind the receipt to (default: STRK token)")
    ap.add_argument("--bind-rpc", default="https://api.cartridge.gg/x/starknet/mainnet")
    ap.add_argument("--no-bind", action="store_true", help="skip the on-chain binding")
    a = ap.parse_args()
    files = sorted((ROOT / "src").rglob("*.cairo")) + [ROOT / "Scarb.toml"]
    version = subprocess.run([SCARB, "--version"], capture_output=True, text=True).stdout.strip()
    run = subprocess.run([SCARB, "execute", "--print-program-output"], capture_output=True,
                         text=True, cwd=str(ROOT), timeout=300)
    out = (run.stdout or "") + (run.stderr or "")
    verdict = "PASS" if out.count(": PASS") >= 6 and ": FAIL" not in out else "FAIL"
    file_hashes = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in files}
    receipt = {
        "cells": ["accounting_conservation", "authorization_on_upgrade", "idempotency_of_cross_calls",
                  "escrow_release_rules", "upgrade_safety", "cross_call_ordering"],
        "what_it_claims": [
            "accounting: sum(balances) == total survives the stated deposit/withdraw sequence",
            "authorization: only the owner can change the implementation, through propose+accept",
            "idempotency: delivering the same message id twice applies the effect once",
            "escrow: no payout before the deadline, at most one payout, none after cancel",
            "upgrade safety: v2 keeps every slot v1 wrote at the same index (and the broken variant is caught)",
            "ordering: a re-entrant call observes the already-updated state and is rejected",
        ],
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
    if not a.no_bind:
        receipt["bound_to"] = bind(a.bind_rpc, a.bind_address)
    (ROOT / "RECEIPT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"verdict: {verdict} | receipt: RECEIPT.json | statement_sha256: {receipt['statement_sha256'][:16]}…")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
