//! Cell 1: accounting conservation.
//!
//! Model: a vault where the owner tracks a global total and per-user balances.
//! Invariant: sum(balances) == total, at every step.
//!
//! This is a MODEL, not deployed bytecode. A cell proves that the stated invariant
//! survives the stated sequence under the pinned compiler — nothing more.

#[derive(Drop, Copy, PartialEq)]
pub struct Ledger {
    pub total: u256,
    pub alice: u256,
    pub bob: u256,
}

#[generate_trait]
pub impl LedgerImpl of LedgerTrait {
    fn empty() -> Ledger {
        Ledger { total: 0, alice: 0, bob: 0 }
    }

    /// Deposit into `who` is modelled as credit + total increase by the same amount.
    fn deposit(ref self: Ledger, who: felt252, amount: u256) {
        self.total = self.total + amount;
        if who == 'alice' {
            self.alice = self.alice + amount;
        } else {
            self.bob = self.bob + amount;
        };
    }

    /// Withdraw is modelled as debit + total decrease; it must never underflow.
    fn withdraw(ref self: Ledger, who: felt252, amount: u256) {
        if who == 'alice' {
            assert(self.alice >= amount, 'alice underflow');
            self.alice = self.alice - amount;
        } else {
            assert(self.bob >= amount, 'bob underflow');
            self.bob = self.bob - amount;
        };
        self.total = self.total - amount;
    }

    /// The invariant this cell exists for.
    fn invariant_holds(ref self: Ledger) -> bool {
        self.alice + self.bob == self.total
    }
}

/// Exercises a fixed sequence and returns the invariant verdict.
/// Deterministic on purpose: the same sequence must give the same receipt hash.
pub fn run_accounting_cell() -> bool {
    let mut ledger = LedgerTrait::empty();
    ledger.deposit('alice', 100);
    ledger.deposit('bob', 50);
    ledger.withdraw('alice', 30);
    ledger.deposit('bob', 7);
    ledger.withdraw('bob', 17);
    ledger.invariant_holds()
}
