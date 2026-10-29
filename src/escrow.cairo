//! Cell 4: escrow release rules.
//!
//! Model: an escrow holding a deposit, releasable to the recipient only after the deadline
//! has passed AND the depositor has not cancelled. Two gates, both required.
//! Invariant: the escrow never pays out before the deadline and never pays twice.
//!
//! This is a MODEL, not deployed bytecode.

#[derive(Drop, Copy, PartialEq)]
pub struct Escrow {
    pub amount: u256,
    pub deadline: u64,
    pub released: bool,
    pub cancelled: bool,
}

#[generate_trait]
pub impl EscrowImpl of EscrowTrait {
    fn new(amount: u256, deadline: u64) -> Escrow {
        Escrow { amount, deadline, released: false, cancelled: false }
    }

    fn cancel(ref self: Escrow) {
        assert(!self.cancelled, 'already cancelled');
        assert(!self.released, 'already released');
        self.cancelled = true;
    }

    /// Release returns the paid amount (0 means "nothing paid").
    fn release(ref self: Escrow, now: u64) -> u256 {
        if self.released || self.cancelled || now < self.deadline {
            return 0;
        }
        self.released = true;
        self.amount
    }
}

pub fn run_escrow_cell() -> bool {
    let amount = 500_u256;
    let deadline = 1000_u64;

    // 1) до дедлайна — не платит
    let mut e1 = EscrowTrait::new(amount, deadline);
    let early = e1.release(999);

    // 2) после дедлайна — платит ровно один раз
    let mut e2 = EscrowTrait::new(amount, deadline);
    let on_time = e2.release(1000);
    let twice = e2.release(1001);

    // 3) отменённый эскроу не платит никогда
    let mut e3 = EscrowTrait::new(amount, deadline);
    e3.cancel();
    let after_cancel = e3.release(2000);

    early == 0 && on_time == amount && twice == 0 && after_cancel == 0
}
