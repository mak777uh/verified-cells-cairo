# Adding a cell

A cell is three things: **a model**, **a test that can fail**, and **a receipt**. This guide takes you from
nothing to a passing cell in one file, without contacting anyone.

If you get stuck, the failure will be a compile error or a `FAIL` line — not a missing document. That is the
point of this file.

---

## 1. What a cell is allowed to claim

A cell claims exactly one sentence of the form:

> For **this sequence of operations**, **this invariant** holds at the end.

Not "the contract is safe". Not "there are no bugs". A cell that cannot be written as that sentence is not a
cell — it is an audit, and it belongs somewhere else.

## 2. Pick the invariant before you pick the code

Write the sentence down first, in the past tense of a test:

```
For the sequence deposit(100) -> withdraw(30), the invariant total == sum(balances) holds.
```

Two properties make an invariant usable:

| property | why |
|---|---|
| it can be **false** | if no reachable state violates it, the test proves nothing |
| it is **arithmetic or structural** | "only the owner can call it" is structural; "it is secure" is not |

## 3. Create the file

```bash
cp src/vault.cairo src/<your_cell>.cairo
```

The template to copy is `src/vault.cairo`: a state struct, a trait with the operations, and a function
`run_<name>_cell() -> bool` that returns the verdict.

Three rules for the file:

1. **No external calls.** A cell models; it does not deploy. If your invariant needs another contract, model
   the other contract as a struct too.
2. **Deterministic.** Same inputs, same output, every run. No timestamps, no randomness, no environment.
3. **Include a broken variant.** If your cell can only show the good case, add a second function that models
   the *bug* and assert that your check catches it. A cell that cannot fail is decoration — see
   `src/upgrade_safety.cairo` (`layout_v2_broken`) and `src/ordering.cairo` (`withdraw_broken`) for two
   worked examples.

## 4. Wire it into the executable

`src/lib.cairo` runs every cell and prints one line per cell:

```cairo
if run_<your_cell>() {
    println!("CELL <your_cell_name>: PASS");
} else {
    println!("CELL <your_cell_name>: FAIL");
    failures = failures + 1;
};
```

Keep the line format exactly `CELL <name>: PASS` — `make_receipt.py` counts `": PASS"` occurrences and
refuses to issue a `PASS` receipt if any line says `FAIL`.

## 5. Run it

```bash
scarb build
scarb execute --print-program-output
```

You should see your line among the others. If your cell fails on the first run, that is normal and useful: it
means the model and the invariant disagree, which is exactly what the cell exists to detect.

## 6. Issue the receipt

```bash
python make_receipt.py     # writes RECEIPT.json, prints the verdict and the statement hash
python verify_receipt.py   # re-checks file hashes and the statement hash
```

The receipt pins the toolchain, hashes every source file, records the exact command and the exact output, and
binds them to one `statement_sha256`. If you change a line of your model, the hash changes — a claim cannot
drift silently.

## 7. What to write in your pull request

Three lines are enough:

```
cell: <name>
claims: <the one sentence>
can fail because: <the broken variant, and what it does wrong>
```

---

## Where cells usually go wrong

| symptom | cause | fix |
|---|---|---|
| the cell always passes | the invariant is a tautology, or the sequence never reaches the interesting state | add the operation that breaks it, then assert the break is caught |
| the cell cannot be re-run by a stranger | it depends on a local path, a key or a network | model the dependency instead of calling it |
| the receipt hash changes every run | a value is read from a live source (price, block, clock) | pin it: pass the value in as an argument |
| the cell proves the code, not the property | the test mirrors the implementation line by line | state the invariant in words first, then write the test that could contradict it |

## The boundary, stated once

A cell verifies a model and a test on a pinned toolchain. It does **not** verify deployed bytecode, and it does
not replace an audit. Every receipt carries this in `what_it_does_not_claim`, so a reader cannot mistake a green
cell for a green contract.
