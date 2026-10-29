# verified_cells_cairo

A **verified cell** is the smallest thing a reviewer can re-run without trusting the author:

1. a **model** of an invariant,
2. a **test** that exercises it,
3. a **manifest** pinning the toolchain,
4. a **receipt** that binds the claim to a canonical hash.

This repository holds the first cell for Cairo: **accounting conservation**.

## Run it (no account, no keys)

```bash
scarb build
scarb execute --print-program-output   # prints: CELL accounting_conservation: PASS
python make_receipt.py                 # writes RECEIPT.json
python verify_receipt.py               # re-checks file hashes and the statement hash
```

Pinned toolchain: **scarb 2.21.0 / cairo 2.21.0**.

## What the cell claims

> For the sequence `deposit(alice,100) → deposit(bob,50) → withdraw(alice,30) → deposit(bob,7) →
> withdraw(bob,17)`, the invariant `alice + bob == total` holds at the end.

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
