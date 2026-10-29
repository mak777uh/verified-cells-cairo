//! Cell 6: cross-contract call ordering.
//!
//! Model: a function that changes state and then calls out. The state must be written BEFORE the
//! external call, otherwise a re-entrant callee sees the old state and can double-spend.
//! Invariant: a re-entrant call observes the already-updated state and is rejected.
//!
//! This is a MODEL, not deployed bytecode.

#[derive(Drop, Copy, PartialEq)]
pub struct Vault {
    pub balance: u256,
    pub in_flight: bool,
}

#[generate_trait]
pub impl VaultImpl of VaultTrait {
    fn new(balance: u256) -> Vault {
        Vault { balance, in_flight: false }
    }

    /// "checks-effects-interactions": effect first, then the outbound call.
    fn withdraw_cei(ref self: Vault, amount: u256) -> u256 {
        assert(!self.in_flight, 'reentrant call');
        assert(self.balance >= amount, 'insufficient');
        self.balance = self.balance - amount; // ЭФФЕКТ до вызова
        self.in_flight = true;
        // здесь был бы внешний вызов; повторный вход увидит in_flight == true
        let out = amount;
        self.in_flight = false;
        out
    }

    /// Broken version: interacts before the effect — the classic double-spend.
    fn withdraw_broken(ref self: Vault, amount: u256) -> (u256, u256) {
        let first = amount;                      // «вызов», затем эффект
        let reentrant = if self.balance >= amount { amount } else { 0 };
        self.balance = self.balance - first;
        (first, reentrant)
    }
}

pub fn run_ordering_cell() -> bool {
    let mut good = VaultTrait::new(100_u256);
    let paid = good.withdraw_cei(100);
    // после корректного вывода баланс 0 и повторный вход невозможен
    let safe = paid == 100 && good.balance == 0;

    let mut bad = VaultTrait::new(100_u256);
    let (first, reentrant) = bad.withdraw_broken(100);
    // в сломанной версии повторный вход «видит» старый баланс и тоже платит
    let bug_detected = first == 100 && reentrant == 100;

    safe && bug_detected
}
