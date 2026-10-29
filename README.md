# verified_cells_cairo

A **verified cell** is the smallest thing a reviewer can re-run without trusting the author:

1. a **model** of an invariant,
2. a **test** that exercises it,
3. a **manifest** pinning the toolchain,
4. a **receipt** that binds the claim to a canonical hash.

This repository holds **six** cells for Cairo: **accounting conservation**, **authorization on upgrade paths** and **idempotency of cross-contract calls** — the classes named in milestone 1 and milestone 2 of the application.

## Run it (no account, no keys)

```bash
scarb build
scarb execute --print-program-output   # prints six PASS lines
python make_receipt.py                 # writes RECEIPT.json
python verify_receipt.py               # re-checks file hashes and the statement hash
```

Pinned toolchain: **scarb 2.21.0 / cairo 2.21.0**.

## What the cells claim

1. **accounting** — for `deposit(alice,100) → deposit(bob,50) → withdraw(alice,30) → deposit(bob,7) →
   withdraw(bob,17)`, the invariant `alice + bob == total` holds at the end.
2. **authorization** — a non-owner cannot change the implementation; the owner can, through
   `propose` + `accept`, and no other path exists.
3. **idempotency** — delivering the same message id three times applies the credit once, and a
   different id still works (the counter does not stick).
4. **escrow** — no payout before the deadline, `amount` exactly once after it, and nothing at all
   after a cancellation.
5. **upgrade safety** — v2 keeps every slot v1 wrote at the same index; a reordered variant is
   detected by the same check.
6. **cross-call ordering** — the effect is written before the outbound call, so a re-entrant call
   sees the updated state and is rejected; a broken interact-first variant is shown to double-pay.

## What it does **not** claim

- it does not verify deployed bytecode;
- it does not replace an audit;
- it does not prove the sequence is exhaustive.

A green cell is a result, and it is stated as such.

## Why this exists

A Starknet team can show green CI but not *what* holds. This cell makes one property explicit and
re-runnable, and the receipt makes the result falsifiable: change a line of the model and the
`statement_sha256` changes, so a claim cannot drift silently.

## Roadmap (the part the grant pays for)

| milestone | content |
|---|---|
| M1 | Cairo harness + 3 cells (accounting, authorization, idempotency) + receipt format v1 |
| M2 | 3 more cells (escrow, upgrade safety, cross-call ordering) + adoption guide + recorded walkthrough |

License: MIT.

## Adding your own cell

`docs/ADD_A_CELL.md` takes a stranger from nothing to a passing cell in one file: pick the invariant, copy
`src/vault.cairo`, include a broken variant so the cell can fail, wire the `CELL <name>: PASS` line, and issue
the receipt. No contact required, which is the only test of a guide that matters.

## Why these six, and what they map to on Starknet

| cell | the real risk it mirrors |
|---|---|
`accounting_conservation` | vault/CDO accounting drift: shares outstanding no longer match assets held |
`authorization_on_upgrade` | `upgrade` / `set_implementation` callable by a non-owner (often via a forgotten setter or a proxy admin path) |
`idempotency_of_cross_calls` | a message executed twice after a retry/reorg — Starknet's L1↔L2 messaging makes retries normal, not exotic |
`escrow_release_rules` | an escrow that pays before its deadline, or pays twice, or pays after cancellation |
`upgrade_safety` | storage layout reordering between two versions of the same class — silent state reinterpretation |
`cross_call_ordering` | interact-before-effect through a re-entrant callee (a contract that calls back into yours) |

Each cell contains a **deliberately broken variant** where it makes sense (`upgrade_safety`,
`cross_call_ordering`), and the test asserts the check catches it. A cell that cannot fail is decoration.

## What a reviewer can check in one minute

```bash
git clone https://github.com/mak777uh/verified-cells-cairo
cd verified-cells-cairo
scarb execute --print-program-output   # six PASS lines
python verify_receipt.py               # file hashes + statement hash
```

No account, no keys, no network access required beyond the clone.
